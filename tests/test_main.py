import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


class TestApplicationStartup:
    """Test application startup and basic endpoints."""
    
    def test_app_creation(self):
        """Test that the FastAPI app can be created."""
        assert app is not None
        assert app.title == "FastAPI Chart Application"
    
    def test_health_check_via_root(self, client: TestClient):
        """Test that the application responds to basic requests."""
        # Since there's no explicit health endpoint, test a known endpoint
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_docs_accessible(self, client: TestClient):
        """Test that OpenAPI documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_json_accessible(self, client: TestClient):
        """Test that OpenAPI JSON is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.options("/api/charts/", 
                                headers={"Origin": "http://localhost:3000",
                                       "Access-Control-Request-Method": "POST"})
        # CORS middleware should add headers regardless of response status
        assert "access-control-allow-origin" in response.headers or "access-control-allow-methods" in response.headers


class TestStorageEndpoints:
    """Test storage-related endpoints."""
    
    def test_storage_stats_endpoint(self, client: TestClient, mock_storage_engine):
        """Test storage stats endpoint."""
        mock_storage_engine.get_storage_stats.return_value = {
            "public": {
                "total_files": 3,
                "total_size": 2048,
                "categories": {
                    "charts": {"files": 1, "size": 1024},
                    "images": {"files": 2, "size": 1024}
                }
            },
            "temp": {
                "total_files": 2,
                "total_size": 512,
                "categories": {
                    "uploads": {"files": 1, "size": 256},
                    "processing": {"files": 1, "size": 256}
                }
            },
            "templates": {
                "total_files": 0,
                "total_size": 0,
                "categories": {}
            }
        }
        
        response = client.get("/api/storage/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "public" in data
        assert "temp" in data
        assert "templates" in data
    
    def test_storage_cleanup_endpoint(self, client: TestClient, mock_storage_engine):
        """Test storage cleanup endpoint."""
        response = client.post("/api/storage/cleanup")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Cleanup task started"


class TestAsyncApplicationBehavior:
    """Test async behavior of the application."""
    
    @pytest.mark.asyncio
    async def test_async_client_connection(self, async_client: AsyncClient):
        """Test async client can connect to the application."""
        response = await async_client.get("/openapi.json")
        assert response.status_code == 200


@pytest.mark.integration
class TestStaticFileServing:
    """Test static file serving functionality."""
    
    def test_static_directory_mount(self, client: TestClient):
        """Test that static directory is properly mounted."""
        # This will return 404 if no file exists, but should not return 405 or other server errors
        response = client.get("/static/nonexistent.txt")
        assert response.status_code in [404, 200]  # 200 if file exists, 404 if not
    
    def test_storage_directory_mount(self, client: TestClient):
        """Test that storage directory is properly mounted."""
        response = client.get("/storage/nonexistent.txt")
        assert response.status_code in [404, 200]  # 200 if file exists, 404 if not