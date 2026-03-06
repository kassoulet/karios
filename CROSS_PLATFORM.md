# Cross-Platform Compatibility

## Installation Method: `--target`

Using `pip install --target <plugin-folder>/site-packages` works universally.

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| **Linux** | ✓ Tested | Works on all distributions |
| **Windows** | ✓ Compatible | No special requirements |
| **macOS** | ✓ Compatible | Works on Intel & Apple Silicon |

## Why It Works Everywhere

### 1. No System Python Modifications
```bash
# Installing to plugin folder, not system Python
pip install --target /path/to/plugin/site-packages package
```
✓ No PEP 668 issues (Linux)  
✓ No permission errors (all platforms)  
✓ No virtualenv needed  

### 2. Standard Python Features
- `os.path.join()` - Cross-platform path handling
- `sys.path.insert()` - Works on all Python installations
- `subprocess.run()` - Standard library
- `importlib` - Standard library

### 3. Platform-Specific Wheels
PyPI provides pre-compiled wheels for:
- **Linux**: `manylinux` wheels (works on most distributions)
- **Windows**: `.whl` files for Win64
- **macOS**: `.whl` for Intel & Apple Silicon

## Platform Notes

### Linux

**Tested on:**
- Ubuntu 24.04 ✓
- Debian 12+ ✓
- Fedora ✓

**No issues with:**
- PEP 668 (externally-managed environments)
- Permission errors
- Distribution-specific Python

### Windows

**Compatible with:**
- Windows 10/11
- QGIS Standalone installer
- OSGeo4W

**Notes:**
- Paths use backslashes (`\`) - handled by `os.path`
- No PEP 668 on Windows
- pip usually at `C:\Python\python.exe -m pip`

### macOS

**Compatible with:**
- macOS 11+ (Big Sur and later)
- Intel Macs
- Apple Silicon (M1/M2/M3)

**Notes:**
- QGIS from qgis.org or Homebrew
- No PEP 668 on macOS
- Universal wheels for OpenCV, NumPy, etc.

## Dependencies

All required packages have cross-platform wheels:

| Package | Linux | Windows | macOS | Apple Silicon |
|---------|-------|---------|-------|---------------|
| opencv-python-headless | ✓ | ✓ | ✓ | ✓ |
| numpy | ✓ | ✓ | ✓ | ✓ |
| scikit-image | ✓ | ✓ | ✓ | ✓ |
| pandas | ✓ | ✓ | ✓ | ✓ |

## Potential Issues & Solutions

### Issue 1: pip Not Found

**Symptom:**
```
[INSTALL] Error: No module named pip
```

**Solution by Platform:**

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install python3-pip

# Fedora
sudo dnf install python3-pip
```

**Windows:**
- Usually included with Python
- Reinstall Python with "pip" option checked

**macOS:**
```bash
# If using system Python
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

### Issue 2: Network/Firewall

**Symptom:**
```
Could not fetch URL https://pypi.org/simple/
```

**Solution:**
- Check internet connection
- Configure proxy if behind corporate firewall
- Use alternative PyPI mirror:
  ```bash
  pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple/ ...
  ```

### Issue 3: Slow Download

**Symptom:** Installation takes >10 minutes

**Solution:**
- Use local PyPI cache
- Pre-download packages on one machine, copy `site-packages`
- Increase timeout in code (currently 300s per package)

### Issue 4: Disk Space

**Symptom:**
```
No space left on device
```

**Required Space:**
- OpenCV: ~50 MB
- scikit-image: ~30 MB
- pandas: ~40 MB
- numpy: ~20 MB
- **Total: ~140 MB**

**Solution:** Free up disk space or install to different location.

## Testing on Different Platforms

### Quick Test

Run in QGIS Python Console:

```python
import sys
import os

# Check Python
print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")
print(f"Platform: {sys.platform}")

# Check if target installation works
plugin_dir = os.path.dirname(qgis.utils.plugins['karios_qgis'].__file__)
target = os.path.join(plugin_dir, 'site-packages')
print(f"Target: {target}")

# Try import
try:
    import cv2
    print(f"✓ OpenCV: {cv2.__version__}")
except ImportError as e:
    print(f"✗ OpenCV: {e}")
```

### Platform Detection

```python
import sys

if sys.platform == 'linux':
    print("Linux")
elif sys.platform == 'win32':
    print("Windows")
elif sys.platform == 'darwin':
    print("macOS")
```

## Logs by Platform

### Linux
```
[INSTALL] Python executable: /usr/bin/python3
[INSTALL] Command: /usr/bin/python3 -m pip install --target .../site-packages opencv-python-headless
```

### Windows
```
[INSTALL] Python executable: C:\OSGeo4W\bin\python3.exe
[INSTALL] Command: C:\OSGeo4W\bin\python3.exe -m pip install --target .../site-packages opencv-python-headless
```

### macOS
```
[INSTALL] Python executable: /Library/Frameworks/Python.framework/Versions/3.11/bin/python3
[INSTALL] Command: .../python3 -m pip install --target .../site-packages opencv-python-headless
```

## Uninstall Options

### Option 1: Delete site-packages Folder

**All Platforms:**
```bash
# In plugin folder
rm -rf site-packages/          # Linux/macOS
rmdir /s /q site-packages      # Windows
```

### Option 2: Reinstall Plugin

**All Platforms:**
1. Delete plugin folder
2. Reinstall from ZIP
3. Fresh start

## Best Practices

### For Users

1. **Ensure internet connection** before enabling plugin
2. **Wait for installation** - takes 2-5 minutes depending on speed
3. **Check logs** (F12) if something goes wrong
4. **Don't interrupt** installation process

### For Developers

1. **Test on all platforms** before release
2. **Include platform-specific notes** in documentation
3. **Provide manual install instructions** as fallback
4. **Log everything** for debugging

## Fallback: Manual Installation

If auto-install fails, users can manually install:

### Linux/macOS
```bash
cd /path/to/karios-qgis
python3 -m pip install --target site-packages \
    opencv-python-headless \
    numpy \
    scikit-image \
    pandas
```

### Windows
```cmd
cd C:\path\to\karios-qgis
python -m pip install --target site-packages ^
    opencv-python-headless ^
    numpy ^
    scikit-image ^
    pandas
```

## Summary

✓ **Linux** - Fully tested and working  
✓ **Windows** - Compatible (standard Python behavior)  
✓ **macOS** - Compatible (standard Python behavior)  
✓ **No root/admin** required on any platform  
✓ **No PEP 668 issues** on any platform  
✓ **Self-contained** - Plugin has its own dependencies  
✓ **Portable** - Can copy plugin folder to another machine  

The `--target` approach is the most compatible method for QGIS plugin dependency installation.
