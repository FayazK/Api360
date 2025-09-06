import pytest
from unittest.mock import Mock, patch
import pygal

from app.services.chart_service import create_chart, ChartService, chart_service
from app.schemas.chart import ChartData
from app.services.common.exceptions import ValidationError


class TestChartService:
    """Test chart service functionality."""
    
    @pytest.fixture
    def service(self):
        """Create a ChartService instance for testing."""
        return ChartService()
    
    def test_validate_chart_type_valid(self, service):
        """Test valid chart type validation."""
        service._validate_chart_type("bar")
        service._validate_chart_type("pie")
        service._validate_chart_type("line")
        service._validate_chart_type("area")
    
    def test_validate_chart_type_invalid(self, service):
        """Test invalid chart type validation raises error."""
        with pytest.raises(ValidationError) as exc_info:
            service._validate_chart_type("invalid_type")
        
        assert "chart_type" in exc_info.value.details["field"]
    
    def test_create_chart_instance_bar(self, service):
        """Test bar chart instance creation."""
        chart = service._create_chart_instance("bar")
        assert isinstance(chart, pygal.Bar)
    
    def test_create_chart_instance_pie(self, service):
        """Test pie chart instance creation."""
        chart = service._create_chart_instance("pie")
        assert isinstance(chart, pygal.Pie)
    
    def test_create_chart_instance_line(self, service):
        """Test line chart instance creation."""
        chart = service._create_chart_instance("line")
        assert isinstance(chart, pygal.Line)
    
    def test_create_chart_instance_area(self, service):
        """Test area chart instance creation."""
        chart = service._create_chart_instance("area")
        assert isinstance(chart, pygal.StackedLine)
    
    def test_create_chart_instance_invalid(self, service):
        """Test invalid chart type raises ValidationError."""
        with pytest.raises(ValidationError):
            service._create_chart_instance("invalid_type")


class TestCreateChart:
    """Test chart creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_chart_without_title(self, sample_chart_data, mock_storage_engine):
        """Test chart creation without title."""
        chart_data = ChartData(**sample_chart_data)
        
        with patch('app.services.chart_service.chart_service._save_chart') as mock_save:
            mock_save.return_value = {"url": "http://test.com/chart.svg", "filename": "chart.svg"}
            
            result = await create_chart(chart_data, "bar")
            
            assert result is not None
            assert result["url"] == "http://test.com/chart.svg"
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_chart_with_title(self, sample_chart_data, mock_storage_engine):
        """Test chart creation with title."""
        chart_data = ChartData(**sample_chart_data)
        
        with patch('app.services.chart_service.chart_service._save_chart') as mock_save:
            mock_save.return_value = {"url": "http://test.com/chart.svg", "filename": "chart.svg"}
            
            result = await create_chart(chart_data, "bar", "Test Chart Title")
            
            assert result is not None
            assert result["url"] == "http://test.com/chart.svg"
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_pie_chart(self, sample_chart_data, mock_storage_engine):
        """Test pie chart creation."""
        chart_data = ChartData(**sample_chart_data)
        
        with patch('app.services.chart_service.chart_service._save_chart') as mock_save:
            mock_save.return_value = {"url": "http://test.com/pie.svg", "filename": "pie.svg"}
            
            result = await create_chart(chart_data, "pie", "Pie Chart")
            
            assert result is not None
            assert result["url"] == "http://test.com/pie.svg"
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_line_chart(self, sample_chart_data, mock_storage_engine):
        """Test line chart creation."""
        chart_data = ChartData(**sample_chart_data)
        
        with patch('app.services.chart_service.chart_service._save_chart') as mock_save:
            mock_save.return_value = {"url": "http://test.com/line.svg", "filename": "line.svg"}
            
            result = await create_chart(chart_data, "line", "Line Chart")
            
            assert result is not None
            assert result["url"] == "http://test.com/line.svg"
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_chart_with_multiple_series(self, mock_storage_engine):
        """Test chart creation with multiple data series."""
        chart_data = ChartData(data={
            "Q1": [100, 200, 150],
            "Q2": [150, 250, 200],
            "Q3": [200, 300, 250],
            "Q4": [250, 350, 300]
        })
        
        with patch('app.services.chart_service.chart_service._save_chart') as mock_save:
            mock_save.return_value = {"url": "http://test.com/multi.svg", "filename": "multi.svg"}
            
            result = await create_chart(chart_data, "bar", "Quarterly Data")
            
            assert result is not None
            assert result["url"] == "http://test.com/multi.svg"
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_chart_invalid_type_raises_error(self, sample_chart_data):
        """Test that invalid chart type raises ValidationError."""
        chart_data = ChartData(**sample_chart_data)
        
        with pytest.raises(ValidationError):
            await create_chart(chart_data, "invalid_type")
    
    @pytest.mark.asyncio 
    async def test_create_chart_empty_data(self, mock_storage_engine):
        """Test chart creation with empty data."""
        chart_data = ChartData(data={})
        
        with patch('app.services.chart_service.chart_service._save_chart') as mock_save:
            mock_save.return_value = {"url": "http://test.com/empty.svg", "filename": "empty.svg"}
            
            result = await create_chart(chart_data, "bar", "Empty Chart")
            
            assert result is not None
            assert result["url"] == "http://test.com/empty.svg"
            mock_save.assert_called_once()