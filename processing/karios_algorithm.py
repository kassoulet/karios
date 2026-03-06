# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KariosQGIS - Processing Algorithm
                                 A QGIS plugin
 Apply KARIOS processing to raster images
                              -------------------
        begin                : 2026-02-26
        copyright            : (C) 2026 by KARIOS QGIS Plugin
        license              : Apache-2.0
 ***************************************************************************/
"""

import os
import sys
import tempfile
import json
from pathlib import Path

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterString,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingOutputFile,
    QgsProcessingOutputString,
    QgsProcessingContext,
    QgsProcessingFeedback,
)
from qgis.PyQt.QtCore import QCoreApplication


class KariosAlgorithm(QgsProcessingAlgorithm):
    """
    KARIOS Processing Algorithm for geometric accuracy analysis.
    
    This algorithm applies the KARIOS (KLT-based Algorithm for Registration 
    of Images from Observing Systems) processing to analyze geometric 
    deformations between two raster images.
    """

    # Constants
    INPUT_MONITORED = 'INPUT_MONITORED'
    INPUT_REFERENCE = 'INPUT_REFERENCE'
    INPUT_MASK = 'INPUT_MASK'
    INPUT_DEM = 'INPUT_DEM'
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'
    PIXEL_SIZE = 'PIXEL_SIZE'
    TITLE_PREFIX = 'TITLE_PREFIX'
    GENERATE_KP_MASK = 'GENERATE_KP_MASK'
    GENERATE_DELTA_RASTER = 'GENERATE_DELTA_RASTER'
    GENERATE_KP_CHIPS = 'GENERATE_KP_CHIPS'
    DEM_DESCRIPTION = 'DEM_DESCRIPTION'
    ENABLE_LARGE_SHIFT = 'ENABLE_LARGE_SHIFT'
    CONFIG_FILE = 'CONFIG_FILE'
    OUTPUT_CSV = 'OUTPUT_CSV'
    OUTPUT_GEOJSON = 'OUTPUT_GEOJSON'
    OUTPUT_STATS = 'OUTPUT_STATS'

    def __init__(self):
        super().__init__()
        self.karios_api = None

    def tr(self, text):
        """Translate text."""
        return QCoreApplication.translate('KariosQGIS', text)

    def createInstance(self):
        """Create a new instance of the algorithm."""
        return KariosAlgorithm()

    def icon(self):
        """Return the algorithm icon."""
        from qgis.PyQt.QtGui import QIcon
        return QIcon(':/icons/tpz.png')

    def name(self):
        """Return the algorithm name."""
        return 'karios_processing'

    def displayName(self):
        """Return the algorithm display name."""
        return self.tr('KARIOS Processing')

    def group(self):
        """Return the group name."""
        return self.tr('KARIOS')

    def groupId(self):
        """Return the group ID."""
        return 'karios'

    def shortHelpString(self):
        """Return the short help string."""
        return self.tr(
            '<h2>KARIOS Processing - Geometric Accuracy Analysis</h2>'
            '<p>This tool applies the KARIOS algorithm to analyze geometric '
            'deformations between two raster images using the KLT (Kanade-Lucas-Tomasi) '
            'feature matching algorithm.</p>'
            '<h3>Inputs:</h3>'
            '<ul>'
            '<li><b>Monitored Image:</b> The image to analyze for shifts/changes</li>'
            '<li><b>Reference Image:</b> The stable reference image for comparison</li>'
            '<li><b>Mask File (optional):</b> Exclude pixels from matching (0=excluded, 1=valid)</li>'
            '<li><b>DEM File (optional):</b> Enable altitude-based analysis</li>'
            '</ul>'
            '<h3>Outputs:</h3>'
            '<ul>'
            '<li>CSV file with key points and displacement vectors</li>'
            '<li>GeoJSON file with geographic features</li>'
            '<li>Statistical summary file</li>'
            '<li>Visualization plots (overview, dx, dy, CE90)</li>'
            '</ul>'
        )

    def initAlgorithm(self, config=None):
        """Initialize the algorithm parameters."""

        # Required inputs - raster layers from QGIS
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_MONITORED,
                self.tr('Monitored Image')
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_REFERENCE,
                self.tr('Reference Image')
            )
        )

        # Output folder
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                self.tr('Output Folder'),
                defaultValue='',
                optional=True
            )
        )

        # Optional inputs - files (can be layers or external files)
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_MASK,
                self.tr('Mask File (optional)'),
                QgsProcessingParameterFile.File,
                optional=True,
                fileFilter='Raster files (*.tif *.tiff *.img)'
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_DEM,
                self.tr('DEM File (optional)'),
                QgsProcessingParameterFile.File,
                optional=True,
                fileFilter='Raster files (*.tif *.tiff *.img)'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFile(
                self.CONFIG_FILE,
                self.tr('Configuration File (optional)'),
                QgsProcessingParameterFile.File,
                optional=True,
                fileFilter='JSON files (*.json)'
            )
        )
                
        # Processing parameters
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PIXEL_SIZE,
                self.tr('Pixel Size (meters)'),
                QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                optional=True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterString(
                self.TITLE_PREFIX,
                self.tr('Title Prefix for Plots'),
                defaultValue='',
                optional=True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterString(
                self.DEM_DESCRIPTION,
                self.tr('DEM Description'),
                defaultValue='',
                optional=True
            )
        )
        
        # Boolean flags
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.GENERATE_KP_MASK,
                self.tr('Generate Key Points Mask'),
                defaultValue=False
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.GENERATE_DELTA_RASTER,
                self.tr('Generate Displacement Raster'),
                defaultValue=True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.GENERATE_KP_CHIPS,
                self.tr('Generate Key Points Chips'),
                defaultValue=False
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ENABLE_LARGE_SHIFT,
                self.tr('Enable Large Shift Detection (experimental)'),
                defaultValue=False
            )
        )
        
        # Outputs
        self.addOutput(
            QgsProcessingOutputFile(
                self.OUTPUT_CSV,
                self.tr('Output CSV File')
            )
        )

        self.addOutput(
            QgsProcessingOutputFile(
                self.OUTPUT_GEOJSON,
                self.tr('Output GeoJSON File')
            )
        )

        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT_STATS,
                self.tr('Output Statistics Folder')
            )
        )

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        """
        Process the algorithm using KARIOS.
        
        :param parameters: Algorithm parameters
        :param context: Processing context
        :param feedback: Processing feedback
        :return: Dictionary of output results
        """
        
        # Import karios - handle the submodule path
        plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        karios_path = os.path.join(plugin_dir, 'karios')
        
        if os.path.exists(karios_path):
            sys.path.insert(0, karios_path)
        
        try:
            from karios.api import KariosAPI, RuntimeConfiguration
            from karios.core.configuration import ProcessingConfiguration
        except ImportError as e:
            feedback.pushInfo(f'Failed to import KARIOS. Ensure the karios submodule is initialized: {str(e)}')
            raise Exception(f'KARIOS import failed: {str(e)}')
        
        # Get input parameters - raster layers
        monitored_layer = self.parameterAsRasterLayer(parameters, self.INPUT_MONITORED, context)
        reference_layer = self.parameterAsRasterLayer(parameters, self.INPUT_REFERENCE, context)
        
        # Get file paths from layers
        monitored_path = monitored_layer.source() if monitored_layer else None
        reference_path = reference_layer.source() if reference_layer else None
        
        # Handle multi-band rasters - get the actual file path
        if monitored_path and '|' in monitored_path:
            monitored_path = monitored_path.split('|')[0]
        if reference_path and '|' in reference_path:
            reference_path = reference_path.split('|')[0]
        
        # Optional file inputs
        mask_path = self.parameterAsFile(parameters, self.INPUT_MASK, context)
        dem_path = self.parameterAsFile(parameters, self.INPUT_DEM, context)
        config_path = self.parameterAsFile(parameters, self.CONFIG_FILE, context)
        output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)

        # Validate required inputs
        if not monitored_layer or not reference_layer:
            raise Exception('Both monitored and reference raster layers are required')

        # Set up output directory
        if output_folder and output_folder.strip():
            output_dir = output_folder.strip()
        else:
            output_dir = os.path.join(tempfile.gettempdir(), 'karios_processing')
            os.makedirs(output_dir, exist_ok=True)
        
        # Get processing parameters
        pixel_size = self.parameterAsDouble(parameters, self.PIXEL_SIZE, context)
        title_prefix = self.parameterAsString(parameters, self.TITLE_PREFIX, context)
        dem_description = self.parameterAsString(parameters, self.DEM_DESCRIPTION, context)
        generate_kp_mask = self.parameterAsBool(parameters, self.GENERATE_KP_MASK, context)
        generate_delta_raster = self.parameterAsBool(parameters, self.GENERATE_DELTA_RASTER, context)
        generate_kp_chips = self.parameterAsBool(parameters, self.GENERATE_KP_CHIPS, context)
        enable_large_shift = self.parameterAsBool(parameters, self.ENABLE_LARGE_SHIFT, context)
        
        # Load processing configuration
        if config_path and os.path.exists(config_path):
            feedback.pushInfo(f'Loading configuration from: {config_path}')
            processing_config = ProcessingConfiguration.from_file(config_path)
        else:
            # Use default configuration from karios package
            feedback.pushInfo('Using default KARIOS configuration')
            import karios
            karios_config_path = os.path.join(
                os.path.dirname(karios.__file__),
                'configuration',
                'processing_configuration.json'
            )
            if os.path.exists(karios_config_path):
                processing_config = ProcessingConfiguration.from_file(karios_config_path)
            else:
                processing_config = ProcessingConfiguration()
        
        # Create runtime configuration
        runtime_config = RuntimeConfiguration(
            output_directory=Path(output_dir),
            gen_kp_mask=generate_kp_mask,
            gen_delta_raster=generate_delta_raster,
            generate_kp_chips=generate_kp_chips,
            pixel_size=pixel_size if pixel_size > 0 else None,
            enable_large_shift_detection=enable_large_shift,
            title_prefix=title_prefix if title_prefix else None,
            dem_description=dem_description if dem_description else None,
        )
        
        # Initialize KARIOS API
        feedback.pushInfo('Initializing KARIOS API...')
        api = KariosAPI(processing_config, runtime_config)
        
        # Process images
        feedback.pushInfo('Starting KARIOS processing...')
        feedback.pushInfo(f'Monitored image: {monitored_path}')
        feedback.pushInfo(f'Reference image: {reference_path}')
        
        if mask_path:
            feedback.pushInfo(f'Mask file: {mask_path}')
        if dem_path:
            feedback.pushInfo(f'DEM file: {dem_path}')
        
        try:
            match_result, accuracy, reports = api.process(
                monitored_image_path=monitored_path,
                reference_image_path=reference_path,
                mask_file_path=mask_path if mask_path else None,
                dem_file_path=dem_path if dem_path else None,
            )
        except Exception as e:
            feedback.reportError(f'KARIOS processing failed: {str(e)}')
            raise

        # Report results
        feedback.pushInfo('=' * 50)
        feedback.pushInfo('KARIOS Processing Complete')
        feedback.pushInfo('=' * 50)
        feedback.pushInfo(f'CE90: {accuracy.ce90:.3f} pixels')
        feedback.pushInfo(f'RMSE: {accuracy.rmse:.3f} pixels')
        feedback.pushInfo(f'Mean Error X: {accuracy.mean_x:.3f} pixels')
        feedback.pushInfo(f'Mean Error Y: {accuracy.mean_y:.3f} pixels')
        feedback.pushInfo(f'Min Error: {accuracy.min_error:.3f} pixels')
        feedback.pushInfo(f'Max Error: {accuracy.max_error:.3f} pixels')
        feedback.pushInfo(f'Std Dev: {accuracy.std_dev:.3f} pixels')
        feedback.pushInfo(f'Number of Key Points: {accuracy.num_points}')
        feedback.pushInfo('=' * 50)
        
        # Prepare outputs
        csv_file = reports.key_points_csv if hasattr(reports, 'key_points_csv') else ''
        geojson_file = reports.key_points_geojson if hasattr(reports, 'key_points_geojson') else ''
        
        return {
            self.OUTPUT_CSV: csv_file,
            self.OUTPUT_GEOJSON: geojson_file,
            self.OUTPUT_STATS: output_dir,
        }
