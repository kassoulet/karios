# Automated Deployment Testing

## Overview

Test plugin deployment on Linux, Windows, and macOS using CI/CD pipelines.

## Testing Strategy

### 1. **Linux (GitHub Actions)**
- ✓ Automated on every commit
- ✓ QGIS Docker container
- ✓ Full installation test
- ✓ Dependency installation test

### 2. **Windows (GitHub Actions)**
- ✓ Automated on every commit
- ✓ QGIS standalone installation
- ✓ Full installation test
- ✓ Dependency installation test

### 3. **macOS (GitHub Actions)**
- ✓ Automated on every commit
- ✓ QGIS from DMG
- ✓ Full installation test
- ✓ Dependency installation test

### 4. **Manual Testing**
- ✓ Real hardware testing
- ✓ Different QGIS versions
- ✓ Network conditions
- ✓ Offline installation

## File Structure

```
karios-qgis/
├── .github/
│   └── workflows/
│       ├── test-linux.yml      # Linux CI
│       ├── test-windows.yml    # Windows CI
│       ├── test-macos.yml      # macOS CI
│       └── test-all.yml        # Master workflow
├── tests/
│   ├── test_install.py         # Installation test script
│   ├── test_dependencies.py    # Dependency verification
│   ├── test_plugin.py          # Plugin functionality
│   └── conftest.py             # Pytest configuration
├── scripts/
│   ├── setup_qgis_linux.sh     # Linux QGIS setup
│   ├── setup_qgis_windows.ps1  # Windows QGIS setup
│   ├── setup_qgis_macos.sh     # macOS QGIS setup
│   └── run_tests.sh            # Test runner
└── docs/
    └── TESTING.md              # This file
```

## GitHub Actions Workflows

### 1. Linux Test (`.github/workflows/test-linux.yml`)

```yaml
name: Test Linux

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        qgis-version: [release-3_28, release-3_34, latest]
    
    steps:
    - uses: actions/checkout@v4
      with:
        submodules: recursive
    
    - name: Set up QGIS Docker
      run: |
        docker pull qgis/qgis:${{ matrix.qgis-version }}
    
    - name: Run installation test
      run: |
        docker run --rm \
          -v ${{ github.workspace }}:/workspace \
          qgis/qgis:${{ matrix.qgis-version }} \
          python3 /workspace/tests/test_install.py
    
    - name: Verify dependencies
      run: |
        docker run --rm \
          -v ${{ github.workspace }}:/workspace \
          qgis/qgis:${{ matrix.qgis-version }} \
          python3 /workspace/tests/test_dependencies.py
```

### 2. Windows Test (`.github/workflows/test-windows.yml`)

```yaml
name: Test Windows

on:
  push:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v4
      with:
        submodules: recursive
    
    - name: Install QGIS
      shell: pwsh
      run: |
        # Download QGIS installer
        Invoke-WebRequest -Uri "https://qgis.org/downloads/QGIS-OSGeo4W-3.34.0-1.msi" -OutFile "qgis.msi"
        
        # Install silently
        Start-Process msiexec.exe -Wait -ArgumentList "/i qgis.msi /quiet"
        
        # Add to PATH
        $env:Path = "C:\OSGeo4W\bin;$env:Path"
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.9'
    
    - name: Run installation test
      shell: pwsh
      run: |
        python tests/test_install.py
    
    - name: Verify dependencies
      shell: pwsh
      run: |
        python tests/test_dependencies.py
```

### 3. macOS Test (`.github/workflows/test-macos.yml`)

```yaml
name: Test macOS

on:
  push:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: macos-latest
    
    strategy:
      matrix:
        qgis-version: [3.28, 3.34]
    
    steps:
    - uses: actions/checkout@v4
      with:
        submodules: recursive
    
    - name: Install QGIS
      run: |
        # Download QGIS
        curl -L "https://qgis.org/downloads/MacOS/QGIS-${{ matrix.qgis-version }}.dmg" -o qgis.dmg
        
        # Mount and install
        hdiutil attach qgis.dmg
        cp -R /Volumes/QGIS/QGIS.app /Applications/
        hdiutil detach /Volumes/QGIS
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.9'
    
    - name: Run installation test
      run: |
        # Run QGIS in batch mode
        /Applications/QGIS.app/Contents/MacOS/QGIS \
          --nolog \
          --noplugins \
          --code tests/test_install.py
    
    - name: Verify dependencies
      run: |
        python3 tests/test_dependencies.py
```

### 4. Master Workflow (`.github/workflows/test-all.yml`)

