"""Run the KARIOS processing on the sample images of the karios submodule: checks the installed plugin works end to end.

Run headless: QT_QPA_PLATFORM=offscreen python tests/test_algorithms.py
(see plugin_env.py for KARIOS_PLUGIN_PARENT / KARIOS_PACK_BASE_URL)
Images: karios/tests/end_to_end/test_data, or the folder given as argument (monitored and reference images).
"""
import math
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_env import ROOT, start_plugin  # noqa: E402

DATA = os.path.join(ROOT, "karios", "tests", "end_to_end", "test_data")
MONITORED = "L2F_T12SYH_20220824T175017_LS9_R035_B04_10m.tif"
REFERENCE = "T12SYH_20220514T175909_B04.tif"
# Reference values come from a known good run (default configuration); REL_TOL absorbs OpenCV/BLAS
# differences across platforms. If a dependency upgrade legitimately moves them, check, then update here.
REL_TOL = 0.1
EXPECTED = {"CE90": 2.632, "RMSE": 0.229, "Number of Key Points": 2370}
OUTPUTS = ("01_overview.png", "02_dx.png", "03_dy.png", "04_ce.png", "kp_delta.json")


def main():
    from qgis.core import Qgis, QgsProcessingContext, QgsProcessingFeedback, QgsProject, QgsRasterLayer

    class Feedback(QgsProcessingFeedback):
        def __init__(self):
            super().__init__()
            self.lines = []

        def pushInfo(self, info):
            self.lines.append(info)

        def reportError(self, error, fatalError=False):
            self.lines.append(f"ERROR: {error}")

    data = sys.argv[1] if len(sys.argv) > 1 else DATA
    plugin, _ = start_plugin()
    alg = plugin.provider.algorithm("karios_processing").create()
    assert alg.flags() & Qgis.ProcessingAlgorithmFlag.NoThreading, "must run on the main thread"

    layers = [QgsRasterLayer(os.path.join(data, f), "r") for f in (MONITORED, REFERENCE)]
    assert all(layer.isValid() for layer in layers), f"cannot open the sample images in {data}"
    out = tempfile.mkdtemp()
    params = dict(INPUT_MONITORED=layers[0], INPUT_REFERENCE=layers[1], OUTPUT_FOLDER=out, PIXEL_SIZE=0,
                  GENERATE_KP_MASK=False, GENERATE_DELTA_RASTER=False, GENERATE_KP_CHIPS=False, ENABLE_LARGE_SHIFT=False)
    context, feedback = QgsProcessingContext(), Feedback()
    context.setProject(QgsProject.instance())
    alg.prepare(params, context, feedback)
    results, ok = alg.run(params, context, feedback)
    assert ok, "algorithm failed:\n" + "\n".join(feedback.lines)

    text = "\n".join(feedback.lines)
    for key, expected in EXPECTED.items():
        m = re.search(rf"{key}: ([\d.]+)", text)
        assert m, f"{key} not reported:\n{text}"
        val = float(m.group(1))
        assert math.isfinite(val) and math.isclose(val, expected, rel_tol=REL_TOL), f"{key}={val}, expected {expected}"
        print(f"OK: {key}={val}")
    # the CSV and GeoJSON outputs point at the written files
    for key in ("OUTPUT_CSV", "OUTPUT_GEOJSON"):
        assert results.get(key) and os.path.isfile(results[key]), f"{key} is not a written file: {results.get(key)!r}"
    assert os.path.basename(results["OUTPUT_GEOJSON"]) == "kp_delta.json" and os.path.dirname(results["OUTPUT_CSV"]) == out
    files = os.listdir(out)
    for f in OUTPUTS:
        assert f in files, f"{f} not written to {out}: {files}"
    assert any(f.startswith("KLT_matcher_") and f.endswith(".csv") for f in files), f"no key points CSV in {out}: {files}"
    print(f"OK: KARIOS processing, {len(files)} files written")


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    os._exit(0)
