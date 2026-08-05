"""Unit tests for scripts/build_azure_functions_package.py.

Tests validate:
- Prerequisite checks (exit code 1 for missing files/directories)
- ZIP archive contents (function_app.py, host.json, app/ directory)
- Generated file content matches expected templates

Requirements: 10.4, 10.5, 10.8
"""

import json
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Path to the build script under test
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD_SCRIPT = PROJECT_ROOT / "scripts" / "build_azure_functions_package.py"


def run_build_script(env=None):
    """Run the build script and return the CompletedProcess."""
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    return result


class TestPrerequisiteValidation:
    """Test that the build script exits with code 1 when prerequisites are missing."""

    def test_exit_code_1_when_requirements_azure_txt_missing(self, tmp_path, monkeypatch):
        """Exit code 1 with error message when api/requirements-azure.txt is missing."""
        # Import the module to patch its constants
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "build_azure_functions_package", BUILD_SCRIPT
        )
        module = importlib.util.module_from_spec(spec)

        # Patch paths to use tmp_path where requirements file doesn't exist
        fake_api_dir = tmp_path / "api"
        fake_api_dir.mkdir()
        # Create app/ dir so only requirements check triggers
        (fake_api_dir / "app").mkdir()
        # Do NOT create requirements-azure.txt

        with patch.dict("os.environ", {}):
            spec.loader.exec_module(module)
            # Override the module-level constants
            module.REQUIREMENTS_FILE = fake_api_dir / "requirements-azure.txt"
            module.APP_SOURCE_DIR = fake_api_dir / "app"
            module.BUILD_DIR = tmp_path / "build"
            module.DIST_DIR = tmp_path / "dist"
            module.OUTPUT_ZIP = tmp_path / "dist" / "azure_functions.zip"

        # Run main and expect SystemExit with code 1
        with pytest.raises(SystemExit) as exc_info:
            module.main()
        assert exc_info.value.code == 1

    def test_exit_code_1_when_app_directory_missing(self, tmp_path, monkeypatch):
        """Exit code 1 with error message when api/app/ directory is missing."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "build_azure_functions_package", BUILD_SCRIPT
        )
        module = importlib.util.module_from_spec(spec)

        fake_api_dir = tmp_path / "api"
        fake_api_dir.mkdir()
        # Create requirements file so that check passes
        (fake_api_dir / "requirements-azure.txt").write_text("azure-functions==1.0.0\n")
        # Do NOT create app/ directory

        with patch.dict("os.environ", {}):
            spec.loader.exec_module(module)
            module.REQUIREMENTS_FILE = fake_api_dir / "requirements-azure.txt"
            module.APP_SOURCE_DIR = fake_api_dir / "app"
            module.BUILD_DIR = tmp_path / "build"
            module.DIST_DIR = tmp_path / "dist"
            module.OUTPUT_ZIP = tmp_path / "dist" / "azure_functions.zip"

        with pytest.raises(SystemExit) as exc_info:
            module.main()
        assert exc_info.value.code == 1


class TestZipContents:
    """Test that the generated ZIP contains expected files and directories."""

    @pytest.fixture()
    def build_zip(self, tmp_path):
        """Build a ZIP using the script with patched paths and return the ZIP path."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "build_azure_functions_package", BUILD_SCRIPT
        )
        module = importlib.util.module_from_spec(spec)

        # Set up fake project structure
        fake_api_dir = tmp_path / "api"
        fake_api_dir.mkdir()
        (fake_api_dir / "requirements-azure.txt").write_text("# empty deps\n")
        app_dir = fake_api_dir / "app"
        app_dir.mkdir()
        (app_dir / "__init__.py").write_text("")
        (app_dir / "main.py").write_text("app = None\n")

        with patch.dict("os.environ", {}):
            spec.loader.exec_module(module)
            module.PROJECT_ROOT = tmp_path
            module.API_DIR = fake_api_dir
            module.REQUIREMENTS_FILE = fake_api_dir / "requirements-azure.txt"
            module.APP_SOURCE_DIR = app_dir
            module.AZURE_DAL_DIR = fake_api_dir / "azure_dal"
            module.BUILD_DIR = tmp_path / "build"
            module.DIST_DIR = tmp_path / "dist"
            module.OUTPUT_ZIP = tmp_path / "dist" / "azure_functions.zip"

        # Run build steps manually (skip install_dependencies which calls pip)
        module.clean_build_dir()
        module.create_build_dir()
        # Skip install_dependencies - would call pip for empty requirements
        module.copy_app_source()
        module.copy_azure_dal()
        module.create_function_app()
        module.create_host_json()
        module.create_zip()

        return module.OUTPUT_ZIP

    def test_zip_contains_function_app_py(self, build_zip):
        """ZIP archive contains function_app.py at the root."""
        with zipfile.ZipFile(build_zip, "r") as zf:
            names = zf.namelist()
        assert "function_app.py" in names

    def test_zip_contains_host_json(self, build_zip):
        """ZIP archive contains host.json at the root."""
        with zipfile.ZipFile(build_zip, "r") as zf:
            names = zf.namelist()
        assert "host.json" in names

    def test_zip_contains_app_directory(self, build_zip):
        """ZIP archive contains the app/ directory with source code."""
        with zipfile.ZipFile(build_zip, "r") as zf:
            names = zf.namelist()
        # Check that app/ entries exist (files inside app/ directory)
        app_entries = [n for n in names if n.startswith("app/")]
        assert len(app_entries) > 0
        # Specifically check for known files
        assert "app/__init__.py" in names
        assert "app/main.py" in names


class TestGeneratedFileContent:
    """Test that generated files match expected templates."""

    @pytest.fixture()
    def build_dir_with_generated_files(self, tmp_path):
        """Create a build directory with generated function_app.py and host.json."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "build_azure_functions_package", BUILD_SCRIPT
        )
        module = importlib.util.module_from_spec(spec)

        with patch.dict("os.environ", {}):
            spec.loader.exec_module(module)
            module.BUILD_DIR = tmp_path / "build"

        module.BUILD_DIR.mkdir(parents=True)
        module.create_function_app()
        module.create_host_json()

        return module.BUILD_DIR

    def test_function_app_py_content_matches_expected_template(
        self, build_dir_with_generated_files
    ):
        """Generated function_app.py matches the expected ASGI adapter template."""
        function_app_path = build_dir_with_generated_files / "function_app.py"
        content = function_app_path.read_text()

        expected = (
            "import azure.functions as func\n"
            "from app.main import app as fastapi_app\n"
            "\n"
            "app = func.AsgiFunctionApp("
            "app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)\n"
        )
        assert content == expected

    def test_host_json_content_matches_expected_schema(
        self, build_dir_with_generated_files
    ):
        """Generated host.json matches the expected version 2.0 schema with extension bundle."""
        host_json_path = build_dir_with_generated_files / "host.json"
        content = json.loads(host_json_path.read_text())

        expected = {
            "version": "2.0",
            "extensionBundle": {
                "id": "Microsoft.Azure.Functions.ExtensionBundle",
                "version": "[4.*, 5.0.0)",
            },
        }
        assert content == expected
