# Dependency Checker Module

A reusable, cross-platform Python module to check and install dependencies with a Qt dialog for QGIS plugins.

## Features

- ✓ Check if Python packages are installed
- ✓ Verify minimum version requirements
- ✓ Install missing packages via pip (Linux/Windows/macOS)
- ✓ Qt dialog with "Install Missing" button
- ✓ Progress feedback during installation
- ✓ Support for optional dependencies
- ✓ Reusable across projects

## Usage

### 1. Define Your Dependencies

```python
from dependency_checker import DependencyInfo

DEPENDENCIES = [
    DependencyInfo(
        name="OpenCV",
        import_name="cv2",
        package="opencv-python",  # Optional, defaults to import_name
        min_version="4.0.0",      # Optional
        optional=False,           # Optional, defaults to False
    ),
    DependencyInfo(
        name="NumPy",
        import_name="numpy",
        min_version="1.20.0",
    ),
    DependencyInfo(
        name="Pillow",
        import_name="PIL",
        package="Pillow",
        optional=True,  # Won't block installation
    ),
]
```

### 2. Quick Check (One-Liner)

```python
from dependency_checker import check_and_show_dialog

# In your plugin's initGui() or similar
all_ok = check_and_show_dialog(DEPENDENCIES, iface)
if not all_ok:
    # Handle missing dependencies
    pass
```

### 3. Advanced Usage

```python
from dependency_checker import DependencyChecker, show_dependency_dialog

# Create checker instance
checker = DependencyChecker(DEPENDENCIES)

# Check all dependencies
results = checker.check_all()

# Get summary
print(checker.summary())

# Check if any required dependencies are missing
if checker.has_missing():
    # Show Qt dialog with install button
    show_dependency_dialog(checker, iface)
    
    # Or install programmatically
    def progress_callback(message):
        print(message)
    
    results = checker.install_missing(callback=progress_callback)
```

### 4. Integration in QGIS Plugin

```python
# In your plugin class __init__
self.dependencies = [
    DependencyInfo("OpenCV", "cv2", "opencv-python"),
    DependencyInfo("NumPy", "numpy"),
]

# In initGui()
def initGui(self):
    checker = DependencyChecker(self.dependencies)
    checker.check_all()
    
    if checker.has_missing():
        check_and_show_dialog(
            self.dependencies,
            self.iface,
            title="My Plugin - Missing Dependencies",
            message="Please install the required dependencies:",
        )
    
    # Continue with plugin initialization...
```

## API Reference

### DependencyInfo

```python
DependencyInfo(
    name: str,           # Human-readable name
    import_name: str,    # Python import name
    package: str = None, # Pip package name (optional)
    min_version: str = None,  # Minimum version (optional)
    optional: bool = False,   # Is optional? (optional)
)
```

### DependencyChecker

```python
checker = DependencyChecker(dependencies: List[DependencyInfo])

# Check methods
checker.check_all() -> Dict[str, DependencyStatus]
checker.check_single(info: DependencyInfo) -> DependencyStatus
checker.has_missing() -> bool
checker.get_missing() -> List[DependencyStatus]
checker.summary() -> str

# Install methods
checker.install_single(info, callback=None) -> Tuple[bool, str]
checker.install_missing(callback=None) -> Dict[str, Tuple[bool, str]]
```

### Convenience Functions

```python
# Show dialog for missing dependencies
show_dependency_dialog(
    checker: DependencyChecker,
    iface,  # QGIS interface
    title: str = "Missing Dependencies",
    message: str = "The following dependencies are missing:",
) -> bool  # True if all installed after dialog

# Check and show dialog in one call
check_and_show_dialog(
    dependencies: List[DependencyInfo],
    iface,
    title: str = "Missing Dependencies",
    message: str = "The following dependencies are missing:",
    critical: bool = True,
) -> bool  # True if all satisfied
```

## Cross-Platform Support

The module handles platform differences automatically:

- **Linux**: Uses system Python's pip
- **Windows**: Uses Python executable path from `sys.executable`
- **macOS**: Uses Python executable path from `sys.executable`

All platforms use `python -m pip` for maximum compatibility.

## Testing

Run standalone test:

```bash
python dependency_checker.py
```

## License

Apache-2.0
