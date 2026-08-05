#!/usr/bin/env python3
"""Build script for creating the AWS Lambda deployment package.

This script:
1. Creates a temporary build directory
2. Installs dependencies from api/requirements.txt into the build directory
3. Copies the api/app/ source code into the build directory
4. Creates a handler.py with the Mangum wrapper for Lambda
5. Zips everything into dist/lambda.zip
6. Validates the ZIP is under 50MB
7. Cleans up the build directory
"""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# Maximum allowed ZIP size: 50 MB
MAX_ZIP_SIZE = 50 * 1024 * 1024

# Resolve paths relative to the project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_DIR = PROJECT_ROOT / "api"
REQUIREMENTS_FILE = API_DIR / "requirements-aws.txt"
APP_SOURCE_DIR = API_DIR / "app"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
OUTPUT_ZIP = DIST_DIR / "lambda.zip"

HANDLER_CONTENT = """\
from mangum import Mangum
from app.main import app

handler = Mangum(app)
"""


def clean_build_dir():
    """Remove existing build directory if it exists."""
    if BUILD_DIR.exists():
        print(f"Cleaning up existing build directory: {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)


def create_build_dir():
    """Create fresh build directory."""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Created build directory: {BUILD_DIR}")


def install_dependencies():
    """Install Python dependencies into the build directory."""
    print(f"Installing dependencies from {REQUIREMENTS_FILE} into {BUILD_DIR}...")
    result = subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "-r", str(REQUIREMENTS_FILE),
            "-t", str(BUILD_DIR),
            "--quiet",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: Failed to install dependencies:\n{result.stderr}")
        sys.exit(1)
    print("Dependencies installed successfully.")


def copy_app_source():
    """Copy the api/app/ directory into the build directory."""
    dest = BUILD_DIR / "app"
    print(f"Copying application source from {APP_SOURCE_DIR} to {dest}...")
    shutil.copytree(APP_SOURCE_DIR, dest, dirs_exist_ok=True)
    print("Application source copied successfully.")


def create_handler():
    """Create handler.py with the Mangum wrapper at the build root."""
    handler_path = BUILD_DIR / "handler.py"
    print(f"Creating Lambda handler at {handler_path}...")
    handler_path.write_text(HANDLER_CONTENT)
    print("Handler created successfully.")


def create_zip():
    """Zip the contents of the build directory into dist/lambda.zip."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Creating deployment package: {OUTPUT_ZIP}...")

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(BUILD_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(BUILD_DIR)
                zf.write(file_path, arcname)

    print(f"Deployment package created: {OUTPUT_ZIP}")


def validate_zip_size():
    """Validate the ZIP file is under 50MB."""
    zip_size = OUTPUT_ZIP.stat().st_size
    zip_size_mb = zip_size / (1024 * 1024)

    if zip_size > MAX_ZIP_SIZE:
        print(
            f"ERROR: Deployment package is {zip_size_mb:.2f} MB, "
            f"exceeding the 50 MB limit."
        )
        sys.exit(1)

    print(f"Deployment package size: {zip_size_mb:.2f} MB (within 50 MB limit)")


def main():
    """Build the Lambda deployment package."""
    print("=" * 60)
    print("Building Lambda Deployment Package")
    print("=" * 60)

    # Verify prerequisites
    if not REQUIREMENTS_FILE.exists():
        print(f"ERROR: Requirements file not found: {REQUIREMENTS_FILE}")
        sys.exit(1)

    if not APP_SOURCE_DIR.exists():
        print(f"ERROR: Application source directory not found: {APP_SOURCE_DIR}")
        sys.exit(1)

    # Build steps
    clean_build_dir()
    create_build_dir()
    install_dependencies()
    copy_app_source()
    create_handler()
    create_zip()
    validate_zip_size()

    # Clean up build directory
    clean_build_dir()

    print("=" * 60)
    print("SUCCESS: Lambda deployment package built at:")
    print(f"  {OUTPUT_ZIP}")
    print("=" * 60)


if __name__ == "__main__":
    main()
