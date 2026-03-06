# KARIOS QGIS Plugin - Automated Testing

## Quick Start

### Run Tests Locally

```bash
# Test plugin imports and setup
python tests/test_install.py

# Test dependencies functionality
python tests/test_dependencies.py
```

### Run Tests in Docker (Linux)

```bash
# Test with latest QGIS
docker run --rm -v $(pwd):/workspace qgis/qgis:latest \
  python3 /workspace/tests/test_install.py

# Test with specific QGIS version
docker run --rm -v $(pwd):/workspace qgis/qgis:release-3_34 \
  python3 /workspace/tests/test_install.py
```

## CI/CD Automation

Tests run automatically on:
- ✓ Every push to `main` or `develop` branches
- ✓ Every pull request
- ✓ Manual trigger via GitHub Actions UI

### GitHub Actions

Workflows located in `.github/workflows/`:

| Workflow | Platform | QGIS Versions |
|----------|----------|---------------|
| `test-linux.yml` | Ubuntu (Docker) | 3.28, 3.34, latest |
| `test-windows.yml` | Windows 2022 | Latest |
| `test-macos.yml` | macOS 13 | Latest |
| `test-all.yml` | All platforms | Matrix |

## Test Coverage

### Installation Tests (`tests/test_install.py`)

1. **Plugin Import** - Can import `karios_qgis` module
2. **Dependency Checker** - Can import and use dependency checker
3. **Auto-Install Setup** - Plugin has dependencies defined
4. **Site-Packages** - Target folder exists or can be created
5. **Dependencies Status** - Check what's installed vs needs install

### Dependency Tests (`tests/test_dependencies.py`)

1. **OpenCV** - Image processing operations
2. **NumPy** - Array and matrix operations
3. **scikit-image** - Image filters and features
4. **pandas** - DataFrame operations
5. **All Imports** - Verify all modules can be imported

## Test Output

### Success Example

```
╔══════════════════════════════════════════════════════════╗
║               KARIOS Plugin Tests                        ║
╚══════════════════════════════════════════════════════════╝

============================================================
Test 1: Plugin Imports
============================================================
✓ Plugin module imported successfully

============================================================
Test 2: Dependency Checker
============================================================
✓ Dependency checker imported successfully
✓ Dependency checker works

...

============================================================
Test Summary
============================================================
✓ PASS: Plugin Import
✓ PASS: Dependency Checker
✓ PASS: Auto-Install Setup
✓ PASS: Site-Packages
✓ PASS: Dependencies

Passed: 5/5

╔══════════════════════════════════════════════════════════╗
║                  ALL TESTS PASSED                        ║
╚══════════════════════════════════════════════════════════╝
```

### Failure Example

```
============================================================
Test Summary
============================================================
✓ PASS: Plugin Import
✗ FAIL: Dependency Checker
✓ PASS: Auto-Install Setup
✓ PASS: Site-Packages
✓ PASS: Dependencies

Passed: 4/5

╔══════════════════════════════════════════════════════════╗
║                  SOME TESTS FAILED                       ║
╚══════════════════════════════════════════════════════════╝
```

## GitHub Actions Integration

### Add Badge to README

```markdown
[![Test All Platforms](https://github.com/your-org/karios-qgis/actions/workflows/test-all.yml/badge.svg)](https://github.com/your-org/karios-qgis/actions/workflows/test-all.yml)
```

### Enable Workflows

1. Push `.github/workflows/` to repository
2. Go to GitHub > Actions tab
3. Enable workflows if needed
4. Workflows run automatically on next push

### View Results

1. Go to GitHub repository
2. Click "Actions" tab
3. Select workflow run
4. View logs and test output

## Manual Testing Checklist

### Before Release

- [ ] Run tests on Linux (Docker)
- [ ] Run tests on Windows
- [ ] Run tests on macOS
- [ ] Test auto-install with missing dependencies
- [ ] Test with all dependencies pre-installed
- [ ] Test with slow network connection
- [ ] Test offline installation (site-packages folder)

### After Installation

- [ ] Plugin loads without errors
- [ ] All dependencies installed
- [ ] Processing algorithms available
- [ ] KARIOS processing runs successfully

## Troubleshooting

### Test Fails on Import

**Error:** `ModuleNotFoundError: No module named 'qgis'`

**Solution:** Run tests in QGIS environment:
```bash
# Docker
docker run --rm -v $(pwd):/workspace qgis/qgis:latest python3 tests/test_install.py

# Or with QGIS Python
/path/to/qgis/python.exe tests/test_install.py
```

### Test Fails on Dependencies

**Error:** `ImportError: No module named 'cv2'`

**Solution:** Dependencies will auto-install when plugin loads. Or manually:
```bash
python -m pip install --target site-packages \
  opencv-python-headless \
  numpy \
  scikit-image \
  pandas
```

### Docker Permission Denied

**Error:** `Permission denied while trying to connect to Docker daemon`

**Solution:** Add user to docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

## Continuous Integration

### Automated Testing

```yaml
# .github/workflows/test-all.yml
name: Test All Platforms

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
```

### Automated Releases

```yaml
# .github/workflows/release.yml
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
    # ... deployment steps
```

## Test Reports

### Generate Coverage Report

```bash
# Install pytest-cov
pip install pytest-cov

# Run tests with coverage
pytest --cov=karios_qgis --cov-report=html

# Open in browser
firefox htmlcov/index.html
```

### Upload to Coverage Service

```yaml
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
    flags: unittests
```

## Summary

### What's Tested

✓ Plugin imports correctly  
✓ Dependency checker works  
✓ Auto-install mechanism  
✓ Site-packages folder creation  
✓ All dependencies functional  

### Where Tests Run

✓ GitHub Actions (Linux, Windows, macOS)  
✓ Local Docker containers  
✓ Developer machines  

### When Tests Run

✓ Every commit  
✓ Every pull request  
✓ Before releases  
✓ On demand  

### Test Results

- **Green checkmark** ✓ - All tests passed
- **Red X** ✗ - Some tests failed
- **Yellow circle** ⚠ - Warnings but tests passed

View results at: https://github.com/your-org/karios-qgis/actions
