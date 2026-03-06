# -*- coding: utf-8 -*-
"""
Dependency Checker Module - Generic Python dependency management for QGIS plugins

This module provides utilities to check and install Python dependencies with:
- Automatic version checking using importlib.metadata
- Isolated installation to plugin directory
- Background execution with progress reporting
- Cross-platform support (Windows, Linux, macOS)

Copyright (C) 2026 Telespazio
License: GPL-3.0
"""

import importlib
import importlib.util
import logging
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple, Callable, Any

try:
    from importlib import metadata
except ImportError:
    metadata = None

# Configure logging
logger = logging.getLogger("qgis_plugin_deps")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class DependencyInfo:
    """Information about a single dependency."""

    def __init__(
        self,
        name: str,
        import_name: str,
        package: Optional[str] = None,
        min_version: Optional[str] = None,
        optional: bool = False,
        installable: bool = True,
    ):
        """
        Initialize dependency info.

        :param name: Human-readable name (e.g., "OpenCV")
        :param import_name: Python import name (e.g., "cv2")
        :param package: Pip package name (defaults to import_name)
        :param min_version: Minimum version string (e.g., "4.0.0")
        :param optional: Whether the dependency is optional
        :param installable: Whether this package can be installed via pip
                           (False for system-provided packages like QGIS bundled libs)
        """
        self.name = name
        self.import_name = import_name
        self.package = package or import_name
        self.min_version = min_version
        self.optional = optional
        self.installable = installable


class DependencyStatus:
    """Status of a single dependency check."""

    def __init__(
        self,
        info: DependencyInfo,
        installed: bool = False,
        version: Optional[str] = None,
        error: Optional[str] = None,
        version_ok: bool = True,
        path: Optional[str] = None,
    ):
        self.info = info
        self.installed = installed
        self.version = version
        self.error = error
        self.version_ok = version_ok
        self.path = path

    def __str__(self) -> str:
        if self.installed:
            version_str = f" (v{self.version})" if self.version else ""
            status = "✓" if self.version_ok else "⚠"
            if not self.version_ok:
                return f"{status} {self.info.name}{version_str} - Needs v{self.info.min_version}"
            return f"{status} {self.info.name}{version_str}"
        else:
            status = "✗" if not self.info.optional else "○"
            return f"{status} {self.info.name} (missing)"


