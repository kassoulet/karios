# KARIOS QGIS Plugin - Quick Start

## Installation

### Quick Install
```bash
# Clone with submodules
git clone --recursive https://github.com/your-org/karios-qgis.git
cd karios-qgis

# Install to QGIS
python install_plugin.py

# Or manually compile resources
pyrcc6 -o resources/resources.py resources/resources.qrc
```

## Usage

### Check Dependencies
The plugin automatically checks for dependencies on startup. If missing, a dialog will appear with an "Install" button.

### Run Processing
1. Open QGIS Processing Toolbox (`Processing > Toolbox`)
2. Navigate to `KARIOS > KARIOS Processing`
3. Configure inputs and run

## Troubleshooting

### Plugin Crashes on Load

**Step 1: Check Logs**
- Open QGIS Log Messages Panel (`F12`)
- Look for "KARIOS" tab
- Check for ERROR or CRITICAL messages

**Step 2: Common Fixes**

**Missing OpenCV:**
```bash
pip install opencv-python
```

**Missing KARIOS submodule:**
```bash
git submodule update --init --recursive
cd karios
pip install -e .
```

**Linux - Missing libGL:**
```bash
sudo apt-get install libgl1-mesa-glx
```

### View Detailed Logs

In QGIS Python Console (`Ctrl+Alt+P`):
```python
import logging
logging.getLogger("KARIOS").setLevel(logging.DEBUG)
logging.getLogger("KARIOS.deps").setLevel(logging.DEBUG)
```

Then reload the plugin.

### Run Tests

```bash
# Test in QGIS Docker container
python tests/run_docker_tests.py --build

# Test with dependency installation
python tests/run_docker_tests.py --install-deps --verbose
```

## Dependencies

**Required:**
- QGIS 3.28+
- Python 3.8+
- OpenCV (opencv-python)
- NumPy

**Optional:**
- KARIOS library (for processing algorithms)

## Files Overview

```
karios-qgis/
├── karios_qgis.py              # Main plugin file
├── dependency_checker.py       # Dependency checker with logs
├── install_plugin.py           # Installation script
├── processing/
│   └── provider.py             # Processing provider
├── tests/
│   ├── run_docker_tests.py     # Test runner
│   └── docker/
│       ├── Dockerfile          # Test container
│       └── test_plugin.py      # Test script
├── LOGGING.md                  # Logging guide
├── DEBUG_SUMMARY.md            # Debug implementation
└── README.md                   # Full documentation
```

## Getting Help

1. Check `LOGGING.md` for detailed log information
2. Check `DEBUG_SUMMARY.md` for troubleshooting guide
3. Check `tests/README.md` for Docker testing
4. Open an issue on GitHub with log output

## Quick Commands

```bash
# View logs in real-time (Linux)
tail -f /tmp/karios_debug.log

# Reinstall plugin
python install_plugin.py

# Check Python version
python --version

# Check QGIS version
# In QGIS Python Console:
import qgis
print(qgis.__version__)
```
