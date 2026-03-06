#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for KARIOS QGIS Plugin dependency checker.
Runs inside QGIS Docker container to verify plugin installation and dependency checking.

Usage:
    python test_plugin.py [--install-deps] [--verbose]

Arguments:
    --install-deps    Actually install missing dependencies (default: dry-run)
    --verbose         Show detailed output
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger("test_plugin")

# Add plugin directory to path
PLUGIN_DIR = Path("/root/.local/share/QGIS/QGIS3/profiles/default/python/plugins/karios_qgis")
sys.path.insert(0, str(PLUGIN_DIR))


class MockQgsInterface:
    """Mock QGIS interface for testing outside QGIS GUI."""

    def __init__(self):
        self._message_bar = MockMessageBar()
        self._main_window = None

    def messageBar(self):
        return self._message_bar

    def mainWindow(self):
        return self._main_window

    def addPluginToMenu(self, *args, **kwargs):
        pass

    def addToolBarIcon(self, *args, **kwargs):
        pass


class MockMessageBar:
    """Mock QGIS message bar."""

    def __init__(self):
        self.messages = []

    def pushInfo(self, title, message, *args, **kwargs):
        self.messages.append(("INFO", title, message))
        print(f"[INFO] {title}: {message}")

    def pushWarning(self, title, message, *args, **kwargs):
        self.messages.append(("WARNING", title, message))
        print(f"[WARNING] {title}: {message}")

    def pushCritical(self, title, message, *args, **kwargs):
        self.messages.append(("CRITICAL", title, message))
        print(f"[CRITICAL] {title}: {message}")

    def pushSuccess(self, title, message, *args, **kwargs):
        self.messages.append(("SUCCESS", title, message))
        print(f"[SUCCESS] {title}: {message}")


def print_section(title):
    """Print a section header."""
    logger.info("=" * 60)
    logger.info(f" {title}")
    logger.info("=" * 60)
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60 + "\n")


def test_imports():
    """Test that all required modules can be imported."""
    print_section("1. Testing Module Imports")
    logger.info("Testing module imports")

    errors = []

    try:
        from dependency_checker import (
            DependencyChecker,
            DependencyInfo,
            DependencyStatus,
            check_and_show_dialog,
            show_dependency_dialog,
        )
        logger.info("✓ dependency_checker module imported successfully")
        print("✓ dependency_checker module imported successfully")
    except ImportError as e:
        errors.append(f"Failed to import dependency_checker: {e}")
        logger.error(f"✗ Failed to import dependency_checker: {e}")
        print(f"✗ Failed to import dependency_checker: {e}")
        return errors

    try:
        from karios_qgis import KariosQGISPlugin, logger as plugin_logger
        logger.info("✓ karios_qgis module imported successfully")
        print("✓ karios_qgis module imported successfully")
    except ImportError as e:
        errors.append(f"Failed to import karios_qgis: {e}")
        logger.error(f"✗ Failed to import karios_qgis: {e}")
        print(f"✗ Failed to import karios_qgis: {e}")

    try:
        from processing.provider import KariosProvider
        logger.info("✓ processing.provider module imported successfully")
        print("✓ processing.provider module imported successfully")
    except ImportError as e:
        errors.append(f"Failed to import processing.provider: {e}")
        logger.error(f"✗ Failed to import processing.provider: {e}")
        print(f"✗ Failed to import processing.provider: {e}")

    return errors


def test_dependency_checker_api():
    """Test the DependencyChecker API."""
    print_section("2. Testing DependencyChecker API")

    from dependency_checker import DependencyChecker, DependencyInfo

    errors = []

    # Test DependencyInfo creation
    try:
        dep = DependencyInfo(
            name="Test Module",
            import_name="os",
            package="test-package",
            min_version="1.0.0",
            optional=True,
        )
        print(f"✓ DependencyInfo created: {dep.name}")
    except Exception as e:
        errors.append(f"Failed to create DependencyInfo: {e}")
        print(f"✗ Failed to create DependencyInfo: {e}")
        return errors

    # Test DependencyChecker creation
    try:
        dependencies = [
            DependencyInfo("OS Module", "os"),
            DependencyInfo("Sys Module", "sys"),
            DependencyInfo("NonExistent", "nonexistent_module", optional=True),
            DependencyInfo("NumPy", "numpy", min_version="1.0.0", optional=True),
        ]
        checker = DependencyChecker(dependencies)
        print("✓ DependencyChecker created successfully")
    except Exception as e:
        errors.append(f"Failed to create DependencyChecker: {e}")
        print(f"✗ Failed to create DependencyChecker: {e}")
        return errors

    # Test check_all()
    try:
        results = checker.check_all()
        print(f"✓ check_all() returned {len(results)} results")
        for import_name, status in results.items():
            symbol = "✓" if status.installed else "✗"
            version_info = f" (v{status.version})" if status.version else ""
            print(f"  {symbol} {import_name}{version_info}")
    except Exception as e:
        errors.append(f"check_all() failed: {e}")
        print(f"✗ check_all() failed: {e}")

    # Test has_missing()
    try:
        has_missing = checker.has_missing()
        print(f"✓ has_missing() = {has_missing}")
    except Exception as e:
        errors.append(f"has_missing() failed: {e}")
        print(f"✗ has_missing() failed: {e}")

    # Test get_missing()
    try:
        missing = checker.get_missing()
        print(f"✓ get_missing() returned {len(missing)} items")
    except Exception as e:
        errors.append(f"get_missing() failed: {e}")
        print(f"✗ get_missing() failed: {e}")

    # Test summary()
    try:
        summary = checker.summary()
        print("✓ summary() works:")
        for line in summary.split("\n"):
            print(f"    {line}")
    except Exception as e:
        errors.append(f"summary() failed: {e}")
        print(f"✗ summary() failed: {e}")

    return errors


