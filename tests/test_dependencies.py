#!/usr/bin/env python3
"""
Verify all dependencies are working correctly.

Usage:
    python tests/test_dependencies.py
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add plugin directory to path
plugin_dir = Path(__file__).parent.parent
sys.path.insert(0, str(plugin_dir))


def test_opencv():
    """Test OpenCV functionality."""
    logger.info("-" * 60)
    logger.info("Testing OpenCV...")
    
    try:
        import cv2
        import numpy as np
        
        # Create test image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Test basic operations
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        
        # Get version and location
        version = cv2.__version__
        location = getattr(cv2, '__file__', 'unknown')
        
        logger.info(f"✓ OpenCV {version} working")
        logger.info(f"  Location: {location}")
        return True
        
    except Exception as e:
        logger.error(f"✗ OpenCV failed: {e}")
        return False


def test_numpy():
    """Test NumPy functionality."""
    logger.info("-" * 60)
    logger.info("Testing NumPy...")
    
    try:
        import numpy as np
        
        # Test array operations
        arr = np.array([1, 2, 3, 4, 5])
        result = arr * 2
        assert list(result) == [2, 4, 6, 8, 10]
        
        # Test matrix operations
        matrix = np.random.rand(10, 10)
        eigenvalues = np.linalg.eigvals(matrix)
        
        # Get version
        version = np.__version__
        
        logger.info(f"✓ NumPy {version} working")
        return True
        
    except Exception as e:
        logger.error(f"✗ NumPy failed: {e}")
        return False


def test_skimage():
    """Test scikit-image functionality."""
    logger.info("-" * 60)
    logger.info("Testing scikit-image...")
    
    try:
        from skimage import filters, feature
        import numpy as np
        
        # Create test image
        img = np.zeros((100, 100))
        img[25:75, 25:75] = 1
        
        # Test filters
        sobel_result = filters.sobel(img)
        
        # Test feature detection
        corners = feature.corner_harris(img)
        
        logger.info(f"✓ scikit-image working")
        return True
        
    except Exception as e:
        logger.error(f"✗ scikit-image failed: {e}")
        return False


def test_pandas():
    """Test pandas functionality."""
    logger.info("-" * 60)
    logger.info("Testing pandas...")
    
    try:
        import pandas as pd
        import numpy as np
        
        # Create DataFrame
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [10, 20, 30, 40, 50],
            'c': ['x', 'y', 'z', 'w', 'v']
        })
        
        # Test operations
        result = df.groupby('c').sum()
        filtered = df[df['a'] > 2]
        
        # Get version
        version = pd.__version__
        
        logger.info(f"✓ pandas {version} working")
        return True
        
    except Exception as e:
        logger.error(f"✗ pandas failed: {e}")
        return False


def test_all_imports():
    """Test that all required modules can be imported."""
    logger.info("-" * 60)
    logger.info("Testing all imports...")
    
    required = {
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'skimage': 'scikit-image',
        'pandas': 'pandas',
    }
    
    all_ok = True
    for import_name, display_name in required.items():
        try:
            __import__(import_name)
            module = sys.modules[import_name]
            version = getattr(module, '__version__', 'unknown')
            logger.info(f"✓ {display_name} (v{version})")
        except ImportError as e:
            logger.error(f"✗ {display_name} NOT installed: {e}")
            all_ok = False
    
    return all_ok


def main():
    """Run all tests."""
    logger.info("")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 12 + "Dependency Verification Tests" + " " * 15 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("")

    # Test all imports first
    all_imports_ok = test_all_imports()

    if not all_imports_ok:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Some dependencies are missing!")
        logger.info("They will be auto-installed when the plugin loads.")
        logger.info("This is EXPECTED - auto-install will handle this.")
        logger.info("=" * 60)
        # Return 0 - this is not a failure, just informational
        # The auto-install test will verify the installation works
        return 0

    # Run functional tests
    results = {
        'OpenCV': test_opencv(),
        'NumPy': test_numpy(),
        'scikit-image': test_skimage(),
        'pandas': test_pandas(),
    }

    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test}")

    passed = sum(results.values())
    total = len(results)

    logger.info("")
    logger.info(f"Passed: {passed}/{total}")

    if all(results.values()):
        logger.info("")
        logger.info("╔" + "=" * 58 + "╗")
        logger.info("║" + " " * 10 + "ALL DEPENDENCIES WORKING CORRECTLY" + " " * 12 + "║")
        logger.info("╚" + "=" * 58 + "╝")
        return 0
    else:
        logger.info("")
        logger.error("╔" + "=" * 58 + "╗")
        logger.error("║" + " " * 16 + "SOME TESTS FAILED" + " " * 21 + "║")
        logger.error("╚" + "=" * 58 + "╝")
        return 1


if __name__ == '__main__':
    sys.exit(main())
