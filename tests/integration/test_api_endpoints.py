import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, Mock, AsyncMock
from app.main import app
from app.services.ai.factory import AITextGeneratorFactory
from app.services.common.exceptions import ValidationError, ServiceError


@pytest.mark.integration
class TestChartEndpoints:
    """Test chart API endpoints."""
    
    def test_create_bar_chart(self, client: TestClient, mock_storage_engine):
        """Test creating a bar chart."""
        chart_data = {
            "data": {
                "Q1": [100, 200, 150],
                "Q2": [150, 250, 200]
            }
        }
        
        # Mock the storage engine's store_bytes method
        mock_storage_engine.store_bytes.return_value = {
            "url": "/storage/charts/test-chart.svg",
            "filename": "test-chart.svg",
            "path": "charts/test-chart.svg",
            "size": 1024,
            "content_type": "image/svg+xml"
        }
        
        response = client.post(
            "/api/charts/?chart_type=bar&title=Test Chart",
            json=chart_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["url"].startswith("/storage/charts/")
        assert result["url"].endswith(".svg")
    
    def test_create_pie_chart(self, client: TestClient, mock_storage_engine):
        """Test creating a pie chart."""
        chart_data = {
            "data": {
                "Category A": [300],
                "Category B": [200],
                "Category C": [100]
            }
        }
        
        # Mock the storage engine's store_bytes method
        mock_storage_engine.store_bytes.return_value = {
            "url": "/storage/charts/test-pie.svg",
            "filename": "test-pie.svg",
            "path": "charts/test-pie.svg", 
            "size": 1024,
            "content_type": "image/svg+xml"
        }
        
        response = client.post(
            "/api/charts/?chart_type=pie",
            json=chart_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["url"].startswith("/storage/charts/")
        assert result["url"].endswith(".svg")
    
    def test_create_chart_invalid_type(self, client: TestClient):
        """Test creating chart with invalid type."""
        chart_data = {
            "data": {
                "Series 1": [1, 2, 3]
            }
        }
        
        response = client.post(
            "/api/charts/?chart_type=invalid",
            json=chart_data
        )
        
        assert response.status_code == 422
    
    def test_create_chart_missing_data(self, client: TestClient):
        """Test creating chart with missing data."""
        response = client.post(
            "/api/charts/?chart_type=bar",
            json={}
        )
        
        assert response.status_code == 422
    
    def test_create_chart_invalid_chart_type_regex(self, client: TestClient):
        """Test chart type regex validation."""
        chart_data = {
            "data": {
                "Series 1": [1, 2, 3]
            }
        }
        
        response = client.post(
            "/api/charts/?chart_type=scatter",  # Not in allowed types
            json=chart_data
        )
        
        assert response.status_code == 422


@pytest.mark.integration  
class TestPdfEndpoints:
    """Test PDF API endpoints."""
    
    def test_generate_pdf(self, client: TestClient):
        """Test PDF generation."""
        pdf_data = {
            "html_content": "<html><body><h1>Test PDF</h1></body></html>",
            "filename": "test.pdf"
        }
        
        with patch('app.services.pdf_service.generate_pdf') as mock_generate_pdf:
            mock_generate_pdf.return_value = b"fake pdf content"
            
            response = client.post("/api/pdf/", json=pdf_data)
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert response.headers["content-disposition"] == 'attachment; filename="test.pdf"'
            assert response.content == b"fake pdf content"
    
    def test_generate_pdf_missing_html(self, client: TestClient):
        """Test PDF generation with missing HTML content."""
        pdf_data = {"filename": "test.pdf"}
        
        response = client.post("/api/pdf/", json=pdf_data)
        
        assert response.status_code == 422
    
    def test_generate_pdf_missing_filename(self, client: TestClient):
        """Test PDF generation with missing filename."""
        pdf_data = {"html_content": "<html><body>Test</body></html>"}
        
        response = client.post("/api/pdf/", json=pdf_data)
        
        assert response.status_code == 422



@pytest.mark.integration
class TestDocumentEndpoints:
    """Test document processing API endpoints."""
    
    def test_extract_document_text_file(self, client: TestClient, sample_document_file):
        """Test document text extraction from text file."""
        with open(sample_document_file, 'rb') as f:
            files = {"file": ("test.txt", f, "text/plain")}
            
            with patch('app.services.documents.docling_extractor.DoclingExtractor.extract_text') as mock_extract:
                mock_extract.return_value = {
                    "text": "Extracted text content",
                    "markdown": "Extracted text content",
                    "metadata": {"filename": "test.txt", "mime_type": "text/plain"}
                }
                
                response = client.post("/api/documents/extract", files=files)
                
                assert response.status_code == 200
                result = response.json()
                assert result.get("status")
                assert result.get("data", {}).get("markdown")

    def test_extract_document_with_ocr_true(self, client: TestClient, sample_document_file):
        """Ensure use_ocr=true is passed to the service layer."""
        with open(sample_document_file, 'rb') as f:
            files = {"file": ("test.txt", f, "text/plain")}
            with patch('app.services.documents.docling_extractor.DoclingExtractor.extract_text', new_callable=AsyncMock) as mock_extract:
                mock_extract.return_value = {
                    "text": "T",
                    "markdown": "M",
                    "metadata": {"filename": "test.txt", "mime_type": "text/plain"}
                }
                resp = client.post("/api/documents/extract?use_ocr=true", files=files)
                assert resp.status_code == 200
                # Verify the service received the OCR flag
                assert mock_extract.call_args.kwargs.get("use_ocr") is True

    def test_extract_document_with_ocr_default_false(self, client: TestClient, sample_document_file):
        """Ensure use_ocr defaults to false when not provided."""
        with open(sample_document_file, 'rb') as f:
            files = {"file": ("test.txt", f, "text/plain")}
            with patch('app.services.documents.docling_extractor.DoclingExtractor.extract_text', new_callable=AsyncMock) as mock_extract:
                mock_extract.return_value = {
                    "text": "T",
                    "markdown": "M",
                    "metadata": {"filename": "test.txt", "mime_type": "text/plain"}
                }
                resp = client.post("/api/documents/extract", files=files)
                assert resp.status_code == 200
                assert mock_extract.call_args.kwargs.get("use_ocr") is False

    def test_extract_url_success(self, client: TestClient):
        """Test extracting a remote document via URL endpoint."""
        with patch('app.services.documents.docling_extractor.DoclingExtractor.extract_text_from_url', new_callable=AsyncMock) as mock_extract_url:
            mock_extract_url.return_value = {
                "text": "Remote text",
                "markdown": "Remote markdown",
                "metadata": {"filename": "remote.pdf", "mime_type": "application/pdf", "source_url": "https://example.com/remote.pdf"}
            }
            resp = client.post("/api/documents/extract-url?url=https://example.com/remote.pdf&use_ocr=true")
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "success"
            assert mock_extract_url.call_args.kwargs.get("use_ocr") is True

    def test_extract_url_validation_error(self, client: TestClient):
        """Test URL validation error surfaces as 400."""
        with patch('app.services.documents.docling_extractor.DoclingExtractor.extract_text_from_url', new_callable=AsyncMock) as mock_extract_url:
            mock_extract_url.side_effect = ValidationError("Unsupported content-type", field="content_type", value="application/zip")
            resp = client.post("/api/documents/extract-url?url=https://example.com/bad.zip")
            assert resp.status_code == 400

    def test_extract_url_service_error(self, client: TestClient):
        """Test remote fetch/service error surfaces as 502."""
        with patch('app.services.documents.docling_extractor.DoclingExtractor.extract_text_from_url', new_callable=AsyncMock) as mock_extract_url:
            mock_extract_url.side_effect = ServiceError("Failed to fetch URL", error_code="REMOTE_FETCH_FAILED")
            resp = client.post("/api/documents/extract-url?url=https://example.com/404.pdf")
            assert resp.status_code == 502

    def test_extract_url_missing_param(self, client: TestClient):
        """Test missing URL param yields 422 validation error."""
        resp = client.post("/api/documents/extract-url")
        assert resp.status_code == 422

    def test_batch_extract_with_ocr_true(self, client: TestClient, sample_document_file):
        """Ensure OCR flag propagates to each batch extraction call."""
        with open(sample_document_file, 'rb') as f1, open(sample_document_file, 'rb') as f2:
            files = [
                ("files", ("t1.txt", f1, "text/plain")),
                ("files", ("t2.txt", f2, "text/plain")),
            ]
            with patch('app.services.documents.docling_extractor.DoclingExtractor.extract_text', new_callable=AsyncMock) as mock_extract:
                mock_extract.return_value = {
                    "text": "T",
                    "markdown": "M",
                    "metadata": {"filename": "t.txt", "mime_type": "text/plain"}
                }
                resp = client.post("/api/documents/batch-extract?use_ocr=true", files=files)
                assert resp.status_code == 200
                assert mock_extract.call_count == 2
                for call in mock_extract.call_args_list:
                    assert call.kwargs.get("use_ocr") is True
    
    def test_extract_document_no_file(self, client: TestClient):
        """Test document extraction without file."""
        response = client.post("/api/documents/extract")
        
        assert response.status_code == 422


@pytest.mark.integration
class TestImageEndpoints:
    """Test image processing API endpoints."""
    
    def test_process_image(self, client: TestClient, mock_storage_engine):
        """Test image conversion endpoint."""
        # Mock the storage engine's store_bytes method
        mock_storage_engine.store_bytes.return_value = {
            "url": "/storage/images/processed.png",
            "filename": "processed.png",
            "path": "images/processed.png",
            "size": 2048,
            "content_type": "image/png"
        }
        
        files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
        response = client.post(
            "/api/images/convert?output_format=png&width=800",
            files=files
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["url"] == "/storage/images/processed.png"
    
    def test_process_image_no_file(self, client: TestClient):
        """Test image conversion without file."""
        response = client.post("/api/images/convert")
        
        assert response.status_code == 422


@pytest.mark.integration
class TestAsyncEndpoints:
    """Test async endpoint behavior."""
    
    @pytest.mark.asyncio
    async def test_async_chart_creation(self, async_client: AsyncClient, mock_storage_engine):
        """Test async chart creation."""
        chart_data = {
            "data": {
                "Async Series": [1, 2, 3, 4, 5]
            }
        }
        
        # Mock the storage engine's store_bytes method
        mock_storage_engine.store_bytes.return_value = {
            "url": "/storage/charts/async-chart.svg",
            "filename": "async-chart.svg",
            "path": "charts/async-chart.svg",
            "size": 1024,
            "content_type": "image/svg+xml"
        }
        
        response = await async_client.post(
            "/api/charts/?chart_type=line",
            json=chart_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["url"].startswith("/storage/charts/")
        assert result["url"].endswith(".svg")
    
    @pytest.mark.asyncio
    async def test_async_pdf_generation(self, async_client: AsyncClient):
        """Test async PDF generation."""
        pdf_data = {
            "html_content": "<html><body><h1>Async Test</h1></body></html>",
            "filename": "async-test.pdf"
        }
        
        with patch('app.services.pdf_service.generate_pdf') as mock_generate_pdf:
            mock_generate_pdf.return_value = b"async pdf content"
            
            response = await async_client.post("/api/pdf/", json=pdf_data)
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert response.content == b"async pdf content"


@pytest.mark.integration
@pytest.mark.slow
class TestEndpointPerformance:
    """Test endpoint performance characteristics."""
    
    def test_multiple_chart_requests(self, client: TestClient, mock_storage_engine):
        """Test handling multiple chart requests."""
        chart_data = {
            "data": {
                "Performance Test": [i for i in range(100)]
            }
        }
        
        # Mock the storage engine's store_bytes method
        mock_storage_engine.store_bytes.return_value = {
            "url": "/storage/charts/perf.svg",
            "filename": "perf.svg",
            "path": "charts/perf.svg",
            "size": 2048,
            "content_type": "image/svg+xml"
        }
        
        # Send multiple requests
        for i in range(5):
            response = client.post(
                f"/api/charts/?chart_type=bar&title=Performance Test {i}",
                json=chart_data
            )
            assert response.status_code == 200
    
    def test_large_chart_data(self, client: TestClient, mock_storage_engine):
        """Test handling large chart datasets."""
        large_data = {
            "data": {
                f"Series {i}": [j for j in range(1000)]
                for i in range(10)
            }
        }
        
        # Mock the storage engine's store_bytes method
        mock_storage_engine.store_bytes.return_value = {
            "url": "/storage/charts/large.svg",
            "filename": "large.svg",
            "path": "charts/large.svg",
            "size": 10240,
            "content_type": "image/svg+xml"
        }
        
        response = client.post(
            "/api/charts/?chart_type=line&title=Large Dataset",
            json=large_data
        )
        
        assert response.status_code == 200


@pytest.mark.integration
class TestAIEndpoints:
    """Test AI API endpoints."""
    
    def test_ai_health_check_with_providers(self, client: TestClient):
        """Test AI health check with providers configured but unavailable."""
        response = client.get("/api/ai/health")
        
        assert response.status_code == 200
        data = response.json()
        # With real environment settings, it should be configured but may be unhealthy due to invalid keys
        assert data["configured"] is True
    
    def test_ai_generate_endpoints_exist(self, client: TestClient):
        """Test AI endpoint exists and handles requests appropriately."""
        # Test that endpoints exist and return expected error codes
        response = client.post("/api/ai/generate", json={"prompt": "Test"})
        # Should be 503 (service unavailable) due to invalid API key or 422 (validation error)
        assert response.status_code in [503, 422]
        
        response = client.post("/api/ai/validate", json={"prompt": "Test"})
        # Should be 503 (service unavailable) due to invalid API key or 422 (validation error)
        assert response.status_code in [503, 422, 200]
