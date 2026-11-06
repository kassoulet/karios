"""Install smoke test: start the plugin like QGIS does, check its dependencies and that the provider registers.

Run headless: QT_QPA_PLATFORM=offscreen python tests/test_install.py
(see plugin_env.py for KARIOS_PLUGIN_PARENT / KARIOS_PACK_BASE_URL)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_env import check_dependencies, start_plugin  # noqa: E402


def main():
    plugin, plugin_dir = start_plugin()
    versions = check_dependencies(plugin_dir)
    from qgis.core import QgsApplication
    provider = QgsApplication.processingRegistry().providerById("karios")
    assert provider is plugin.provider, "provider not registered"
    names = [a.name() for a in provider.algorithms()]
    assert names == ["karios_processing"], f"unexpected algorithms: {names}"
    print(f"OK: plugin started from {plugin_dir}; cv2 {versions[0]}, pandas {versions[1]}, skimage {versions[2]}")
    plugin.unload()


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    os._exit(0)  # no exitQgis: tearing down after matplotlib/GDAL use can segfault
