import os
import asyncio
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import tempfile
import shutil
from unittest.mock import Mock, patch

from app.main import app
from app.core.config import settings
from app.core.storage_engine import init_storage_engine, get_storage_engine


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_storage_dir():
    """Create a temporary storage directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="test_storage_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def mock_env_vars(test_storage_dir, monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("STORAGE_BASE_PATH", test_storage_dir)
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    
    # Reload settings with test values
    from app.core.config import Settings
    test_settings = Settings()
    with patch('app.core.config.settings', test_settings):
        yield test_settings


@pytest.fixture(scope="session")
def test_app(test_storage_dir):
    """Create FastAPI test application."""
    # Initialize storage engine with test directory
    test_settings = Mock()
    test_settings.STORAGE_BASE_PATH = test_storage_dir
    test_settings.TEMP_FILE_CLEANUP_HOURS = 1
    test_settings.MAX_TEMP_FILE_SIZE_MB = 10
    
    init_storage_engine(test_settings)
    yield app


@pytest.fixture
def client(test_app):
    """Create test client."""
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
async def async_client(test_app):
    """Create async test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_storage_engine():
    """Mock storage engine for unit tests."""
    mock_engine = Mock()
    mock_engine.save_file.return_value = {"url": "http://test.com/file.svg", "filename": "test.svg"}
    mock_engine.get_public_url.return_value = "http://test.com/file.svg"
    mock_engine.cleanup_temp_files.return_value = None
    mock_engine.get_storage_stats.return_value = {"total_files": 0, "total_size": 0}
    
    with patch('app.core.storage_engine.get_storage_engine', return_value=mock_engine):
        yield mock_engine


@pytest.fixture
def sample_chart_data():
    """Sample chart data for testing."""
    return {
        "data": {
            "Series 1": [1, 2, 3, 4, 5],
            "Series 2": [2, 4, 6, 8, 10]
        }
    }




@pytest.fixture
def sample_pdf_request():
    """Sample PDF generation request."""
    return {
        "html_content": "<html><body><h1>Test PDF</h1></body></html>",
        "filename": "test.pdf"
    }


@pytest.fixture
def sample_document_file():
    """Create a sample document file for testing."""
    content = "This is a test document content for testing document extraction."
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(content)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def mock_file_upload():
    """Mock file upload object."""
    mock_file = Mock()
    mock_file.filename = "test.txt"
    mock_file.content_type = "text/plain"
    mock_file.read.return_value = b"test content"
    mock_file.file.read.return_value = b"test content"
    return mock_file