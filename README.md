# KARIOS QGIS Plugin

A QGIS plugin that integrates [KARIOS](https://github.com/telespazio-tim/karios) (KLT-based Algorithm for Registration of Images from Observing Systems) for geometric accuracy analysis of raster images.

## Features

- **Image Matching**: Uses KLT (Kanade-Lucas-Tomasi) algorithm for feature point detection and matching
- **Geometric Accuracy Analysis**: Provides statistical metrics including:
  - RMSE (Root Mean Square Error)
  - CE90 (Circular Error @ 90 percentile)
  - Mean, Min, Max errors
  - Standard deviation
- **Displacement Analysis**: Analyzes shifts in both line (along-track) and pixel (across-track) directions
- **DEM-based Analysis**: Optional altitude-dependent error analysis
- **Mask Support**: Exclude invalid pixels (clouds, water, etc.)
- **Visual Outputs**: Generates overview plots, displacement maps, and CE90 visualizations

## Requirements

- QGIS 3.28 or later
- Python 3.8 or later
- KARIOS library (included as git submodule)

## Installation

### Option 1: Using the Install Script

```bash
# Clone the repository
git clone --recursive https://github.com/your-org/karios-qgis.git
cd karios-qgis

# Run the installation script
python install_plugin.py
```

### Option 2: Manual Installation

1. **Clone the repository with submodules**:
   ```bash
   git clone --recursive https://github.com/your-org/karios-qgis.git
   cd karios-qgis
   ```

2. **Initialize submodule if not already done**:
   ```bash
   git submodule update --init --recursive
   ```

3. **Compile Qt resources**:
   ```bash
   # For PyQt5
   pyrcc5 -o resources/resources.py resources/resources.qrc
   
   # Or for PyQt6
   pyrcc6 -o resources/resources.py resources/resources.qrc
   ```

4. **Copy to QGIS plugins directory**:
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Windows**: `%APPDATA%/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

5. **Enable the plugin in QGIS**:
   - Open QGIS
   - Go to Plugins > Manage and Install Plugins
   - Find "KARIOS Processing" in the Installed tab
   - Check the box to enable it

### Installing KARIOS Dependencies

The plugin includes KARIOS as a submodule, but you need to install its Python dependencies:

```bash
cd karios
pip install -e .
```

Or using conda (recommended):

```bash
cd karios
conda env create -f environment.yml
conda activate karios
pip install -e .
```

## Usage

1. **Open Processing Toolbox** in QGIS (Processing > Toolbox)

2. **Navigate to**: KARIOS > KARIOS Processing

3. **Configure the algorithm**:

   **Required Inputs**:
   - **Monitored Image**: The raster image to analyze for geometric deformations
   - **Reference Image**: The stable reference raster image for comparison

   **Optional Inputs**:
   - **Mask File**: Raster file to exclude pixels from matching (0=excluded, 1=valid)
   - **DEM File**: Digital Elevation Model for altitude-based analysis
   - **Configuration File**: Custom KARIOS configuration JSON file

   **Parameters**:
   - **Pixel Size**: Ground resolution in meters (default: 10.0)
   - **Title Prefix**: Prefix for plot titles (max 26 chars)
   - **DEM Description**: Description of DEM source for plots
   - **Generate Key Points Mask**: Output key points mask GeoTIFF
   - **Generate Displacement Raster**: Output dx/dy displacement rasters
   - **Generate Key Points Chips**: Output 57×57 pixel chip images
   - **Enable Large Shift Detection**: Enable experimental large shift correction

   **Outputs**:
   - **Output Folder**: Directory for all output files
   - **CSV File**: Key points with displacement vectors
   - **GeoJSON File**: Geographic features with displacement data
   - **Statistics Folder**: Contains all generated files and plots

4. **Run the algorithm**

## Output Files

The plugin generates the following outputs:

- **CSV File**: `KLT_matcher_{monitored}_{reference}.csv`
  - Columns: x0, y0, dx, dy, score, radial_error, angle, zncc_score
  
- **GeoJSON File**: `kp_delta.json`
  - Geographic features with displacement vectors and CRS information

- **Statistical Summary**: `correl_res.txt`
  - Accuracy metrics summary

- **Visualization Plots**:
  - `01_overview.png`: Error distribution overview
  - `02_dx.png`: Along-track displacement analysis
  - `03_dy.png`: Across-track displacement analysis
  - `04_ce.png`: Circular error visualization
  - DEM analysis plots (if DEM provided)

- **Optional Products**:
  - `kp_mask.tif`: Key points mask
  - `kp_delta.tif`: Displacement raster
  - `chips/`: 57×57 pixel image patches centered on key points

## Configuration

KARIOS uses a JSON configuration file for processing parameters. You can use the default configuration or provide a custom one. The configuration file controls:

- KLT matching parameters (corner detection, window sizes, quality thresholds)
- Accuracy analysis settings
- Plot configurations (figure sizes, color maps)
- Large shift detection thresholds

See the [KARIOS documentation](https://github.com/telespazio-tim/karios) for detailed configuration options.

## Development

### Project Structure

```
karios-qgis/
├── __init__.py              # Plugin initialization
├── karios_qgis.py           # Main plugin class
├── metadata.txt             # Plugin metadata
├── install_plugin.py        # Installation script
├── processing/
│   ├── __init__.py
│   └── karios_algorithm.py  # Processing algorithm
├── resources/
│   ├── __init__.py
│   ├── resources.qrc        # Qt resources definition
│   ├── resources.py         # Compiled resources (generated)
│   └── icon.png             # Plugin icon
└── karios/                  # KARIOS submodule
```

### Building the Plugin

```bash
# Compile resources
pyrcc6 -o resources/resources.py resources/resources.qrc

# Install to QGIS
python install_plugin.py
```

### Debugging

Enable debug output in QGIS:
1. Go to Settings > Options > System
2. Enable "Show debug messages in log panel"
3. Check the Log Messages Panel for plugin output

## Troubleshooting

### KARIOS Import Error

If you get import errors, ensure the karios submodule is initialized and installed:

```bash
git submodule update --init --recursive
cd karios
pip install -e .
```

### Missing libGL (Linux)

Install the required OpenGL library:

```bash
# Ubuntu/Debian
sudo apt-get install libgl1-mesa-glx

# Fedora/RHEL
sudo dnf install mesa-libGL
```

### Plugin Not Appearing in QGIS

1. Check that the plugin is in the correct directory
2. Verify `__init__.py` and `metadata.txt` are present
3. Restart QGIS
4. Check Plugins > Manage and Install Plugins > Installed

## License

This plugin is licensed under the Apache License, Version 2.0.

KARIOS is licensed under the Apache License, Version 2.0. See [KARIOS LICENSE](https://github.com/telespazio-tim/karios/blob/main/LICENSE).

## References

- **KARIOS Repository**: https://github.com/telespazio-tim/karios
- **KARIOS Documentation**: https://github.com/telespazio-tim/karios/tree/main/docs
- **QGIS Processing Framework**: https://docs.qgis.org/latest/en/docs/user_manual/processing/index.html

## Citation

If you use this plugin in your research, please cite KARIOS:

```bibtex
@software{karios2024,
  author = {{KARIOS Development Team}},
  title = {KARIOS: KLT-based Algorithm for Registration of Images from Observing Systems},
  url = {https://github.com/telespazio-tim/karios},
  doi = {10.5281/zenodo.10598329},
  year = {2024}
}
```

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Support

For KARIOS-specific issues, please refer to the [KARIOS issue tracker](https://github.com/telespazio-tim/karios/issues).

For plugin-specific issues, please open an issue in this repository.
