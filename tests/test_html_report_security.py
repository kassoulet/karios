import html
import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Mock GDAL and other dependencies
sys.modules['osgeo'] = MagicMock()
sys.modules['osgeo.gdal'] = MagicMock()
sys.modules['osgeo.osr'] = MagicMock()

from karios.report.html_report import HtmlReportGenerator

def test_html_report_escaping(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Malicious inputs
    malicious_prefix = "<script>alert('XSS')</script>"
    malicious_mon = "Monitored <img src=x onerror=alert(1)>"
    malicious_ref = "Reference <b>Bold</b>"
    malicious_dem_desc = "DEM <script>alert(2)</script>"
    # Use a payload that doesn't contain / to avoid Path().name stripping it
    malicious_product = "malicious_script_alert_3.json"
    # Actually, the code does: p_path = Path(p); p_name = p_path.name
    # If p is 'malicious_<script>alert(3)</script>.json', Path(p).name is 'script>alert(3)</script>.json' (on linux if < is seen as part of path?)
    # Wait, on Linux < is a valid filename character.
    # Ah! 'malicious_<script' might be seen as a directory if there is a slash? No slash here.

    malicious_product = "malicious-script-alert-3.json"
    # Let's use something that definitely has HTML chars but no path chars
    malicious_product_name = "product&<>.json"

    # Mock MatchResult
    match_result = MagicMock()
    match_result.monitored_image.file_name = malicious_mon
    match_result.reference_image.file_name = malicious_ref
    match_result.mask = None
    match_result.points = [MagicMock()]

    # Mock AccuracyAnalysis
    accuracy_analysis = MagicMock()
    accuracy_analysis.valid_pixels = 100
    accuracy_analysis.total_pixels = 1000
    accuracy_analysis.mean_x = 0.1
    accuracy_analysis.mean_y = 0.2
    accuracy_analysis.std_x = 0.01
    accuracy_analysis.std_y = 0.02
    accuracy_analysis.ce90 = 0.5
    accuracy_analysis.ce95 = 0.6

    # Mock ReportPaths
    report_paths = MagicMock()
    report_paths.overview_plot = "overview.png"
    report_paths.dx_plot = "dx.png"
    report_paths.dy_plot = "dy.png"
    report_paths.ce_plot = "ce.png"
    report_paths.dem_plots = []
    report_paths.products = [malicious_product_name]

    # Mock RuntimeConfiguration
    runtime_config = MagicMock()
    runtime_config.pixel_size = 1.0
    runtime_config.enable_large_shift_detection = False
    runtime_config.title_prefix = malicious_prefix
    runtime_config.generate_kp_chips = False
    runtime_config.dem_description = malicious_dem_desc
    runtime_config.output_directory = output_dir

    generator = HtmlReportGenerator(
        output_dir=output_dir,
        match_result=match_result,
        accuracy_analysis=accuracy_analysis,
        report_paths=report_paths,
        runtime_config=runtime_config,
        dem_file_path=None
    )

    # Mock _copy_assets to avoid file system issues with missing assets in test env
    generator._copy_assets = MagicMock()

    generator.generate()

    report_html = (output_dir / "report.html").read_text()
    products_html = (output_dir / "products.html").read_text()

    # Verify escaping in report.html
    assert html.escape(malicious_prefix) in report_html
    assert malicious_prefix not in report_html

    assert html.escape(malicious_mon) in report_html
    assert malicious_mon not in report_html

    assert html.escape(malicious_ref) in report_html
    assert malicious_ref not in report_html

    # Verify escaping in products.html
    assert html.escape(malicious_prefix) in products_html
    assert malicious_prefix not in products_html

    assert html.escape(malicious_product_name) in products_html
    assert malicious_product_name not in products_html
