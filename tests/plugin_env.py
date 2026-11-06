"""Shared by test_install.py and test_algorithms.py: start the plugin the way QGIS does (headless).

KARIOS_PLUGIN_PARENT: folder holding the karios_qgis plugin folder to test (CI points it at the unzipped
release zip, KARIOS_PACK_BASE_URL at the served dependency packs; a user can point it at the plugins folder
of their QGIS profile). Unset: the source tree is loaded as the karios_qgis package.
"""
import importlib.util
import os
import sys
import time
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = os.environ.get("KARIOS_PLUGIN_PARENT")
_app = None


def start_plugin(timeout=180):
    """Start QGIS and the plugin (initGui, background dependency check); return the plugin once its provider is registered."""
    from qgis.core import QgsApplication
    from qgis.PyQt.QtCore import QCoreApplication

    global _app
    _app = QgsApplication([], True)  # kept alive: QGIS is torn down when the object is collected
    _app.initQgis()
    # the "processing" plugin is not on sys.path outside a running QGIS
    sys.path.append(os.path.join(QgsApplication.pkgDataPath(), "python", "plugins"))
    from processing.core.Processing import Processing
    Processing.initialize()

    if PARENT:
        sys.path.insert(0, PARENT)
        import karios_qgis as pkg
    else:
        spec = importlib.util.spec_from_file_location("karios_qgis", os.path.join(ROOT, "__init__.py"),
                                                      submodule_search_locations=[ROOT])
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["karios_qgis"] = pkg
        spec.loader.exec_module(pkg)

    plugin = pkg.classFactory(MagicMock())
    plugin.initGui()
    end = time.time() + timeout
    while time.time() < end and not plugin.provider:
        QCoreApplication.processEvents()
        time.sleep(0.1)
    assert plugin.provider, "plugin did not register its provider"
    return plugin, os.path.dirname(os.path.abspath(pkg.__file__))


def check_dependencies(plugin_dir):
    """OpenCV, pandas, scikit-image import; with a zip (KARIOS_PLUGIN_PARENT) they must come from its dependency bundle."""
    import cv2
    import pandas
    import skimage
    if PARENT:
        deps = os.path.abspath(os.path.join(plugin_dir, "dependencies"))  # one cpXY folder per Python
        for m in (cv2, skimage):  # conda's pandas may stay in the test environment: not checked
            assert os.path.abspath(m.__file__).startswith(deps), f"{m.__name__} not from the zip: {m.__file__}"
    return cv2.__version__, pandas.__version__, skimage.__version__
