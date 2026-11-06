#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install script for KARIOS QGIS Plugin

This script sets up the plugin by:
1. Initializing the karios git submodule
2. Compiling the Qt resources
3. Creating necessary directories

Usage:
    python install_plugin.py [--qgis-plugin-dir PATH]

If --qgis-plugin-dir is not specified, the script will:
- On Linux: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
- On Windows: %APPDATA%/QGIS/QGIS3/profiles/default/python/plugins/
- On macOS: ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path


def get_default_qgis_plugin_dir():
    """Get the default QGIS plugins directory for the current OS."""
    system = platform.system()
    
    if system == 'Windows':
        return os.path.join(os.getenv('APPDATA'), 'QGIS', 'QGIS3', 'profiles', 'default', 'python', 'plugins')
    elif system == 'Darwin':  # macOS
        return os.path.expanduser('~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins')
    else:  # Linux
        return os.path.expanduser('~/.local/share/QGIS/QGIS3/profiles/default/python/plugins')


def compile_resources(plugin_dir):
    """Compile Qt resources to generate resources.py."""
    resources_qrc = os.path.join(plugin_dir, 'resources', 'resources.qrc')
    resources_py = os.path.join(plugin_dir, 'resources', 'resources.py')
    
    # Try pyrcc6 first (PyQt6), then pyrcc5 (PyQt5)
    for rcc_cmd in ['pyrcc6', 'pyrcc5']:
        try:
            subprocess.run([rcc_cmd, '-o', resources_py, resources_qrc], check=True)
            print(f"✓ Successfully compiled resources using {rcc_cmd}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print("✗ Warning: Could not compile resources. Neither pyrcc6 nor pyrcc5 found.")
    print("  You may need to install PyQt5 or PyQt6 development tools.")
    print("  The plugin may still work but icons might not display correctly.")
    return False


def init_submodule(plugin_dir):
    """Initialize and update the karios git submodule."""
    print("Initializing karios git submodule...")
    try:
        subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'], 
                      cwd=plugin_dir, check=True)
        print("✓ Karios submodule initialized")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error initializing submodule: {e}")
        print("  You can initialize it manually with: git submodule update --init --recursive")
        return False


def install_plugin(plugin_dir, target_dir):
    """Install the plugin to the QGIS plugins directory."""
    plugin_name = 'karios-qgis'
    target_path = os.path.join(target_dir, plugin_name)

    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)

    # Remove any existing installation so that files deleted from the source
    # (stale modules, old dependencies/ and site-packages/ folders) do not
    # linger in the target and get imported instead of the current ones.
    if os.path.islink(target_path):
        print(f"Removing existing symlink at {target_path}...")
        os.unlink(target_path)
    elif os.path.isdir(target_path):
        print(f"Removing existing installation at {target_path}...")
        shutil.rmtree(target_path)
    elif os.path.exists(target_path):
        print(f"✗ Error: {target_path} exists but is not a directory.")
        return None
    
    # Copy plugin files (excluding .git directories and build artifacts)
    print(f"Installing plugin to {target_path}...")
    
    ignore_patterns = shutil.ignore_patterns(
        '.git', '.gitignore', '.gitmodules',
        '__pycache__', '*.pyc', '*.pyo',
        '.qwen', '*.md', 'install_plugin.py'
    )
    
    shutil.copytree(plugin_dir, target_path, ignore=ignore_patterns)
    print("✓ Plugin installed successfully")
    
    return target_path


def main():
    """Main installation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Install KARIOS QGIS Plugin')
    parser.add_argument('--qgis-plugin-dir', 
                       help='QGIS plugins directory (default: auto-detect)')
    parser.add_argument('--skip-submodule', 
                       action='store_true',
                       help='Skip git submodule initialization')
    parser.add_argument('--skip-resources', 
                       action='store_true',
                       help='Skip Qt resources compilation')
    
    args = parser.parse_args()
    
    # Get plugin directory (parent directory of this script)
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 60)
    print("KARIOS QGIS Plugin Installation")
    print("=" * 60)
    print(f"Plugin directory: {plugin_dir}")
    
    # Initialize submodule
    if not args.skip_submodule:
        init_submodule(plugin_dir)
    else:
        print("Skipping submodule initialization (--skip-submodule)")
    
    # Compile resources
    if not args.skip_resources:
        compile_resources(plugin_dir)
    else:
        print("Skipping resources compilation (--skip-resources)")
    
    # Install to QGIS plugins directory
    target_dir = args.qgis_plugin_dir or get_default_qgis_plugin_dir()
    print(f"Target QGIS plugins directory: {target_dir}")
    
    if install_plugin(plugin_dir, target_dir) is None:
        return 1
    
    print("=" * 60)
    print("Installation complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Open QGIS")
    print("2. Go to Plugins > Manage and Install Plugins")
    print("3. Find 'KARIOS Processing' in the Installed tab")
    print("4. Enable the plugin if not already enabled")
    print("5. Access via Processing Toolbox > KARIOS > KARIOS Processing")
    print("\nNote: a plugin installed from source does not get its dependencies automatically")
    print("(that only works with the released zip, see bundle-requirements.txt). Install them")
    print("in the Python of QGIS: pip install -r bundle-requirements.txt scipy")

    return 0


if __name__ == '__main__':
    sys.exit(main())