```yaml
name: Test All Platforms

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  linux:
    uses: ./.github/workflows/test-linux.yml
  
  windows:
    uses: ./.github/workflows/test-windows.yml
  
  macos:
    uses: ./.github/workflows/test-macos.yml
  
  notify:
    needs: [linux, windows, macos]
    runs-on: ubuntu-latest
    if: always()
    
    steps:
    - name: Check results
      run: |
        if [ "${{ needs.linux.result }}" == "failure" ] || \
           [ "${{ needs.windows.result }}" == "failure" ] || \
           [ "${{ needs.macos.result }}" == "failure" ]; then
          echo "❌ Some tests failed"
          exit 1
        else
          echo "✅ All tests passed"
        fi
```

## Test Scripts

### Installation Test (`tests/test_install.py`)

```python
#!/usr/bin/env python3
"""
Test plugin installation and dependency auto-install.
"""

import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def test_plugin_loads():
    """Test that plugin can be imported."""
    logger.info("Testing plugin import...")
    
    try:
        from karios_qgis import KariosQGISPlugin
        logger.info("✓ Plugin imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Plugin import failed: {e}")
        return False

def test_dependencies_installed():
    """Test that all dependencies are installed."""
    logger.info("Testing dependencies...")
    
    required = {
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'skimage': 'scikit-image',
        'pandas': 'pandas',
    }
    
    all_ok = True
    for import_name, display_name in required.items():
        try:
            __import__(import_name)
            logger.info(f"✓ {display_name} installed")
        except ImportError:
            logger.error(f"✗ {display_name} NOT installed")
            all_ok = False
    
    return all_ok

def test_auto_install():
    """Test auto-install functionality."""
    logger.info("Testing auto-install...")
    
    # Remove dependencies from sys.path if present
    site_packages = Path(__file__).parent.parent / 'site-packages'
    if str(site_packages) in sys.path:
        sys.path.remove(str(site_packages))
    
    # Force reimport to trigger auto-install
    import importlib
    from karios_qgis import KariosQGISPlugin
    
    # Mock QGIS interface
    class MockIface:
        class messageBar:
            @staticmethod
            def pushMessage(*args, **kwargs):
                logger.info(f"Message: {args}")
            @staticmethod
            def pushSuccess(*args, **kwargs):
                logger.info(f"Success: {args}")
            @staticmethod
            def pushWarning(*args, **kwargs):
                logger.warning(f"Warning: {args}")
            @staticmethod
            def pushCritical(*args, **kwargs):
                logger.error(f"Critical: {args}")
    
    # Create plugin instance (triggers auto-install)
    plugin = KariosQGISPlugin(MockIface())
    
    # Check if site-packages was created
    if site_packages.exists():
        logger.info(f"✓ site-packages created: {site_packages}")
        return True
    else:
        logger.error("✗ site-packages NOT created")
        return False

def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("KARIOS Plugin Installation Tests")
    logger.info("=" * 60)
    
    results = {
        'Plugin Import': test_plugin_loads(),
        'Auto Install': test_auto_install(),
        'Dependencies': test_dependencies_installed(),
    }
    
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("✓✓✓ ALL TESTS PASSED ✓✓✓")
        return 0
    else:
        logger.error("✗✗✗ SOME TESTS FAILED ✗✗✗")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

### Dependency Verification (`tests/test_dependencies.py`)

```python
#!/usr/bin/env python3
"""
Verify all dependencies are working correctly.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_opencv():
    """Test OpenCV functionality."""
    try:
        import cv2
        import numpy as np
        
        # Create test image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Test basic operation
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        logger.info(f"✓ OpenCV {cv2.__version__} working")
        return True
    except Exception as e:
        logger.error(f"✗ OpenCV failed: {e}")
        return False

def test_numpy():
    """Test NumPy functionality."""
    try:
        import numpy as np
        
        # Test array operations
        arr = np.array([1, 2, 3])
        result = arr * 2
        
        logger.info(f"✓ NumPy {np.__version__} working")
        return True
    except Exception as e:
        logger.error(f"✗ NumPy failed: {e}")
        return False

def test_skimage():
    """Test scikit-image functionality."""
    try:
        from skimage import filters
        import numpy as np
        
        # Test filter
        img = np.zeros((100, 100))
        result = filters.sobel(img)
        
        logger.info(f"✓ scikit-image working")
        return True
    except Exception as e:
        logger.error(f"✗ scikit-image failed: {e}")
        return False

def test_pandas():
    """Test pandas functionality."""
    try:
        import pandas as pd
        
        # Create DataFrame
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        result = df.sum()
        
        logger.info(f"✓ pandas {pd.__version__} working")
        return True
    except Exception as e:
        logger.error(f"✗ pandas failed: {e}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("Dependency Verification Tests")
    logger.info("=" * 60)
    
    tests = {
        'OpenCV': test_opencv(),
        'NumPy': test_numpy(),
        'scikit-image': test_skimage(),
        'pandas': test_pandas(),
    }
    
    logger.info("=" * 60)
    
    passed = sum(tests.values())
    total = len(tests)
    
    logger.info(f"Passed: {passed}/{total}")
    
    if all(tests.values()):
        logger.info("✓✓✓ ALL DEPENDENCIES WORKING ✓✓✓")
        return 0
    else:
        logger.error("✗✗✗ SOME DEPENDENCIES FAILED ✗✗✗")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

## Setup Scripts

### Linux Setup (`scripts/setup_qgis_linux.sh`)

```bash
#!/bin/bash
set -e

echo "Setting up QGIS for testing..."

# Add QGIS repository
sudo add-apt-repository ppa:ubuntugis/ppa
sudo apt-get update
sudo apt-get install -y qgis python3-qgis

# Verify installation
qgis --version
python3 -c "import qgis; print(f'QGIS {qgis.__version__}')"

echo "✓ QGIS setup complete"
```

### Windows Setup (`scripts/setup_qgis_windows.ps1`)

```powershell
# Download and install QGIS
$installer = "qgis.msi"
$downloadUrl = "https://qgis.org/downloads/QGIS-OSGeo4W-3.34.0-1.msi"

Invoke-WebRequest -Uri $downloadUrl -OutFile $installer

# Silent install
Start-Process msiexec.exe -Wait -ArgumentList "/i $installer /quiet"

# Add to PATH
$env:Path = "C:\OSGeo4W\bin;$env:Path"

# Verify
qgis --version

Write-Host "✓ QGIS setup complete"
```

### macOS Setup (`scripts/setup_qgis_macos.sh`)

```bash
#!/bin/bash
set -e

echo "Setting up QGIS for testing..."

# Download QGIS
curl -L "https://qgis.org/downloads/MacOS/QGIS-3.34.dmg" -o qgis.dmg

# Mount and install
hdiutil attach qgis.dmg
cp -R /Volumes/QGIS/QGIS.app /Applications/
hdiutil detach /Volumes/QGIS

# Verify
/Applications/QGIS.app/Contents/MacOS/QGIS --version

echo "✓ QGIS setup complete"
```

## Running Tests Locally

### All Tests

```bash
# Linux
./scripts/run_tests.sh

# Windows
.\scripts\run_tests.ps1

# macOS
./scripts/run_tests.sh
```

### Specific Platform

```bash
# Test in Docker (Linux)
docker run --rm -v $(pwd):/workspace qgis/qgis:latest \
  python3 /workspace/tests/test_install.py

# Test with specific QGIS version
docker run --rm -v $(pwd):/workspace qgis/qgis:release-3_28 \
  python3 /workspace/tests/test_install.py
```

## CI/CD Integration

### GitHub Actions Badge

Add to README.md:

```markdown
[![Test All Platforms](https://github.com/your-org/karios-qgis/actions/workflows/test-all.yml/badge.svg)](https://github.com/your-org/karios-qgis/actions/workflows/test-all.yml)
```

### Automated Releases

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    uses: ./.github/workflows/test-all.yml
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Create Release
      uses: softprops/action-gh-release@v1
      with:
        files: |
          karios-qgis.zip
          site-packages.zip
```

## Test Coverage Report

Generate coverage report:

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage
pytest --cov=karios_qgis --cov-report=html

# Open report
firefox htmlcov/index.html
```

## Summary

### Automated Testing

- ✓ **Linux** - GitHub Actions with Docker
- ✓ **Windows** - GitHub Actions with QGIS installer
- ✓ **macOS** - GitHub Actions with QGIS DMG
- ✓ **Multiple QGIS versions** - Test matrix
- ✓ **Dependency verification** - Functional tests

### Manual Testing

- ✓ **Real hardware** - Different machines
- ✓ **Network conditions** - Slow/unreliable connections
- ✓ **Offline mode** - Pre-installed dependencies

### Continuous Integration

- ✓ **Every commit** - Automatic testing
- ✓ **Pull requests** - Pre-merge validation
- ✓ **Releases** - Full test suite before deploy
