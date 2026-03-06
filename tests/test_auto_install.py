"""
Test auto-install functionality.
Run this in QGIS Python Console to test dependency installation without dialog.

Usage:
    exec(open('/path/to/karios-qgis/tests/test_auto_install.py').read())
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(name)s: %(message)s'
)

print("=" * 60)
print("KARIOS Auto-Install Test")
print("=" * 60)

# Add plugin path
plugin_path = '/home/gautier/projects/isl/karios-qgis'
if plugin_path not in sys.path:
    sys.path.insert(0, plugin_path)

try:
    from dependency_checker import DependencyChecker, DependencyInfo
    print("✓ Imported dependency_checker")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Testing dependency check...")
print("=" * 60)

deps = [
    DependencyInfo("OpenCV", "cv2", "opencv-python-headless", min_version="4.0.0"),
    DependencyInfo("NumPy", "numpy", min_version="1.20.0"),
]

checker = DependencyChecker(deps)
results = checker.check_all()

print("\nDependency Status:")
for name, status in results.items():
    symbol = "✓" if status.installed else "✗"
    version = f" (v{status.version})" if status.version else ""
    print(f"  {symbol} {name}{version}")

missing = checker.get_missing()
print(f"\nMissing: {len(missing)} package(s)")

if missing:
    print("\n" + "=" * 60)
    print("Testing auto-install...")
    print("=" * 60)
    
    for i, status in enumerate(missing, 1):
        pkg_name = status.info.name
        pkg_package = status.info.package
        
        print(f"\n[{i}/{len(missing)}] Installing {pkg_name}...")
        print(f"  Package: {pkg_package}")
        
        # Test the install method from karios_qgis
        try:
            from karios_qgis import KariosQGISPlugin
            from qgis.utils import iface
            
            # Create a mock plugin instance
            class MockPlugin:
                def __init__(self):
                    self.iface = iface
            
            plugin = MockPlugin()
            
            # Import the install method
            import subprocess
            import importlib
            
            pip_cmd = [sys.executable, "-m", "pip"]
            package_spec = pkg_package
            cmd = pip_cmd + ["install", package_spec]
            
            print(f"  Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            print(f"  Return code: {result.returncode}")
            
            if result.returncode == 0:
                # Verify
                try:
                    importlib.import_module(status.info.import_name)
                    print(f"  ✓ SUCCESS - installed and imported!")
                except ImportError as e:
                    print(f"  ⚠ Installed but import failed: {e}")
            else:
                error = result.stderr.strip() or result.stdout.strip()
                print(f"  ✗ FAILED: {error}")
                
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Re-check
    print("\n" + "=" * 60)
    print("Re-checking dependencies...")
    print("=" * 60)
    
    checker.check_all()
    missing_after = checker.get_missing()
    
    if not missing_after:
        print("✓ All packages installed successfully!")
    else:
        print(f"✗ Still missing {len(missing_after)} package(s):")
        for status in missing_after:
            print(f"  - {status.info.name}")
else:
    print("✓ All dependencies already installed!")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