def test_plugin_dependencies(iface, install_deps=False, verbose=False):
    """Test the plugin's actual dependency checking."""
    print_section("3. Testing Plugin Dependencies")

    from dependency_checker import DependencyChecker, DependencyInfo

    # These are the dependencies defined in karios_qgis.py
    dependencies = [
        DependencyInfo(
            name="OpenCV",
            import_name="cv2",
            package="opencv-python",
            min_version="4.0.0",
            optional=False,
        ),
        DependencyInfo(
            name="NumPy",
            import_name="numpy",
            min_version="1.20.0",
            optional=False,
        ),
    ]

    checker = DependencyChecker(dependencies)
    results = checker.check_all()

    print("Dependency Check Results:")
    print("-" * 50)

    all_installed = True
    for import_name, status in results.items():
        symbol = "✓" if status.installed else "✗"
        version_info = f" (v{status.version})" if status.version else ""
        print(f"  {symbol} {status.info.name}{version_info}")
        if not status.installed:
            all_installed = False
            if install_deps:
                print(f"      → Installing {status.info.package}...")
                success, msg = checker.install_single(
                    status.info,
                    callback=lambda m: print(f"      {m}") if verbose else None,
                )
                if success:
                    print(f"      ✓ Installation successful")
                else:
                    print(f"      ✗ Installation failed: {msg}")

    print("-" * 50)
    if all_installed:
        print("✓ All dependencies are satisfied!")
    else:
        if install_deps:
            # Re-check after installation
            checker.check_all()
            if not checker.has_missing():
                print("✓ All dependencies installed successfully!")
            else:
                print("⚠ Some dependencies still missing after installation")
        else:
            print("⚠ Some dependencies are missing")
            print("  Run with --install-deps to install them")

    return [] if all_installed or checker.has_missing() else ["Dependencies not satisfied"]


def test_plugin_initialization(iface):
    """Test plugin initialization."""
    print_section("4. Testing Plugin Initialization")

    from karios_qgis import KariosQGISPlugin

    errors = []

    try:
        plugin = KariosQGISPlugin(iface)
        print("✓ KariosQGISPlugin instance created")

        # Check that dependencies are defined
        if hasattr(plugin, "dependencies"):
            print(f"✓ Plugin has {len(plugin.dependencies)} dependencies defined")
            for dep in plugin.dependencies:
                print(f"    - {dep.name} ({dep.import_name})")
        else:
            errors.append("Plugin does not have 'dependencies' attribute")
            print("✗ Plugin does not have 'dependencies' attribute")

    except Exception as e:
        errors.append(f"Failed to create plugin instance: {e}")
        print(f"✗ Failed to create plugin instance: {e}")
        import traceback
        traceback.print_exc()

    return errors


def test_installation_script():
    """Test the installation script."""
    print_section("5. Testing Installation Script")

    install_script = PLUGIN_DIR / "install_plugin.py"

    if not install_script.exists():
        print(f"✗ Installation script not found: {install_script}")
        return ["Installation script not found"]

    print(f"✓ Installation script found: {install_script}")

    try:
        # Try to import it
        import importlib.util
        spec = importlib.util.spec_from_file_location("install_plugin", install_script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print("✓ Installation script can be imported")

        # Check for required functions
        if hasattr(module, "install_plugin"):
            print("✓ install_plugin() function exists")
        else:
            print("⚠ install_plugin() function not found")

    except Exception as e:
        print(f"✗ Failed to import installation script: {e}")
        return [f"Installation script import failed: {e}"]

    return []


def run_all_tests(install_deps=False, verbose=False):
    """Run all tests and report results."""
    print_section("KARIOS QGIS Plugin - Docker Test Suite")
    logger.info("Starting KARIOS QGIS Plugin Docker Test Suite")
    logger.info(f"Plugin directory: {PLUGIN_DIR}")
    logger.info(f"Install dependencies: {install_deps}")
    logger.info(f"Verbose: {verbose}")
    
    print(f"Plugin directory: {PLUGIN_DIR}")
    print(f"Install dependencies: {install_deps}")
    print(f"Verbose: {verbose}")

    # Create mock interface
    iface = MockQgsInterface()

    all_errors = []

    # Run tests
    all_errors.extend(test_imports())
    all_errors.extend(test_dependency_checker_api())
    all_errors.extend(test_plugin_dependencies(iface, install_deps, verbose))
    all_errors.extend(test_plugin_initialization(iface))
    all_errors.extend(test_installation_script())

    # Summary
    print_section("Test Summary")

    if all_errors:
        logger.error(f"Tests failed with {len(all_errors)} error(s)")
        print(f"✗ {len(all_errors)} test(s) failed:")
        for i, error in enumerate(all_errors, 1):
            print(f"  {i}. {error}")
        print("\n" + "=" * 60)
        print(" TESTS FAILED")
        print("=" * 60)
        return 1
    else:
        logger.info("All tests passed!")
        print("✓ All tests passed!")
        print("\n" + "=" * 60)
        print(" TESTS PASSED")
        print("=" * 60)
        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test KARIOS QGIS Plugin in Docker"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Actually install missing dependencies (default: dry-run)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    args = parser.parse_args()

    # Verify plugin directory exists
    if not PLUGIN_DIR.exists():
        print(f"ERROR: Plugin directory not found: {PLUGIN_DIR}")
        print("Make sure the plugin is installed in the QGIS Docker container")
        sys.exit(1)

    # Run tests
    exit_code = run_all_tests(args.install_deps, args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
