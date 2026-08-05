#!/usr/bin/env python3
"""Build script for creating the Azure Functions deployment package.

This script:
1. Validates prerequisites (api/requirements-azure.txt, api/app/ exist)
2. Creates a temporary build directory
3. Installs dependencies from api/requirements-azure.txt into the build directory
4. Copies the api/app/ source code into the build directory
5. Copies the api/azure_dal/ directory into the build directory (if it exists)
6. Creates function_app.py with the Azure Functions ASGI adapter wrapping FastAPI
7. Creates host.json with Azure Functions runtime configuration
8. Zips everything into dist/azure_functions.zip
9. Validates the ZIP size (warn at 500MB, fail at 1GB)
10. Cleans up the build directory
"""

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# Maximum allowed ZIP size: 1 GB
MAX_ZIP_SIZE = 1 * 1024 * 1024 * 1024
# Warning threshold: 500 MB
WARN_ZIP_SIZE = 500 * 1024 * 1024

# Resolve paths relative to the project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_DIR = PROJECT_ROOT / "api"
REQUIREMENTS_FILE = API_DIR / "requirements-azure.txt"
APP_SOURCE_DIR = API_DIR / "app"
AZURE_DAL_DIR = API_DIR / "azure_dal"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
OUTPUT_ZIP = DIST_DIR / "azure_functions.zip"

FUNCTION_APP_CONTENT = """\
import azure.functions as func
from app.main import app as fastapi_app

app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
"""

HOST_JSON_CONTENT = {
    "version": "2.0",
    "extensionBundle": {
        "id": "Microsoft.Azure.Functions.ExtensionBundle",
        "version": "[4.*, 5.0.0)",
    },
}


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


def copy_azure_dal():
    """Copy the api/azure_dal/ directory into the build directory (if it exists)."""
    if AZURE_DAL_DIR.exists():
        dest = BUILD_DIR / "azure_dal"
        print(f"Copying Azure DAL from {AZURE_DAL_DIR} to {dest}...")
        shutil.copytree(AZURE_DAL_DIR, dest, dirs_exist_ok=True)
        print("Azure DAL copied successfully.")
    else:
        print(f"NOTE: Azure DAL directory not found at {AZURE_DAL_DIR}, skipping.")


def create_function_app():
    """Create function_app.py with the Azure Functions ASGI adapter at the build root."""
    function_app_path = BUILD_DIR / "function_app.py"
    print(f"Creating Azure Functions entry point at {function_app_path}...")
    function_app_path.write_text(FUNCTION_APP_CONTENT)
    print("function_app.py created successfully.")


def create_host_json():
    """Create host.json with Azure Functions runtime configuration at the build root."""
    host_json_path = BUILD_DIR / "host.json"
    print(f"Creating host.json at {host_json_path}...")
    host_json_path.write_text(json.dumps(HOST_JSON_CONTENT, indent=2) + "\n")
    print("host.json created successfully.")


def create_zip():
    """Zip the contents of the build directory into dist/azure_functions.zip."""
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
    """Validate the ZIP file size (warn at 500MB, fail at 1GB)."""
    zip_size = OUTPUT_ZIP.stat().st_size
    zip_size_mb = zip_size / (1024 * 1024)

    if zip_size > MAX_ZIP_SIZE:
        print(
            f"ERROR: Deployment package is {zip_size_mb:.2f} MB, "
            f"exceeding the 1 GB limit."
        )
        sys.exit(1)

    if zip_size > WARN_ZIP_SIZE:
        print(
            f"WARNING: Deployment package is {zip_size_mb:.2f} MB, "
            f"approaching the 1 GB limit."
        )
    else:
        print(f"Deployment package size: {zip_size_mb:.2f} MB (within limits)")


def main():
    """Build the Azure Functions deployment package."""
    print("=" * 60)
    print("Building Azure Functions Deployment Package")
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
    copy_azure_dal()
    create_function_app()
    create_host_json()
    create_zip()
    validate_zip_size()

    # Clean up build directory
    clean_build_dir()

    print("=" * 60)
    print("SUCCESS: Azure Functions deployment package built at:")
    print(f"  {OUTPUT_ZIP}")
    print("=" * 60)


if __name__ == "__main__":
    main()
