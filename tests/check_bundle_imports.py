"""Check the dependency packs import under the running Python (no QGIS needed; numpy, scipy installed).

Run: python tests/check_bundle_imports.py packs/deps-*.zip
Packs for other Pythons are skipped; at least one pack must match the running Python.
"""
import subprocess
import sys
import tempfile
import zipfile

TAG = "cp%d%d" % sys.version_info[:2]
CODE = ("import sys; sys.path.insert(0, sys.argv[1]); import cv2, pandas, skimage; "
        "from skimage.transform import warp; import numpy as np; cv2.resize(np.zeros((8, 8), np.uint8), (4, 4)); "
        "print(cv2.__version__, pandas.__version__, skimage.__version__, cv2.__file__)")


def main(packs):
    tested = 0
    for path in packs:
        if not path.endswith(f"-{TAG}.zip"):
            continue
        d = tempfile.mkdtemp()
        zipfile.ZipFile(path).extractall(d)
        r = subprocess.run([sys.executable, "-c", CODE, d], capture_output=True, text=True)
        assert r.returncode == 0, f"{path}: {r.stderr[-800:]}"
        print(f"OK {path}: {r.stdout.strip()}")
        tested += 1
    assert tested, f"no pack for {TAG}"


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except AssertionError as e:
        sys.exit(str(e))
