import pytest
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from fastapi import HTTPException

from app.services.ai.base import AIService
from app.schemas.ai.product import ProductDescriptionRequest


class TestAIServiceInit:
    """Test AIService initialization."""
    
    def test_ai_service_initialization(self):
        """Test AIService can be initialized with API key."""
        with patch('app.services.ai.base.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            
            service = AIService("test-api-key")
            
            assert service.client == mock_client
            assert service.model == "claude-3-5-sonnet-latest"
            assert service.template_manager is not None
            mock_anthropic.assert_called_once_with(api_key="test-api-key")


class TestProductDescriptionGeneration:
    """Test product description generation."""
    
    @pytest.mark.asyncio
    async def test_generate_product_description_text_only(self):
        """Test generating product description without image."""
        request = ProductDescriptionRequest(
            product_description="Test product",
            target_audience="developers",
            tone="professional",
            style="technical",
            industry="software",
            specialization="web development"
        )
        
        with patch('app.services.ai.base.anthropic.Anthropic') as mock_anthropic, \
             patch('app.services.ai.base.TemplateManager') as mock_template_manager:
            
            # Mock Anthropic client
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = "Generated product description"
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client
            
            # Mock template manager
            mock_tm_instance = Mock()
            mock_tm_instance.render_prompt.return_value = "rendered prompt"
            mock_template_manager.return_value = mock_tm_instance
            
            service = AIService("test-api-key")
            result = await service.generate_product_description(request)
            
            assert result == "Generated product description"
            mock_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_product_description_with_image(self):
        """Test generating product description with image."""
        request = ProductDescriptionRequest(
            product_description="Test product",
            target_audience="consumers",
            tone="casual",
            style="marketing",
            industry="retail",
            specialization="fashion",
            image_url="http://example.com/image.jpg"
        )
        
        with patch('app.services.ai.base.anthropic.Anthropic') as mock_anthropic, \
             patch('app.services.ai.base.TemplateManager') as mock_template_manager, \
             patch.object(AIService, '_fetch_image', new_callable=AsyncMock) as mock_fetch_image:
            
            # Mock image fetching
            mock_fetch_image.return_value = {
                'data': 'base64encodeddata',
                'mime_type': 'image/jpeg'
            }
            
            # Mock Anthropic client
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = "Generated description with image"
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client
            
            # Mock template manager
            mock_tm_instance = Mock()
            mock_tm_instance.render_prompt.return_value = "rendered prompt"
            mock_template_manager.return_value = mock_tm_instance
            
            service = AIService("test-api-key")
            result = await service.generate_product_description(request)
            
            assert result == "Generated description with image"
            mock_fetch_image.assert_called_once_with("http://example.com/image.jpg")
            mock_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_product_description_image_fetch_error(self):
        """Test handling of image fetch errors."""
        request = ProductDescriptionRequest(
            product_description="Test product",
            target_audience="consumers",
            tone="casual",
            style="marketing",
            industry="retail",
            specialization="fashion",
            image_url="http://example.com/invalid.jpg"
        )
        
        with patch('app.services.ai.base.anthropic.Anthropic') as mock_anthropic, \
             patch('app.services.ai.base.TemplateManager') as mock_template_manager, \
             patch.object(AIService, '_fetch_image', new_callable=AsyncMock) as mock_fetch_image:
            
            # Mock image fetching to raise HTTPException
            mock_fetch_image.side_effect = HTTPException(status_code=400, detail="Image not found")
            
            # Mock Anthropic client (should not be called due to image error)
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            
            # Mock template manager
            mock_tm_instance = Mock()
            mock_template_manager.return_value = mock_tm_instance
            
            service = AIService("test-api-key")
            
            with pytest.raises(HTTPException, match="Image not found"):
                await service.generate_product_description(request)
    
    @pytest.mark.asyncio
    async def test_generate_product_description_api_error(self):
        """Test handling of Anthropic API errors."""
        request = ProductDescriptionRequest(
            product_description="Test product",
            target_audience="developers",
            tone="professional",
            style="technical",
            industry="software",
            specialization="web development"
        )
        
        with patch('app.services.ai.base.anthropic.Anthropic') as mock_anthropic, \
             patch('app.services.ai.base.TemplateManager') as mock_template_manager:
            
            # Mock Anthropic client to raise exception
            mock_client = Mock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client
            
            # Mock template manager
            mock_tm_instance = Mock()
            mock_tm_instance.render_prompt.return_value = "rendered prompt"
            mock_template_manager.return_value = mock_tm_instance
            
            service = AIService("test-api-key")
            
            with pytest.raises(HTTPException, match="Error generating product description"):
                await service.generate_product_description(request)


class TestImageFetching:
    """Test image fetching functionality."""
    
    @pytest.mark.asyncio
    async def test_fetch_image_success(self):
        """Test successful image fetching."""
        with patch('app.services.ai.base.ImageBuilder') as mock_image_builder, \
             patch('app.services.ai.base.save_temp_image') as mock_save_temp, \
             patch('app.services.ai.base.get_base64_encoded_image') as mock_get_base64, \
             patch('app.services.ai.base.cleanup_temp_file') as mock_cleanup:
            
            # Mock ImageBuilder
            mock_builder_instance = Mock()
            mock_builder_instance.resize.return_value = mock_builder_instance
            mock_builder_instance.get.return_value = b"processed image data"
            mock_builder_instance.get_mime_type.return_value = "image/jpeg"
            mock_image_builder.return_value = mock_builder_instance
            
            # Mock async download method
            async def mock_download(url):
                return mock_builder_instance
            mock_builder_instance.download = mock_download
            
            # Mock other functions
            mock_save_temp.return_value = "/tmp/test.png"
            mock_get_base64.return_value = "base64encodeddata"
            
            result = await AIService._fetch_image("http://example.com/image.jpg")
            
            assert result == {
                'data': 'base64encodeddata',
                'mime_type': 'image/jpeg'
            }
            
            mock_save_temp.assert_called_once()
            mock_get_base64.assert_called_once_with("/tmp/test.png")
            mock_cleanup.assert_called_once_with("/tmp/test.png")
    
    @pytest.mark.asyncio
    async def test_fetch_image_connection_error(self):
        """Test image fetching with connection error."""
        with patch('app.services.ai.base.ImageBuilder') as mock_image_builder:
            mock_builder_instance = Mock()
            
            # Mock download to raise ClientConnectorError
            async def mock_download(url):
                raise aiohttp.ClientConnectorError(connection_key=None, os_error=None)
            mock_builder_instance.download = mock_download
            mock_image_builder.return_value = mock_builder_instance
            
            with pytest.raises(HTTPException, match="Unable to connect to the image URL"):
                await AIService._fetch_image("http://invalid.com/image.jpg")
    
    @pytest.mark.asyncio
    async def test_fetch_image_404_error(self):
        """Test image fetching with 404 error."""
        with patch('app.services.ai.base.ImageBuilder') as mock_image_builder:
            mock_builder_instance = Mock()
            
            # Mock download to raise 404 error
            async def mock_download(url):
                raise aiohttp.ClientResponseError(
                    request_info=None, 
                    history=None, 
                    status=404,
                    message="Not Found"
                )
            mock_builder_instance.download = mock_download
            mock_image_builder.return_value = mock_builder_instance
            
            with pytest.raises(HTTPException, match="Image not found at the provided URL"):
                await AIService._fetch_image("http://example.com/notfound.jpg")
    
    @pytest.mark.asyncio
    async def test_fetch_image_invalid_format(self):
        """Test image fetching with invalid image format."""
        with patch('app.services.ai.base.ImageBuilder') as mock_image_builder, \
             patch('app.services.ai.base.save_temp_image') as mock_save_temp, \
             patch('app.services.ai.base.cleanup_temp_file') as mock_cleanup:
            
            mock_builder_instance = Mock()
            mock_builder_instance.resize.return_value = mock_builder_instance
            mock_builder_instance.get.return_value = None  # Invalid image data
            mock_builder_instance.get_mime_type.return_value = None
            mock_image_builder.return_value = mock_builder_instance
            
            # Mock async download
            async def mock_download(url):
                return mock_builder_instance
            mock_builder_instance.download = mock_download
            
            with pytest.raises(HTTPException, match="Invalid image format"):
                await AIService._fetch_image("http://example.com/invalid.txt")