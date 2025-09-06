import pytest
from pydantic import ValidationError

from app.schemas.chart import ChartData


class TestChartDataSchema:
    """Test ChartData schema validation."""
    
    def test_valid_chart_data(self):
        """Test valid chart data creation."""
        data = {
            "data": {
                "Series 1": [1, 2, 3, 4, 5],
                "Series 2": [2, 4, 6, 8, 10]
            }
        }
        
        chart_data = ChartData(**data)
        
        assert chart_data.data == data["data"]
        assert len(chart_data.data) == 2
        assert "Series 1" in chart_data.data
        assert "Series 2" in chart_data.data
    
    def test_single_series_chart_data(self):
        """Test chart data with single series."""
        data = {
            "data": {
                "Revenue": [100, 150, 200, 180, 220]
            }
        }
        
        chart_data = ChartData(**data)
        
        assert chart_data.data == data["data"]
        assert len(chart_data.data) == 1
        assert chart_data.data["Revenue"] == [100, 150, 200, 180, 220]
    
    def test_empty_chart_data(self):
        """Test empty chart data is valid."""
        data = {"data": {}}
        
        chart_data = ChartData(**data)
        
        assert chart_data.data == {}
        assert len(chart_data.data) == 0
    
    def test_empty_series_values(self):
        """Test series with empty values."""
        data = {
            "data": {
                "Empty Series": [],
                "Non-empty Series": [1, 2, 3]
            }
        }
        
        chart_data = ChartData(**data)
        
        assert chart_data.data["Empty Series"] == []
        assert chart_data.data["Non-empty Series"] == [1, 2, 3]
    
    def test_mixed_positive_negative_values(self):
        """Test chart data with positive and negative values."""
        data = {
            "data": {
                "Profits": [100, -50, 200, -30, 150],
                "Losses": [-100, -200, -150]
            }
        }
        
        chart_data = ChartData(**data)
        
        assert chart_data.data == data["data"]
        assert chart_data.data["Profits"] == [100, -50, 200, -30, 150]
        assert chart_data.data["Losses"] == [-100, -200, -150]
    
    def test_zero_values(self):
        """Test chart data with zero values."""
        data = {
            "data": {
                "Zero Series": [0, 0, 0],
                "Mixed Series": [0, 5, 0, 10, 0]
            }
        }
        
        chart_data = ChartData(**data)
        
        assert chart_data.data["Zero Series"] == [0, 0, 0]
        assert chart_data.data["Mixed Series"] == [0, 5, 0, 10, 0]
    
    def test_large_numbers(self):
        """Test chart data with large numbers."""
        data = {
            "data": {
                "Big Numbers": [1000000, 2500000, 3750000],
                "Very Big Numbers": [1e9, 2.5e9, 3.75e9]
            }
        }
        
        chart_data = ChartData(**data)
        
        assert chart_data.data == data["data"]
    
    def test_missing_data_field_raises_error(self):
        """Test that missing data field raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ChartData()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "data" in errors[0]["loc"]
    
    def test_invalid_data_type_raises_error(self):
        """Test that invalid data type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ChartData(data="invalid")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "dict_type"
    
    def test_invalid_series_values_type_raises_error(self):
        """Test that invalid series values type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ChartData(data={"Series 1": "invalid"})
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "list_type"
    
    def test_invalid_series_value_type_raises_error(self):
        """Test that invalid series value type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ChartData(data={"Series 1": [1, 2, "invalid", 4]})
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "int_parsing"  # Updated for Pydantic v2
    
    def test_model_json_schema(self):
        """Test that the model has expected JSON schema."""
        schema = ChartData.model_json_schema()
        
        assert "data" in schema["properties"]
        assert schema["properties"]["data"]["type"] == "object"
        assert "example" in schema
        
        example = schema["example"]
        assert "data" in example
        assert isinstance(example["data"], dict)
    
    def test_model_serialization(self):
        """Test model serialization to dict and JSON."""
        data = {
            "data": {
                "Test Series": [1, 2, 3]
            }
        }
        
        chart_data = ChartData(**data)
        
        # Test dict serialization
        assert chart_data.model_dump() == data
        
        # Test JSON serialization
        json_str = chart_data.model_dump_json()
        assert '"data":' in json_str
        assert '"Test Series"' in json_str
    
    def test_unicode_series_names(self):
        """Test chart data with unicode series names."""
        data = {
            "data": {
                "收益": [100, 200, 300],
                "Прибыль": [150, 250, 350],
                "العائدات": [50, 100, 150]
            }
        }
        
        chart_data = ChartData(**data)
        
        assert chart_data.data == data["data"]
        assert len(chart_data.data) == 3