# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KariosQGIS
                                 A QGIS plugin
 Apply KARIOS processing to raster images for geometric accuracy analysis
                              -------------------
        begin                : 2026-02-26
        git sha              : $Format:%H$
        copyright            : (C) 2026 by KARIOS QGIS Plugin
        email                : example@example.com
        license              : Apache-2.0
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the Apache License, Version 2.0.                *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

# Import the processing provider
from processing.provider import KariosProvider

# Import dependency checker
from dependency_checker import (
    DependencyChecker,
    DependencyInfo,
    check_and_install_dependencies,
    BackgroundDependencyChecker,
)

import logging
import os
import sys

# Configure logging for QGIS
logger = logging.getLogger("KARIOS")
logger.setLevel(logging.DEBUG)

# Create handler for QGIS message bar (will be added when iface is available)
_qgis_handler = None


def setup_qgis_logging(iface):
    """Setup logging to QGIS message bar and console."""
    global _qgis_handler
    
    class QgisLogHandler(logging.Handler):
        def __init__(self, iface):
            super().__init__()
            self.iface = iface
            self.setLevel(logging.DEBUG)
            
        def emit(self, record):
            msg = self.format(record)
            if record.levelno >= logging.CRITICAL:
                iface.messageBar().pushCritical("KARIOS", msg)
            elif record.levelno >= logging.ERROR:
                iface.messageBar().pushCritical("KARIOS", msg)
            elif record.levelno >= logging.WARNING:
                iface.messageBar().pushWarning("KARIOS", msg)
            elif record.levelno >= logging.INFO:
                iface.messageBar().pushInfo("KARIOS", msg)
            else:
                iface.messageBar().pushMessage("KARIOS", msg, level=0, duration=3)
    
    try:
        # Remove existing handler if any
        if _qgis_handler:
            logger.removeHandler(_qgis_handler)
        
        _qgis_handler = QgisLogHandler(iface)
        logger.addHandler(_qgis_handler)
        logger.info("KARIOS logging initialized")
    except Exception as e:
        # Fallback to basic logging if iface not ready
        logger.warning(f"Could not setup QGIS logging: {e}")


print("[KARIOS] Loading plugin...")

class KariosQGISPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        logger.info("Initializing KariosQGISPlugin...")
        
        try:
            # Setup logging
            setup_qgis_logging(iface)
            logger.debug("Logging configured")
            
            # Save reference to the QGIS interface.
            self.iface = iface
            logger.debug("QGIS interface stored")

            # initialize plugin directory
            self.plugin_dir = os.path.dirname(__file__)
            logger.debug(f"Plugin directory: {self.plugin_dir}")

            # initialize locale
            locale_value = QSettings().value('locale/userLocale')
            locale = locale_value[0:2] if locale_value else 'en'
            locale_path = os.path.join(
                self.plugin_dir,
                'i18n',
                'KariosQGIS_{}.qm'.format(locale))

            if os.path.exists(locale_path):
                self.translator = QTranslator()
                self.translator.load(locale_path)
                QCoreApplication.installTranslator(self.translator)
                logger.debug(f"Locale loaded: {locale}")
            else:
                logger.debug(f"Locale file not found: {locale_path}")

            # Declare instance attributes
            self.actions = []
            self.menu = self.tr(u'&KARIOS Processing')
            self.plugin_active = False
            logger.debug("Instance attributes initialized")

            # Processing provider instance
            self.provider = None
            logger.debug("Provider reference initialized")

            # Define plugin dependencies
            # Note: QGIS provides numpy - mark as installable=False
            # scipy, scikit-image, pandas and opencv-python need to be installed
            self.dependencies = [
                DependencyInfo(
                    name="OpenCV",
                    import_name="cv2",
                    package="opencv-python-headless",  # Headless for QGIS/server
                    min_version="4.0.0",
                    optional=False,
                    installable=True,  # Can be installed via pip
                ),
                # pandas is NOT provided by QGIS - needs to be installed
                DependencyInfo(
                    name="pandas",
                    import_name="pandas",
                    package="pandas",
                    min_version="1.3.0",
                    optional=False,
                    installable=True,  # Needs pip install
                ),
                # scipy is NOT provided by QGIS - needs to be installed
                DependencyInfo(
                    name="SciPy",
                    import_name="scipy",
                    min_version="1.7.0",
                    optional=False,
                    installable=True,  # Needs pip install
                ),
                # scikit-image is NOT provided by QGIS - needs to be installed
                DependencyInfo(
                    name="scikit-image",
                    import_name="skimage",
                    package="scikit-image",
                    min_version="0.19.0",
                    optional=False,
                    installable=True,  # Needs pip install
                ),
                # NumPy is provided by QGIS, just check it's available
                DependencyInfo(
                    name="NumPy",
                    import_name="numpy",
                    min_version="1.20.0",
                    optional=False,
                    installable=False,  # Provided by QGIS, don't install
                ),
            ]
            logger.debug(f"Dependencies defined: {len(self.dependencies)} packages")
            
            logger.info("KariosQGISPlugin constructor completed")
        except Exception as e:
            logger.error(f"Error in __init__: {e}", exc_info=True)
            raise

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate('KariosQGIS', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        logger.info("initGui() called")

        try:
            # Check/install dependencies using dependency_checker module
            self._check_dependencies_with_dialog()

        except Exception as e:
            logger.error(f"Error in initGui: {e}", exc_info=True)
            self.iface.messageBar().pushCritical(
                "KARIOS",
                f"Plugin initialization failed: {e}"
            )
            raise

    def _check_dependencies_with_dialog(self):
        """Use dependency_checker module to check/install dependencies with dialog."""
        logger.info("Starting dependency check with progress dialog...")

        def on_complete(success):
            """Callback when dependency check/installation completes."""
            logger.info(f"Dependency check finished: success={success}")
            if success:
                self.iface.messageBar().pushSuccess(
                    "KARIOS",
                    "Dependencies checked and ready!",
                )
                logger.info("All dependencies satisfied - continuing initialization")
            else:
                self.iface.messageBar().pushWarning(
                    "KARIOS",
                    "Some dependencies could not be installed. Plugin may not work correctly.",
                )
                logger.warning("Dependency check/installation failed")

            # Continue with plugin initialization
            self._finish_initialization()

        # Use BackgroundDependencyChecker from dependency_checker module
        self.dep_checker = BackgroundDependencyChecker(
            iface=self.iface,
            plugin_dir=self.plugin_dir,
            dependencies=self.dependencies,
            on_complete=on_complete,
        )
        self.dep_checker.start()

    def _finish_initialization(self):
        """Complete plugin initialization (provider registration)."""
        logger.info("Finishing initialization...")
        
        try:
            # Initialize and register the processing provider
            logger.info("Initializing processing provider...")
            self.provider = KariosProvider()
            logger.debug("KariosProvider instance created")
            
            self.provider.loadAlgorithms()
            logger.debug("Algorithms loaded")

            from qgis.core import QgsApplication
            QgsApplication.processingRegistry().addProvider(self.provider)
            logger.info("Provider registered with QgsApplication")
            
            logger.info("initGui() completed successfully")
        except Exception as e:
            logger.error(f"Error in _finish_initialization: {e}", exc_info=True)
            self.iface.messageBar().pushCritical(
                "KARIOS",
                f"Provider initialization failed: {e}"
            )
            raise

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        logger.info("unload() called")
        
        try:
            # Unregister the processing provider
            from qgis.core import QgsApplication
            if self.provider:
                QgsApplication.processingRegistry().removeProvider(self.provider)
                logger.info("Provider unregistered")
                self.provider = None
            
            # Remove logging handler
            global _qgis_handler
            if _qgis_handler:
                logger.removeHandler(_qgis_handler)
                _qgis_handler = None
                logger.debug("Logging handler removed")
            
            logger.info("unload() completed successfully")
        except Exception as e:
            logger.error(f"Error in unload: {e}", exc_info=True)
            raise
