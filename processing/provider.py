# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KariosQGIS - Processing Provider
                                 A QGIS plugin
 Apply KARIOS processing to raster images
                              -------------------
        begin                : 2026-02-26
        copyright            : (C) 2026 by KARIOS QGIS Plugin
        license              : Apache-2.0
 ***************************************************************************/
"""

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from .karios_algorithm import KariosAlgorithm


class KariosProvider(QgsProcessingProvider):
    """
    KARIOS Processing Provider.
    
    Provides the KARIOS processing algorithms to the QGIS Processing Framework.
    """

    def __init__(self):
        super().__init__()
        self.algs = []

    def id(self):
        """
        Returns the unique provider ID.
        """
        return 'karios'

    def name(self):
        """
        Returns the provider name.
        """
        return self.tr('KARIOS')

    def longName(self):
        """
        Returns the provider long name.
        """
        return self.tr('KARIOS Processing')

    def tr(self, text):
        """
        Translate text.
        """
        return QCoreApplication.translate('KariosQGIS', text)

    def icon(self):
        """
        Returns the provider icon.
        """
        return QIcon(':/icons/tpz.png')

    def loadAlgorithms(self):
        """
        Loads all algorithms provided by this provider.
        """
        # Add the KARIOS processing algorithm
        self.algs = [KariosAlgorithm()]
        
        for alg in self.algs:
            self.addAlgorithm(alg)
