# Tests

Install and run tests, run headless with QGIS's Python (`QT_QPA_PLATFORM=offscreen` is set by the scripts).

| Script | Checks |
|---|---|
| `test_install.py` | the plugin starts like in QGIS (`initGui`), gets its dependencies (OpenCV, pandas, scikit-image), registers the `karios` provider with the `karios_processing` algorithm |
| `test_algorithms.py [DATA_DIR]` | **runs the KARIOS processing** on the sample images of the `karios` submodule (`karios/tests/end_to_end/test_data`) and compares CE90, RMSE and the number of key points with reference values (10 %), then checks the output files |
| `check_zip.py ZIP...` | layout and `metadata.txt` of a plugin zip |
| `check_bundle_imports.py PACK...` | dependency packs import under the running Python (no QGIS) |

`plugin_env.py` is the shared start-up code. Both QGIS tests read:

- `KARIOS_PLUGIN_PARENT`: folder that contains the `karios_qgis` plugin folder to test. Unset: the source tree.
- `KARIOS_PACK_BASE_URL`: where the plugin downloads its dependency pack (CI serves the packs on `http://127.0.0.1:18431`; plain http is accepted on loopback only).

## Source tree

In a QGIS Python environment that already has OpenCV, pandas and scikit-image (`git submodule update --init` first):

```bash
python tests/test_install.py
python tests/test_algorithms.py
```

## Release zip, as CI does

```bash
python tools/build_zip.py packs packs linux-x64 3.12 manylinux2014_x86_64 manylinux_2_28_x86_64
python tools/build_zip.py plugin out/karios_qgis.zip packs
python tests/check_zip.py out/karios_qgis.zip
mkdir unzipped && python -c "import zipfile; zipfile.ZipFile('out/karios_qgis.zip').extractall('unzipped')"
python -m http.server 18431 --bind 127.0.0.1 --directory packs &
KARIOS_PLUGIN_PARENT=$PWD/unzipped KARIOS_PACK_BASE_URL=http://127.0.0.1:18431 python tests/test_install.py
KARIOS_PLUGIN_PARENT=$PWD/unzipped KARIOS_PACK_BASE_URL=http://127.0.0.1:18431 python tests/test_algorithms.py
```

With `KARIOS_PLUGIN_PARENT` set, the tests fail unless OpenCV and scikit-image are imported from the zip's `dependencies/` folder:
use an environment without them.

## Is the plugin I installed working?

Run the processing test against the plugin in your QGIS profile (**Settings → User Profiles → Open Active Profile Folder**,
then `python/plugins`), with the Python of QGIS (OSGeo4W Shell on Windows):

```bash
KARIOS_PLUGIN_PARENT=<profile>/python/plugins python tests/test_algorithms.py <folder with the two sample .tif>
```

Without the sample images, use any two rasters in QGIS: Processing Toolbox → KARIOS → KARIOS Processing.