class DependencyChecker:
    """
    Check and install Python dependencies with cross-platform support.
    """

    def __init__(self, dependencies: List[DependencyInfo]):
        """
        Initialize the dependency checker.

        :param dependencies: List of DependencyInfo objects
        """
        self.dependencies = dependencies
        self.results: Dict[str, DependencyStatus] = {}

    @staticmethod
    def parse_requirements(
        requirements_path: str,
        optional_packages: Optional[List[str]] = None,
        version_map: Optional[Dict[str, str]] = None,
    ) -> List[DependencyInfo]:
        """
        Parse a requirements.txt file and convert to DependencyInfo objects.

        :param requirements_path: Path to requirements.txt file
        :param optional_packages: List of package names to mark as optional
        :param version_map: Dict mapping import names to min versions
        :returns: List of DependencyInfo objects
        """
        if optional_packages is None:
            optional_packages = []
        if version_map is None:
            version_map = {}

        dependencies = []

        if not os.path.exists(requirements_path):
            logger.warning(f"Requirements file not found: {requirements_path}")
            return dependencies

        with open(requirements_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Skip options like -r, -e, --extra-index-url, etc.
                if line.startswith("-"):
                    continue

                # Parse package specification
                # Examples:
                #   package-name
                #   package-name==1.0.0
                #   package-name>=1.0.0
                #   package-name>=1.0.0,<2.0.0
                #   package-name[extra]>=1.0.0

                # Extract package name (before any version specifier or extras)
                match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                if not match:
                    logger.debug(f"Skipping invalid line: {line}")
                    continue

                package_name = match.group(1)
                package_name_normalized = package_name.lower().replace("-", "_")

                # Try to determine import name (usually same as package name)
                import_name = package_name_normalized

                # Common package name to import name mappings
                import_name_map = {
                    "scikit_image": "skimage",
                    "scikit_learn": "sklearn",
                    "opencv_python": "cv2",
                    "opencv_python_headless": "cv2",
                    "pillow": "PIL",
                    "beautifulsoup4": "bs4",
                }
                import_name = import_name_map.get(
                    package_name_normalized, import_name
                )

                # Extract version from requirements line if present
                min_version = version_map.get(import_name)
                if not min_version:
                    version_match = re.search(r">=([0-9.]+)", line)
                    if version_match:
                        min_version = version_match.group(1)

                # Determine if optional
                is_optional = package_name_normalized in optional_packages

                dependencies.append(
                    DependencyInfo(
                        name=package_name.replace("_", " ").title(),
                        import_name=import_name,
                        package=package_name,
                        min_version=min_version,
                        optional=is_optional,
                    )
                )

        logger.info(
            f"Parsed {len(dependencies)} dependencies from {requirements_path}"
        )
        return dependencies

    def _get_pip_command(self) -> List[str]:
        """Get the appropriate pip command for the current platform."""
        python_executable = sys.executable
        # Handle QGIS on Windows where sys.executable might be qgis-bin.exe
        if os.path.basename(python_executable).lower() in ("qgis.exe", "qgis-bin.exe"):
            python_w = os.path.join(os.path.dirname(python_executable), "pythonw.exe")
            python_exe = os.path.join(os.path.dirname(python_executable), "python.exe")
            if os.path.exists(python_exe):
                python_executable = python_exe
            elif os.path.exists(python_w):
                python_executable = python_w

        return [python_executable, "-m", "pip"]

    def _parse_version(self, version_str: str) -> Tuple[int, ...]:
        """Parse version string to comparable tuple."""
        if not version_str:
            return (0,)
        match = re.match(r"([\d.]+)", str(version_str))
        if match:
            parts = match.group(1).split(".")
            return tuple(int(p) for p in parts if p.isdigit())
        return (0,)

    def _check_version(self, actual: str, minimum: str) -> bool:
        """Check if actual version meets minimum requirement."""
        a = self._parse_version(actual)
        m = self._parse_version(minimum)
        # Pad with zeros for correct comparison (e.g., 1.7 >= 1.7.0)
        max_len = max(len(a), len(m))
        a_padded = a + (0,) * (max_len - len(a))
        m_padded = m + (0,) * (max_len - len(m))
        return a_padded >= m_padded

    def _get_module_version(self, info: DependencyInfo) -> Optional[str]:
        """Try to get the version of an installed module without full import if possible."""
        # 1. Try metadata (package name)
        if metadata:
            try:
                return metadata.version(info.package)
            except Exception:
                pass

            # 2. Try metadata (import name)
            try:
                return metadata.version(info.import_name)
            except Exception:
                pass

        # 3. Fallback: try to import and look for version attributes
        try:
            # Check if already in sys.modules to avoid side effects of re-import
            if info.import_name in sys.modules:
                module = sys.modules[info.import_name]
            else:
                # Use find_spec to see if it's available before importing
                spec = importlib.util.find_spec(info.import_name)
                if spec is None:
                    return None
                module = importlib.import_module(info.import_name)

            for attr in ["__version__", "version", "VERSION"]:
                if hasattr(module, attr):
                    version = getattr(module, attr)
                    if isinstance(version, tuple):
                        return ".".join(str(v) for v in version)
                    return str(version)
        except Exception:
            pass

        return None

    def check_single(self, info: DependencyInfo) -> DependencyStatus:
        """Check a single dependency."""
        try:
            # First check if it can be found without importing
            spec = importlib.util.find_spec(info.import_name)
            if spec is None:
                return DependencyStatus(info=info, installed=False)

            version = self._get_module_version(info)

            # Determine path
            path = getattr(spec, "origin", None)
            if path is None and hasattr(spec, "submodule_search_locations"):
                locs = spec.submodule_search_locations
                if locs:
                    path = list(locs)[0]

            version_ok = True
            if info.min_version and version:
                version_ok = self._check_version(version, info.min_version)

            return DependencyStatus(
                info=info,
                installed=True,
                version=version,
                path=path,
                version_ok=version_ok,
            )
        except Exception as e:
            logger.debug(f"Error checking {info.name}: {e}")
            return DependencyStatus(info=info, installed=False, error=str(e))

    def check_all(self) -> Dict[str, DependencyStatus]:
        """Check all dependencies."""
        self.results = {}
        for info in self.dependencies:
            self.results[info.import_name] = self.check_single(info)
        return self.results

    def has_missing(self) -> bool:
        """Check if there are any missing or invalid non-optional dependencies."""
        if not self.results:
            self.check_all()
        return any(
            (not s.installed or not s.version_ok) and not s.info.optional
            for s in self.results.values()
        )

    def has_missing_installable(self) -> bool:
        """Check if there are any missing installable non-optional dependencies."""
        if not self.results:
            self.check_all()
        return any(
            (not s.installed or not s.version_ok) and not s.info.optional and s.info.installable
            for s in self.results.values()
        )

    def get_missing(self) -> List[DependencyStatus]:
        """Get list of all missing or invalid non-optional dependencies."""
        if not self.results:
            self.check_all()
        return [
            s
            for s in self.results.values()
            if (not s.installed or not s.version_ok) and not s.info.optional
        ]

    def get_missing_installable(self) -> List[DependencyStatus]:
        """Get list of missing installable non-optional dependencies."""
        if not self.results:
            self.check_all()
        return [
            s
            for s in self.results.values()
            if (not s.installed or not s.version_ok) and not s.info.optional and s.info.installable
        ]

    def get_missing_non_installable(self) -> List[DependencyStatus]:
        """Get list of missing non-installable dependencies (system-provided)."""
        if not self.results:
            self.check_all()
        return [
            s
            for s in self.results.values()
            if (not s.installed or not s.version_ok) and not s.info.optional and not s.info.installable
        ]

    def install_missing(
        self,
        target_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Tuple[bool, str]]:
        """
        Install all missing non-optional installable dependencies.

        :param target_dir: Directory to install packages (isolated)
        :param progress_callback: Optional callback for progress messages
        :returns: Dictionary mapping import names to (success, message) tuples
        """
        if not self.results:
            self.check_all()

        results = {}
        missing = self.get_missing_installable()

        for status in missing:
            success, msg = self._install_single(
                status.info, target_dir=target_dir, callback=progress_callback
            )
            results[status.info.import_name] = (success, msg)

            # Re-check this one immediately to update internal state
            self.results[status.info.import_name] = self.check_single(status.info)

        return results

    def _install_single(
        self,
        info: DependencyInfo,
        target_dir: Optional[str] = None,
        callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """Install a single dependency."""
        pip_cmd = self._get_pip_command()
        package_spec = info.package

        # If it was installed but version was too low, we need to upgrade
        if info.min_version:
            package_spec = f"{info.package}>={info.min_version}"

        cmd = pip_cmd + ["install", package_spec]

        if target_dir:
            cmd += ["--target", target_dir, "--upgrade", "--no-cache-dir"]

        if callback:
            callback(f"Installing {info.name}...")

        try:
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # We don't re-check here, install_missing will do it or caller will
                msg = f"✓ {info.name} installed successfully"
                if callback:
                    callback(msg)
                return True, msg
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                # Clean up error message if it's too long
                if len(error_msg) > 200:
                    error_msg = error_msg[:197] + "..."
                msg = f"✗ Failed to install {info.name}: {error_msg}"
                if callback:
                    callback(msg)
                return False, msg

        except subprocess.TimeoutExpired:
            msg = f"✗ Installation of {info.name} timed out"
            if callback:
                callback(msg)
            return False, msg
        except Exception as e:
            msg = f"✗ Error installing {info.name}: {str(e)}"
            if callback:
                callback(msg)
            return False, msg

    def summary(self) -> str:
        """Get a human-readable summary of dependency status."""
        if not self.results:
            self.check_all()

        lines = ["Dependency Status:", "-" * 40]
        for status in self.results.values():
            lines.append(str(status))

        total = len(self.results)
        installed = sum(
            1 for s in self.results.values() if s.installed and s.version_ok
        )

        lines.append("-" * 40)
        lines.append(f"Satisfied: {installed}/{total}")
        return "\n".join(lines)


# ============================================================================
# Background Dependency Checking (Qt Thread)
# ============================================================================

try:
    from qgis.PyQt.QtCore import QObject, pyqtSignal, QThread
    from typing import Optional as QOptional

    HAS_QT = True
except ImportError:
    HAS_QT = False


if HAS_QT:

    class DependencyWorkerSignals(QObject):
        """Signals for the dependency worker thread."""

        started = pyqtSignal()
        finished = pyqtSignal(bool)
        progress_message = pyqtSignal(str)
        log_message = pyqtSignal(str, int)

    class DependencyWorker(QThread):
        """
        Background worker for checking and installing dependencies.
        Runs in a separate thread to avoid blocking the UI.
        """

        def __init__(
            self,
            plugin_dir: str,
            dependencies: list,
            parent: QOptional[QObject] = None,
            simulate_delay: bool = False,
        ):
            super().__init__(parent)
            self.plugin_dir = plugin_dir
            self.dependencies = dependencies
            self.signals = DependencyWorkerSignals()
            self._result = False
            self.messages = []
            self.simulate_delay = simulate_delay

        def run(self):
            """Execute dependency check in background thread."""
            try:
                self.signals.started.emit()
                self.signals.progress_message.emit("Checking dependencies...")

                # Add dependencies folder to sys.path only if it exists and is not empty
                dependencies_dir = os.path.join(self.plugin_dir, "dependencies")
                if os.path.exists(dependencies_dir):
                    # Check if folder has actual content (not just empty)
                    if os.listdir(dependencies_dir):
                        if dependencies_dir not in sys.path:
                            sys.path.insert(0, dependencies_dir)
                            logger.info(f"Added dependencies to path: {dependencies_dir}")
                    else:
                        logger.debug(f"Dependencies folder is empty, not adding to path")
                else:
                    logger.debug(f"Dependencies folder does not exist, will create if needed")

                # Progress callback
                def on_progress(message: str):
                    self.messages.append(message)
                    self.signals.progress_message.emit(message)

                # Run check and install
                self._result = check_and_install_dependencies(
                    self.dependencies,
                    self.plugin_dir,
                    progress_callback=on_progress,
                    simulate_delay=self.simulate_delay,
                )

            except Exception as e:
                logger.error(f"Dependency worker error: {e}", exc_info=True)
                err_msg = f"Critical Error: {e}"
                self.messages.append(err_msg)
                self.signals.log_message.emit(err_msg, 2)
                self._result = False
            finally:
                self.signals.finished.emit(self._result)

    class BackgroundDependencyChecker:
        """
        Manages background dependency checking with progress reporting.
        """

        def __init__(
            self,
            iface: Any,
            plugin_dir: str,
            dependencies: list,
            on_complete: QOptional[Callable[[bool], None]] = None,
            result_dockwidget: Any = None,
        ):
            self.iface = iface
            self.plugin_dir = plugin_dir
            self.dependencies = dependencies
            self.on_complete = on_complete
            self.result_dockwidget = result_dockwidget
            self.worker: QOptional[DependencyWorker] = None

        def start(self):
            """Start background dependency checking."""

            def update_progress(message: str, is_error: bool = False):
                if not message:
                    return
                if self.result_dockwidget and hasattr(
                    self.result_dockwidget, "set_progress_visible"
                ):
                    self.result_dockwidget.set_progress_visible(True)
                    self.result_dockwidget.set_progress_status(message, is_error)

            self.worker = DependencyWorker(self.plugin_dir, self.dependencies)
            self.worker.signals.started.connect(
                lambda: update_progress("Checking dependencies...")
            )
            self.worker.signals.progress_message.connect(
                lambda msg: update_progress(self._extract_status_message(msg))
            )
            self.worker.signals.finished.connect(self._on_finished)
            self.worker.start()

        def _extract_status_message(self, msg: str) -> str:
            """Extract a clean status message for progress display."""
            if not msg:
                return ""

            if "Installing" in msg:
                match = re.search(r"Installing\s+([^\s(]+)", msg)
                if match:
                    return f"Installing {match.group(1)}..."
                return "Installing dependencies..."

            if "successfully" in msg or "✓" in msg:
                match = re.search(r"[✓]\s+([^\s]+)\s+installed", msg)
                if match:
                    return f"✓ {match.group(1)} ready"
                return "✓ Dependency ready"

            if "All dependencies satisfied" in msg:
                return "✓ Dependencies ready"

            # If it's an error, return it as is (will be handled by update_progress)
            if "✗" in msg or "Failed" in msg or "Error" in msg:
                return msg

            return msg if len(msg) < 60 else None

        def _on_finished(self, success: bool):
            """Handle worker completion."""
            if self.result_dockwidget and hasattr(
                self.result_dockwidget, "set_progress_visible"
            ):
                if success:
                    self.result_dockwidget.set_progress_visible(False)
                else:
                    # Installation failed
                    if hasattr(self.worker, "messages"):
                        # Don't overwrite, merge if possible
                        if hasattr(self.result_dockwidget, "_all_messages"):
                            for m in self.worker.messages:
                                if m not in self.result_dockwidget._all_messages:
                                    self.result_dockwidget._all_messages.append(m)

                    self.result_dockwidget.set_progress_status(
                        "⚠ Dependency error - click for details", is_error=True
                    )

            if self.on_complete:
                self.on_complete(success)

            if self.worker:
                self.worker.deleteLater()
                self.worker = None

    def check_dependencies_background(
        iface: Any,
        plugin_dir: str,
        dependencies: list,
        on_complete: QOptional[Callable[[bool], None]] = None,
        result_dockwidget: Any = None,
    ) -> BackgroundDependencyChecker:
        """
        Start background dependency checking.
        """
        checker = BackgroundDependencyChecker(
            iface, plugin_dir, dependencies, on_complete, result_dockwidget
        )
        checker.start()
        return checker


# ============================================================================
# Qt Dialog Functions
# ============================================================================

if HAS_QT:
    from qgis.PyQt.QtCore import Qt, QSize, QCoreApplication
    from qgis.PyQt.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QListWidget,
        QListWidgetItem,
        QTextEdit,
        QProgressBar,
        QMessageBox,
    )

    class DependencyDialog(QDialog):
        """Qt dialog for displaying and installing missing dependencies."""

        def __init__(
            self,
            checker: DependencyChecker,
            iface: Any,
            title: str = "Missing Dependencies",
            message: str = "The following dependencies are missing:",
            parent: Any = None,
            auto_install: bool = True,
        ):
            super().__init__(parent)
            self.checker = checker
            self.iface = iface
            self.title = title
            self.message = message
            self.install_target = None
            self.auto_install = auto_install
            self._setup_ui()
            
            # Auto-start installation if requested
            if self.auto_install:
                QCoreApplication.processEvents()  # Let dialog render first
                self._on_install_clicked()

        def _setup_ui(self):
            """Set up the dialog UI."""
            self.setWindowTitle(self.title)
            self.setMinimumSize(500, 400)
            self.setModal(True)

            layout = QVBoxLayout()
            self.setLayout(layout)

            # Message label
            msg_label = QLabel(self.message)
            msg_label.setWordWrap(True)
            layout.addWidget(msg_label)

            # List of missing dependencies
            self.list_widget = QListWidget()
            self.list_widget.setMinimumHeight(150)
            missing = self.checker.get_missing()
            for status in missing:
                item_text = f"{status.info.name}"
                if status.info.min_version:
                    item_text += f" (needs v{status.info.min_version})"
                if status.installed and not status.version_ok:
                    item_text += f" [installed: {status.version}]"
                else:
                    item_text += " [not installed]"
                item = QListWidgetItem(item_text)
                self.list_widget.addItem(item)
            layout.addWidget(QLabel("Missing dependencies:"))
            layout.addWidget(self.list_widget)

            # Progress bar (indeterminate, visible during install)
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setFormat("%p% - Checking and installing...")
            layout.addWidget(self.progress_bar)

            # Log text (hidden initially)
            self.log_text = QTextEdit()
            self.log_text.setVisible(False)
            self.log_text.setReadOnly(True)
            self.log_text.setMaximumHeight(100)
            layout.addWidget(QLabel("Installation log:"))
            layout.addWidget(self.log_text)

            # Status label
            self.status_label = QLabel("")
            self.status_label.setWordWrap(True)
            layout.addWidget(self.status_label)

            # Buttons
            button_layout = QHBoxLayout()
            button_layout.addStretch()

            self.install_button = QPushButton("Install Missing")
            self.install_button.clicked.connect(self._on_install_clicked)
            button_layout.addWidget(self.install_button)

            self.close_button = QPushButton("Close")
            self.close_button.clicked.connect(self.accept)
            self.close_button.setEnabled(False)  # Disabled until install completes
            button_layout.addWidget(self.close_button)

            layout.addLayout(button_layout)

        def _on_install_clicked(self):
            """Handle install button click."""
            self.install_button.setEnabled(False)
            self.close_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.log_text.setVisible(True)
            self.status_label.setText("Checking and installing dependencies...")

            # Set installation target
            if self.install_target is None:
                self.install_target = os.path.join(
                    self.iface and hasattr(self.iface, "mainWindow") and
                    getattr(self.iface.mainWindow(), "plugin_dir", None) or
                    os.path.dirname(__file__),
                    "dependencies",
                )

            def log_message(msg: str):
                """Add message to log."""
                self.log_text.append(msg)
                self.log_text.scrollToBottom()
                # Update status label with latest message
                clean_msg = msg.replace("✓ ", "").replace("✗ ", "")
                if len(clean_msg) > 50:
                    clean_msg = clean_msg[:47] + "..."
                self.status_label.setText(clean_msg)

            # Run installation in background thread
            self.worker = DependencyWorker(
                os.path.dirname(self.install_target),
                [s.info for s in self.checker.get_missing()],
                simulate_delay=True,
            )
            self.worker.signals.started.connect(
                lambda: log_message("Starting installation...")
            )
            self.worker.signals.progress_message.connect(log_message)
            self.worker.signals.finished.connect(self._on_install_finished)
            self.worker.start()

        def _on_install_finished(self, success: bool):
            """Handle installation completion."""
            self.progress_bar.setVisible(False)
            self.install_button.setEnabled(True)
            self.close_button.setEnabled(True)

            # Re-check dependencies
            self.checker.check_all()

            if success and not self.checker.has_missing():
                self.status_label.setText("✓ All dependencies installed successfully!")
                QMessageBox.information(
                    self,
                    "Success",
                    "All dependencies installed successfully!",
                )
                self.accept()
            else:
                self.status_label.setText("⚠ Installation incomplete")
                QMessageBox.warning(
                    self,
                    "Installation Incomplete",
                    "Some dependencies could not be installed. "
                    "Please try installing them manually.",
                )
                # Refresh the list
                self.list_widget.clear()
                missing = self.checker.get_missing()
                for status in missing:
                    item_text = f"{status.info.name}"
                    if status.info.min_version:
                        item_text += f" (needs v{status.info.min_version})"
                    item_text += " [still missing]"
                    item = QListWidgetItem(item_text)
                    self.list_widget.addItem(item)

    def show_dependency_dialog(
        checker: DependencyChecker,
        iface: Any,
        title: str = "Missing Dependencies",
        message: str = "The following dependencies are missing:",
        on_install_complete: Optional[Callable[[bool], None]] = None,
    ) -> bool:
        """
        Show a Qt dialog for missing dependencies with install button.

        :param checker: DependencyChecker instance with results
        :param iface: QGIS interface instance
        :param title: Dialog title
        :param message: Message to display
        :param on_install_complete: Optional callback(success: bool)
        :returns: True if all dependencies satisfied after dialog closes
        """
        if not HAS_QT:
            logger.error("Qt not available, cannot show dependency dialog")
            return False

        dialog = DependencyDialog(checker, iface, title, message)

        # Set installation target to plugin's dependencies folder
        if hasattr(iface, "mainWindow"):
            plugin_dir = getattr(iface.mainWindow(), "plugin_dir", None)
        else:
            plugin_dir = None

        if plugin_dir is None:
            # Try to get from checker or use current directory
            plugin_dir = os.path.dirname(__file__)

        dialog.install_target = os.path.join(plugin_dir, "dependencies")

        # Add callback handling
        original_on_complete = on_install_complete

        def on_dialog_finished(result):
            """Handle dialog completion."""
            success = result == QDialog.Accepted or not checker.has_missing()
            if original_on_complete:
                original_on_complete(success)

        dialog.finished.connect(on_dialog_finished)
        dialog.exec_()

        return not checker.has_missing()


def check_and_show_dialog(
    dependencies: List[DependencyInfo],
    iface: Any,
    title: str = "Missing Dependencies",
    message: str = "The following dependencies are missing:",
    critical: bool = True,
) -> bool:
    """
    Check dependencies and show dialog if any are missing.

    :param dependencies: List of DependencyInfo objects
    :param iface: QGIS interface instance
    :param title: Dialog title
    :param message: Message to display
    :param critical: If True, show critical error if dialog cannot be shown
    :returns: True if all dependencies satisfied
    """
    checker = DependencyChecker(dependencies)
    checker.check_all()

    if checker.has_missing():
        if HAS_QT:
            return show_dependency_dialog(checker, iface, title, message)
        else:
            # No Qt, just log
            logger.error(checker.summary())
            if critical:
                logger.critical(
                    "Missing dependencies and Qt not available for dialog"
                )
            return False
    else:
        return True


# ============================================================================
# Main Installation Function
# ============================================================================


def check_and_install_dependencies(
    dependencies: List[DependencyInfo],
    plugin_dir: str,
    progress_callback: Optional[Callable[[str], None]] = None,
    simulate_delay: bool = False,
) -> bool:
    """
    Check dependencies and install missing installable ones to plugin directory.

    :param dependencies: List of DependencyInfo objects
    :param plugin_dir: Plugin directory for isolated installation
    :param progress_callback: Optional callback(message: str) for real-time progress
    :param simulate_delay: If True, add 10s delay to simulate installation time
    :returns: True if all dependencies are satisfied (or only non-installable ones missing)
    """
    logger.info("Starting dependency check")

    checker = DependencyChecker(dependencies)

    # Check phase with simulated delay
    if progress_callback:
        progress_callback("Checking dependencies...")

    if simulate_delay:
        import time
        # Simulate check time (part of 10s total)
        for i in range(1, 4):
            if progress_callback:
                progress_callback(f"Checking... ({i}/3)")
            time.sleep(3)

    checker.check_all()

    # Check for missing non-installable dependencies first (system-provided)
    missing_non_installable = checker.get_missing_non_installable()
    if missing_non_installable:
        logger.warning("Missing system-provided dependencies (cannot install):")
        for s in missing_non_installable:
            logger.warning(f"  - {s.info.name} ({s.info.import_name})")
        if progress_callback:
            progress_callback("⚠ Some system dependencies missing")

    # Only set up target dir if there are installable packages to install
    missing_installable = checker.get_missing_installable()
    if missing_installable:
        target_dir = os.path.join(plugin_dir, "dependencies")
        os.makedirs(target_dir, exist_ok=True)

        if target_dir not in sys.path:
            sys.path.insert(0, target_dir)

        logger.info(f"Installing {len(missing_installable)} missing installable dependencies")
        if progress_callback:
            progress_callback(f"Found {len(missing_installable)} packages to install...")

        # Simulate remaining delay during installation (10s total - check time)
        if simulate_delay:
            import time
            remaining_delay = 7  # seconds
            steps = 5
            step_delay = remaining_delay / steps
            for i in range(1, steps + 1):
                if progress_callback:
                    progress_callback(f"Installing dependencies... ({i}/{steps})")
                time.sleep(step_delay)

        # Use the checker to install missing installable ones
        checker.install_missing(target_dir=target_dir, progress_callback=progress_callback)

        # Final re-check
        checker.check_all()
        if checker.has_missing_installable():
            remaining = checker.get_missing_installable()
            for s in remaining:
                logger.error(f"Failed to satisfy dependency: {s.info.name}")
            if progress_callback:
                progress_callback("✗ Some dependencies failed to install")
            return False

        logger.info("All installable dependencies installed and verified")
        if progress_callback:
            progress_callback("✓ Dependencies ready")
    else:
        logger.info("All installable dependencies satisfied")
        if progress_callback:
            progress_callback("✓ All dependencies satisfied")

    # Return True if all installable deps are satisfied (non-installable ones are user's responsibility)
    return not checker.has_missing_installable()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example configuration
    EXAMPLE_DEPENDENCIES = [
        DependencyInfo("SciPy", "scipy", min_version="1.7.0"),
        DependencyInfo("NumPy", "numpy", min_version="1.20.0", optional=True),
        DependencyInfo(
            "scikit-image", "skimage", package="scikit-image", min_version="0.18.0"
        ),
    ]

    checker = DependencyChecker(EXAMPLE_DEPENDENCIES)
    print(checker.summary())

    if checker.has_missing():
        print("\nSome dependencies are missing or outdated.")
    else:
        print("\n✓ All dependencies satisfied!")


# ============================================================================
# Exports (ensure functions are available even without Qt)
# ============================================================================

# Make sure show_dependency_dialog is always importable
if not HAS_QT:
    def show_dependency_dialog(
        checker: DependencyChecker,
        iface: Any,
        title: str = "Missing Dependencies",
        message: str = "The following dependencies are missing:",
        on_install_complete: Optional[Callable[[bool], None]] = None,
    ) -> bool:
        """
        Stub: Show a Qt dialog for missing dependencies.
        
        Qt is not available, so this just logs the missing dependencies.
        
        :param checker: DependencyChecker instance with results
        :param iface: QGIS interface instance (unused)
        :param title: Dialog title (unused)
        :param message: Message to display (unused)
        :param on_install_complete: Optional callback(success: bool)
        :returns: False (dependencies not satisfied)
        """
        logger.error("Qt not available, cannot show dependency dialog")
        logger.error(checker.summary())
        if on_install_complete:
            on_install_complete(False)
        return False
