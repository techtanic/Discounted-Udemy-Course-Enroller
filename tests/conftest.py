import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_settings():
    """Mock settings dictionary for testing."""
    return {
        "download_path": "/tmp/downloads",
        "quality": "1080p",
        "concurrent_downloads": 3,
        "retry_attempts": 3,
        "timeout": 30,
        "verbose": False,
        "save_credentials": False,
        "use_proxy": False,
        "proxy_url": "",
    }


@pytest.fixture
def mock_course_data():
    """Mock Udemy course data for testing."""
    return {
        "id": 12345,
        "title": "Test Course",
        "url": "https://www.udemy.com/course/test-course/",
        "instructor": "Test Instructor",
        "num_lectures": 50,
        "duration": 3600,
        "is_paid": True,
        "price": "$99.99",
        "rating": 4.5,
        "num_reviews": 1000,
    }


@pytest.fixture
def mock_lecture_data():
    """Mock Udemy lecture data for testing."""
    return {
        "id": 67890,
        "title": "Introduction to Testing",
        "duration": 600,
        "video_url": "https://example.com/video.mp4",
        "resources": [
            {"title": "Slides.pdf", "url": "https://example.com/slides.pdf"},
            {"title": "Code.zip", "url": "https://example.com/code.zip"},
        ],
        "captions": [
            {"language": "en", "url": "https://example.com/captions_en.vtt"},
            {"language": "es", "url": "https://example.com/captions_es.vtt"},
        ],
    }


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    mock = Mock()
    mock.status_code = 200
    mock.headers = {"Content-Type": "application/json"}
    mock.text = '{"success": true}'
    mock.json.return_value = {"success": True}
    mock.content = b'{"success": true}'
    mock.raise_for_status = Mock()
    return mock


@pytest.fixture
def mock_failed_response():
    """Create a mock failed response object."""
    mock = Mock()
    mock.status_code = 404
    mock.headers = {"Content-Type": "application/json"}
    mock.text = '{"error": "Not found"}'
    mock.json.return_value = {"error": "Not found"}
    mock.content = b'{"error": "Not found"}'
    mock.raise_for_status = Mock(side_effect=Exception("404 Not Found"))
    return mock


@pytest.fixture
def settings_file(temp_dir):
    """Create a temporary settings file."""
    settings_path = temp_dir / "test-settings.json"
    settings_data = {
        "download_path": str(temp_dir / "downloads"),
        "quality": "720p",
        "concurrent_downloads": 2,
    }
    with open(settings_path, "w") as f:
        json.dump(settings_data, f)
    yield settings_path
    if settings_path.exists():
        settings_path.unlink()


@pytest.fixture
def mock_cloudscraper(mocker):
    """Mock cloudscraper session."""
    mock_session = Mock()
    mock_session.get = Mock()
    mock_session.post = Mock()
    mock_session.headers = {}
    mock_session.cookies = {}
    mocker.patch("cloudscraper.create_scraper", return_value=mock_session)
    return mock_session


@pytest.fixture
def mock_browser_cookies(mocker):
    """Mock browser cookies retrieval."""
    mock_cookies = [
        {"name": "access_token", "value": "test_token", "domain": ".udemy.com"},
        {"name": "client_id", "value": "test_client", "domain": ".udemy.com"},
    ]
    mocker.patch("rookiepy.load", return_value=mock_cookies)
    return mock_cookies


@pytest.fixture
def capture_logs(caplog):
    """Fixture to capture log output."""
    import logging

    caplog.set_level(logging.DEBUG)
    yield caplog


@pytest.fixture
def mock_gui_window(mocker):
    """Mock FreeSimpleGUI window."""
    mock_window = Mock()
    mock_window.read = Mock(return_value=("OK", {"input": "test"}))
    mock_window.close = Mock()
    mock_window.__getitem__ = Mock()
    mock_window.update = Mock()
    mocker.patch("FreeSimpleGUI.Window", return_value=mock_window)
    return mock_window


@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_rich_console(mocker):
    """Mock rich console for testing CLI output."""
    mock_console = Mock()
    mock_console.print = Mock()
    mock_console.log = Mock()
    mock_console.status = Mock()
    mocker.patch("rich.console.Console", return_value=mock_console)
    return mock_console


@pytest.fixture
def sample_html_content():
    """Sample HTML content for testing parsers."""
    return """
    <html>
        <head><title>Test Course</title></head>
        <body>
            <div class="course-title">Test Course</div>
            <div class="instructor">Test Instructor</div>
            <div class="price">$99.99</div>
            <div class="rating">4.5</div>
        </body>
    </html>
    """


@pytest.fixture
def mock_download_progress():
    """Mock download progress callback."""
    progress_data = []

    def progress_callback(current, total, speed=0):
        progress_data.append(
            {"current": current, "total": total, "speed": speed, "percentage": (current / total) * 100 if total > 0 else 0}
        )

    progress_callback.data = progress_data
    return progress_callback