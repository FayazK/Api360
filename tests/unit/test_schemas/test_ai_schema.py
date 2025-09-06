import pytest
from pydantic import ValidationError, HttpUrl

from app.schemas.ai.product import ProductDescriptionRequest, ProductDescriptionResponse


class TestProductDescriptionRequest:
    """Test ProductDescriptionRequest schema validation."""
    
    def test_valid_product_description_request(self):
        """Test valid product description request creation."""
        data = {
            "product_description": "Premium wireless headphones with noise cancellation",
            "image_url": "https://example.com/headphones.jpg",
            "target_audience": "Music professionals and audiophiles",
            "industry": "Consumer Electronics",
            "specialization": "Audio Equipment",
            "tone": "professional",
            "style": "informative"
        }
        
        request = ProductDescriptionRequest(**data)
        
        assert request.product_description == data["product_description"]
        assert str(request.image_url) == data["image_url"]
        assert request.target_audience == data["target_audience"]
        assert request.industry == data["industry"]
        assert request.specialization == data["specialization"]
        assert request.tone == data["tone"]
        assert request.style == data["style"]
    
    def test_minimal_valid_request(self):
        """Test minimal valid request with only required fields."""
        data = {
            "product_description": "Basic product",
            "image_url": "https://example.com/image.jpg"
        }
        
        request = ProductDescriptionRequest(**data)
        
        assert request.product_description == "Basic product"
        assert str(request.image_url) == "https://example.com/image.jpg"
        assert request.target_audience is None
        assert request.industry is None
        assert request.specialization is None
        assert request.tone == "professional"  # Default value
        assert request.style == "informative"  # Default value
    
    def test_default_values(self):
        """Test default values are applied correctly."""
        data = {
            "product_description": "Test product",
            "image_url": "https://example.com/test.jpg"
        }
        
        request = ProductDescriptionRequest(**data)
        
        assert request.tone == "professional"
        assert request.style == "informative"
    
    def test_override_default_values(self):
        """Test that default values can be overridden."""
        data = {
            "product_description": "Luxury product",
            "image_url": "https://example.com/luxury.jpg",
            "tone": "luxury",
            "style": "persuasive"
        }
        
        request = ProductDescriptionRequest(**data)
        
        assert request.tone == "luxury"
        assert request.style == "persuasive"
    
    def test_missing_product_description_raises_error(self):
        """Test that missing product description raises validation error."""
        data = {
            "image_url": "https://example.com/image.jpg"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ProductDescriptionRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "product_description" in errors[0]["loc"]
    
    def test_missing_image_url_raises_error(self):
        """Test that missing image URL raises validation error."""
        data = {
            "product_description": "Test product"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ProductDescriptionRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "image_url" in errors[0]["loc"]
    
    def test_invalid_image_url_raises_error(self):
        """Test that invalid image URL raises validation error."""
        data = {
            "product_description": "Test product",
            "image_url": "not-a-valid-url"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ProductDescriptionRequest(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "url_parsing"
    
    def test_various_valid_urls(self):
        """Test various valid URL formats."""
        valid_urls = [
            "https://example.com/image.jpg",
            "http://example.com/image.png",
            "https://cdn.example.com/path/to/image.gif",
            "https://example.com/image.jpg?param=value",
            "https://example.com:8080/image.jpg"
        ]
        
        for url in valid_urls:
            data = {
                "product_description": "Test product",
                "image_url": url
            }
            
            request = ProductDescriptionRequest(**data)
            assert str(request.image_url) == url
    
    def test_empty_string_fields_are_valid(self):
        """Test that empty strings are valid for optional fields."""
        data = {
            "product_description": "Test product",
            "image_url": "https://example.com/image.jpg",
            "target_audience": "",
            "industry": "",
            "specialization": "",
            "tone": "",
            "style": ""
        }
        
        request = ProductDescriptionRequest(**data)
        
        assert request.target_audience == ""
        assert request.industry == ""
        assert request.specialization == ""
        assert request.tone == ""
        assert request.style == ""
    
    def test_unicode_text_fields(self):
        """Test that unicode text is handled correctly."""
        data = {
            "product_description": "高端无线耳机，具有降噪功能",
            "image_url": "https://example.com/headphones.jpg",
            "target_audience": "音乐专业人士和音响发烧友",
            "industry": "消费电子",
            "specialization": "音频设备",
            "tone": "专业",
            "style": "信息性"
        }
        
        request = ProductDescriptionRequest(**data)
        
        assert request.product_description == data["product_description"]
        assert request.target_audience == data["target_audience"]
        assert request.industry == data["industry"]
        assert request.specialization == data["specialization"]
        assert request.tone == data["tone"]
        assert request.style == data["style"]
    
    def test_model_json_schema(self):
        """Test that the model has expected JSON schema."""
        schema = ProductDescriptionRequest.model_json_schema()
        
        # Check required fields
        assert "product_description" in schema["required"]
        assert "image_url" in schema["required"]
        
        # Check properties exist
        properties = schema["properties"]
        assert "product_description" in properties
        assert "image_url" in properties
        assert "target_audience" in properties
        assert "industry" in properties
        assert "specialization" in properties
        assert "tone" in properties
        assert "style" in properties
        
        # Check example exists
        assert "example" in schema
        example = schema["example"]
        assert "product_description" in example
        assert "image_url" in example
    
    def test_model_serialization(self):
        """Test model serialization to dict and JSON."""
        data = {
            "product_description": "Test product",
            "image_url": "https://example.com/image.jpg",
            "tone": "casual"
        }
        
        request = ProductDescriptionRequest(**data)
        
        # Test dict serialization
        serialized = request.model_dump()
        assert serialized["product_description"] == "Test product"
        assert serialized["image_url"] == "https://example.com/image.jpg"
        assert serialized["tone"] == "casual"
        assert serialized["style"] == "informative"  # Default value
        
        # Test JSON serialization
        json_str = request.model_dump_json()
        assert '"product_description":"Test product"' in json_str
        assert '"image_url":"https://example.com/image.jpg"' in json_str


class TestProductDescriptionResponse:
    """Test ProductDescriptionResponse schema validation."""
    
    def test_valid_product_description_response(self):
        """Test valid product description response creation."""
        data = {
            "description": "This is a comprehensive product description generated by AI."
        }
        
        response = ProductDescriptionResponse(**data)
        
        assert response.description == data["description"]
    
    def test_empty_description_is_valid(self):
        """Test that empty description is valid."""
        data = {"description": ""}
        
        response = ProductDescriptionResponse(**data)
        
        assert response.description == ""
    
    def test_unicode_description(self):
        """Test that unicode descriptions are handled correctly."""
        data = {
            "description": "这是由AI生成的综合产品描述。包含特殊字符：™®©"
        }
        
        response = ProductDescriptionResponse(**data)
        
        assert response.description == data["description"]
    
    def test_long_description(self):
        """Test that long descriptions are handled correctly."""
        long_description = "This is a very long product description. " * 100
        data = {"description": long_description}
        
        response = ProductDescriptionResponse(**data)
        
        assert response.description == long_description
    
    def test_missing_description_raises_error(self):
        """Test that missing description raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ProductDescriptionResponse()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "description" in errors[0]["loc"]
    
    def test_model_serialization(self):
        """Test model serialization to dict and JSON."""
        data = {"description": "Generated product description"}
        
        response = ProductDescriptionResponse(**data)
        
        # Test dict serialization
        assert response.model_dump() == data
        
        # Test JSON serialization
        json_str = response.model_dump_json()
        assert '"description":"Generated product description"' in json_str