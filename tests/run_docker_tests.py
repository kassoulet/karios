#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for KARIOS QGIS Plugin using Docker.

This script builds a QGIS Docker container with the plugin installed
and runs the test suite to verify the dependency checker functionality.

Usage:
    python run_docker_tests.py [--build] [--install-deps] [--verbose] [--cleanup]

Arguments:
    --build         Force rebuild of Docker image (default: use cached)
    --install-deps  Install missing dependencies in container
    --verbose       Show detailed output
    --cleanup       Remove container and image after tests

Examples:
    # Run tests with cached image
    python run_docker_tests.py

    # Rebuild image and run tests
    python run_docker_tests.py --build

    # Run tests and install missing dependencies
    python run_docker_tests.py --install-deps

    # Run tests and cleanup afterwards
    python run_docker_tests.py --cleanup
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DOCKER_DIR = SCRIPT_DIR / "docker"
DOCKERFILE = DOCKER_DIR / "Dockerfile"
TEST_SCRIPT = DOCKER_DIR / "test_plugin.py"

IMAGE_NAME = "karios-qgis-test"
CONTAINER_NAME = "karios-qgis-test-container"
QGIS_VERSION = "release-3_34"


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def check_docker():
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"✓ Docker found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Docker not found or not running")
        print("  Please install Docker Desktop or Docker Engine:")
        print("  https://docs.docker.com/get-docker/")
        return False


def check_git_submodules():
    """Check if git submodules are initialized."""
    karios_dir = PROJECT_ROOT / "karios"
    if not karios_dir.exists() or not (karios_dir / "setup.py").exists():
        print("⚠ KARIOS submodule not initialized")
        print("  Run: git submodule update --init --recursive")
        return False
    print("✓ KARIOS submodule found")
    return True


def build_image(force=False):
    """Build the Docker image."""
    print_section("Building Docker Image")

    cmd = ["docker", "build"]
    if force:
        cmd.append("--no-cache")
    cmd.extend([
        "-t", IMAGE_NAME,
        "-f", str(DOCKERFILE),
        str(PROJECT_ROOT),
    ])

    print(f"Building image: {' '.join(cmd)}")
    print(f"  Context: {PROJECT_ROOT}")
    print(f"  Dockerfile: {DOCKERFILE}")

    try:
        result = subprocess.run(cmd, check=True)
        print(f"✓ Image built successfully: {IMAGE_NAME}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to build image: {e}")
        return False


def run_tests(install_deps=False, verbose=False):
    """Run tests in Docker container."""
    print_section("Running Tests")

    cmd = ["docker", "run", "--rm"]
    cmd.extend(["--name", CONTAINER_NAME])

    # Add test arguments
    test_args = []
    if install_deps:
        test_args.append("--install-deps")
    if verbose:
        test_args.append("--verbose")

    cmd.extend([IMAGE_NAME, "python3", "/workspace/test_plugin.py"] + test_args)

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n✗ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"✗ Failed to run tests: {e}")
        return False


def cleanup():
    """Remove Docker container and image."""
    print_section("Cleanup")

    # Stop and remove container if running
    try:
        subprocess.run(
            ["docker", "rm", "-f", CONTAINER_NAME],
            capture_output=True,
            check=False,
        )
        print(f"✓ Container removed: {CONTAINER_NAME}")
    except Exception as e:
        print(f"⚠ Failed to remove container: {e}")

    # Remove image
    try:
        subprocess.run(
            ["docker", "rmi", IMAGE_NAME],
            capture_output=True,
            check=False,
        )
        print(f"✓ Image removed: {IMAGE_NAME}")
    except Exception as e:
        print(f"⚠ Failed to remove image: {e}")


def pull_qgis_image():
    """Pull the base QGIS image."""
    print_section("Pulling QGIS Base Image")

    base_image = f"qgis/qgis:{QGIS_VERSION}"
    cmd = ["docker", "pull", base_image]

    print(f"Pulling: {base_image}")

    try:
        subprocess.run(cmd, check=True)
        print(f"✓ Base image pulled: {base_image}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to pull base image: {e}")
        return False


def interactive_mode():
    """Run container in interactive mode for debugging."""
    print_section("Interactive Mode")

    cmd = [
        "docker", "run", "--rm", "-it",
        "--name", CONTAINER_NAME,
        IMAGE_NAME,
        "/bin/bash"
    ]

    print(f"Starting interactive container: {' '.join(cmd)}")
    print("Type 'exit' to leave the container")

    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n✗ Interrupted")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run KARIOS QGIS Plugin tests in Docker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Force rebuild of Docker image",
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install missing dependencies in container",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove container and image after tests",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive container for debugging",
    )
    parser.add_argument(
        "--skip-submodule-check",
        action="store_true",
        help="Skip git submodule check",
    )

    args = parser.parse_args()

    print_section("KARIOS QGIS Plugin - Docker Test Runner")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Docker dir: {DOCKER_DIR}")

    # Check prerequisites
    if not check_docker():
        sys.exit(1)

    if not args.skip_submodule_check:
        check_git_submodules()

    # Check files exist
    if not DOCKERFILE.exists():
        print(f"✗ Dockerfile not found: {DOCKERFILE}")
        sys.exit(1)

    if not TEST_SCRIPT.exists():
        print(f"✗ Test script not found: {TEST_SCRIPT}")
        sys.exit(1)

    # Pull base image
    if not pull_qgis_image():
        print("⚠ Continuing without pulling base image (may use cached)")

    # Build image
    if args.build or not image_exists():
        if not build_image(force=args.build):
            print("✗ Build failed")
            sys.exit(1)
    else:
        print(f"✓ Using cached image: {IMAGE_NAME}")

    # Run tests or interactive mode
    if args.interactive:
        interactive_mode()
    else:
        success = run_tests(args.install_deps, args.verbose)

        # Cleanup if requested
        if args.cleanup:
            cleanup()

        sys.exit(0 if success else 1)


def image_exists():
    """Check if Docker image exists."""
    try:
        result = subprocess.run(
            ["docker", "images", "-q", IMAGE_NAME],
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


if __name__ == "__main__":
    main()
