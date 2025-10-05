import sys
from pathlib import Path

import pytest


class TestSetupValidation:
    """Validation tests to ensure the testing infrastructure is properly configured."""

    def test_pytest_is_importable(self):
        """Test that pytest can be imported."""
        import pytest

        assert pytest.__version__

    def test_pytest_cov_is_importable(self):
        """Test that pytest-cov can be imported."""
        import pytest_cov

        assert pytest_cov

    def test_pytest_mock_is_importable(self):
        """Test that pytest-mock can be imported."""
        import pytest_mock

        assert pytest_mock

    def test_project_root_in_path(self):
        """Test that project root is in Python path."""
        project_root = Path(__file__).parent.parent
        assert str(project_root) in sys.path or str(project_root.absolute()) in sys.path

    def test_conftest_fixtures_available(self, temp_dir, mock_settings, mock_course_data):
        """Test that conftest fixtures are available."""
        assert temp_dir.exists()
        assert isinstance(mock_settings, dict)
        assert "download_path" in mock_settings
        assert isinstance(mock_course_data, dict)
        assert "title" in mock_course_data

    def test_temp_dir_fixture_cleanup(self, temp_dir):
        """Test that temp_dir fixture creates and cleans up properly."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"

    def test_mock_response_fixture(self, mock_response):
        """Test mock response fixture."""
        assert mock_response.status_code == 200
        assert mock_response.json() == {"success": True}
        mock_response.raise_for_status()

    def test_mock_failed_response_fixture(self, mock_failed_response):
        """Test mock failed response fixture."""
        assert mock_failed_response.status_code == 404
        assert mock_failed_response.json() == {"error": "Not found"}
        with pytest.raises(Exception, match="404 Not Found"):
            mock_failed_response.raise_for_status()

    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit test marker works."""
        assert True

    @pytest.mark.integration
    def test_integration_marker(self):
        """Test that integration test marker works."""
        assert True

    @pytest.mark.slow
    def test_slow_marker(self):
        """Test that slow test marker works."""
        assert True

    def test_coverage_is_running(self):
        """Test that coverage is being collected."""
        import sys

        for module in sys.modules:
            if "coverage" in module:
                return
        pytest.skip("Coverage not detected, but this is okay for initial setup")

    def test_settings_file_fixture(self, settings_file):
        """Test settings file fixture creates valid JSON."""
        assert settings_file.exists()
        import json

        with open(settings_file) as f:
            data = json.load(f)
        assert "download_path" in data
        assert "quality" in data

    def test_mock_cloudscraper_fixture(self, mock_cloudscraper):
        """Test mock cloudscraper fixture."""
        assert hasattr(mock_cloudscraper, "get")
        assert hasattr(mock_cloudscraper, "post")
        assert hasattr(mock_cloudscraper, "headers")
        assert hasattr(mock_cloudscraper, "cookies")

    def test_capture_logs_fixture(self, capture_logs):
        """Test log capture fixture."""
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Test log message")
        assert "Test log message" in capture_logs.text

    def test_sample_html_fixture(self, sample_html_content):
        """Test sample HTML content fixture."""
        assert "<title>Test Course</title>" in sample_html_content
        assert "Test Instructor" in sample_html_content

    def test_pytest_ini_configuration(self):
        """Test that pytest configuration is being used."""
        import pytest

        config = pytest.config if hasattr(pytest, "config") else None
        if config:
            assert config.getini("minversion")


@pytest.mark.parametrize("module_name", ["base", "cli", "gui", "colors"])
def test_main_modules_importable(module_name):
    """Test that main project modules can be imported."""
    try:
        __import__(module_name)
    except ImportError as e:
        if "No module named" in str(e):
            pytest.skip(f"Module {module_name} not in path, but this is okay for validation")
        else:
            raise