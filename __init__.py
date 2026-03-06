# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KariosQGIS - __init__.py
                              -------------------
        begin                : 2026-02-26
        copyright            : (C) 2026 by KARIOS QGIS Plugin
        license              : Apache-2.0
 ***************************************************************************/
"""

__author__ = 'KARIOS QGIS Plugin'
__date__ = '2026-02-26'
__copyright__ = '(C) 2026 by KARIOS QGIS Plugin'
__license__ = 'Apache-2.0'

# This will get replaced with a git SHA1 value by the git archive command
__revision__ = '$Format:%H$'


def classFactory(iface):
    """Load KariosQGIS class from file KariosQGIS.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .karios_qgis import KariosQGISPlugin
    return KariosQGISPlugin(iface)
