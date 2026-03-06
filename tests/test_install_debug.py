"""
Debug script for testing dependency installation in QGIS.
Run this in QGIS Python Console to test the install functionality.

Usage:
    1. Open QGIS Python Console (Ctrl+Alt+P)
    2. Click "Show Editor" 
    3. Open this file
    4. Click "Run Script"
    
Or directly in console:
    exec(open('/path/to/test_install_debug.py').read())
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(name)s: %(message)s'
)

print("=" * 60)
print("KARIOS Dependency Installation Debug Test")
print("=" * 60)

# Add plugin path
plugin_path = '/home/gautier/projects/isl/karios-qgis'
if plugin_path not in sys.path:
    sys.path.insert(0, plugin_path)
    print(f"Added to path: {plugin_path}")

try:
    from dependency_checker import DependencyChecker, DependencyInfo, logger
    print("✓ Successfully imported dependency_checker")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Enable debug logging
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

print("\n" + "=" * 60)
print("Test 1: Check current dependencies")
print("=" * 60)

deps = [
    DependencyInfo("OpenCV", "cv2", "opencv-python", min_version="4.0.0"),
    DependencyInfo("NumPy", "numpy", min_version="1.20.0"),
]

checker = DependencyChecker(deps)
results = checker.check_all()

print("\nDependency Status:")
for name, status in results.items():
    symbol = "✓" if status.installed else "✗"
    version = f" (v{status.version})" if status.version else ""
    print(f"  {symbol} {name}{version}")

print("\n" + "=" * 60)
print("Test 2: Check missing dependencies")
print("=" * 60)

missing = checker.get_missing()
print(f"Missing: {len(missing)} package(s)")
for status in missing:
    print(f"  - {status.info.name} ({status.info.package})")

if not missing:
    print("  All dependencies are installed!")

print("\n" + "=" * 60)
print("Test 3: Test installation (if missing)")
print("=" * 60)

if missing:
    print("Attempting to install missing packages...\n")
    
    for i, status in enumerate(missing, 1):
        pkg_name = status.info.name
        pkg_package = status.info.package
        
        print(f"[{i}/{len(missing)}] Installing {pkg_name}...")
        print(f"  Package: {pkg_package}")
        
        def callback(msg):
            print(f"  → {msg}")
        
        success, msg = checker.install_single(status.info, callback=callback)
        
        if success:
            print(f"  ✓ SUCCESS")
        else:
            print(f"  ✗ FAILED: {msg}")
            print(f"  → Try manually: pip install {pkg_package}")
    
    # Re-check
    print("\nRe-checking dependencies...")
    checker.check_all()
    missing_after = checker.get_missing()
    
    if not missing_after:
        print("✓ All packages installed successfully!")
    else:
        print(f"✗ Still missing {len(missing_after)} package(s)")
        
else:
    print("No installation needed - all packages are installed")

print("\n" + "=" * 60)
print("Test 4: Test dialog display")
print("=" * 60)

try:
    from qgis.utils import iface
    from dependency_checker import show_dependency_dialog
    
    print("Getting QGIS interface...")
    print(f"  iface: {iface}")
    
    if iface:
        print("Showing dialog...")
        
        def on_complete(success):
            print(f"\n*** Installation complete callback: success={success} ***")
        
        result = show_dependency_dialog(
            checker,
            iface,
            title="Test - Missing Dependencies",
            message="This is a test dialog. Click Install to test.",
            on_install_complete=on_complete
        )
        
        print(f"Dialog shown (non-blocking), result={result}")
        print("Check if dialog appears on screen!")
    else:
        print("QGIS iface not available")
        
except Exception as e:
    print(f"Dialog test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Debug Test Complete")
print("=" * 60)
