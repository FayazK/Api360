import pytest
from unittest.mock import Mock, patch
import pygal

from app.services.chart_service import create_chart, get_chart_instance
from app.schemas.chart import ChartData


class TestGetChartInstance:
    """Test chart instance creation."""
    
    def test_get_bar_chart(self):
        """Test bar chart instance creation."""
        chart = get_chart_instance("bar")
        assert isinstance(chart, pygal.Bar)
    
    def test_get_pie_chart(self):
        """Test pie chart instance creation."""
        chart = get_chart_instance("pie")
        assert isinstance(chart, pygal.Pie)
    
    def test_get_line_chart(self):
        """Test line chart instance creation."""
        chart = get_chart_instance("line")
        assert isinstance(chart, pygal.Line)
    
    def test_get_area_chart(self):
        """Test area chart instance creation."""
        chart = get_chart_instance("area")
        assert isinstance(chart, pygal.StackedLine)
    
    def test_invalid_chart_type(self):
        """Test invalid chart type raises KeyError."""
        with pytest.raises(KeyError):
            get_chart_instance("invalid_type")


class TestCreateChart:
    """Test chart creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_chart_without_title(self, sample_chart_data, mock_storage_engine):
        """Test chart creation without title."""
        chart_data = ChartData(**sample_chart_data)
        
        with patch('app.services.chart_service.save_svg') as mock_save_svg:
            mock_save_svg.return_value = {"url": "http://test.com/chart.svg", "filename": "chart.svg"}
            
            result = await create_chart(chart_data, "bar")
            
            assert result is not None
            assert result["url"] == "http://test.com/chart.svg"
            mock_save_svg.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_chart_with_title(self, sample_chart_data, mock_storage_engine):
        """Test chart creation with title."""
        chart_data = ChartData(**sample_chart_data)
        
        with patch('app.services.chart_service.save_svg') as mock_save_svg:
            mock_save_svg.return_value = {"url": "http://test.com/chart.svg", "filename": "chart.svg"}
            
            result = await create_chart(chart_data, "bar", "Test Chart Title")
            
            assert result is not None
            assert result["url"] == "http://test.com/chart.svg"
            mock_save_svg.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_pie_chart(self, sample_chart_data, mock_storage_engine):
        """Test pie chart creation."""
        chart_data = ChartData(**sample_chart_data)
        
        with patch('app.services.chart_service.save_svg') as mock_save_svg:
            mock_save_svg.return_value = {"url": "http://test.com/pie.svg", "filename": "pie.svg"}
            
            result = await create_chart(chart_data, "pie", "Pie Chart")
            
            assert result is not None
            assert result["url"] == "http://test.com/pie.svg"
            mock_save_svg.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_line_chart(self, sample_chart_data, mock_storage_engine):
        """Test line chart creation."""
        chart_data = ChartData(**sample_chart_data)
        
        with patch('app.services.chart_service.save_svg') as mock_save_svg:
            mock_save_svg.return_value = {"url": "http://test.com/line.svg", "filename": "line.svg"}
            
            result = await create_chart(chart_data, "line", "Line Chart")
            
            assert result is not None
            assert result["url"] == "http://test.com/line.svg"
            mock_save_svg.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_chart_with_multiple_series(self, mock_storage_engine):
        """Test chart creation with multiple data series."""
        chart_data = ChartData(data={
            "Q1": [100, 200, 150],
            "Q2": [150, 250, 200],
            "Q3": [200, 300, 250],
            "Q4": [250, 350, 300]
        })
        
        with patch('app.services.chart_service.save_svg') as mock_save_svg:
            mock_save_svg.return_value = {"url": "http://test.com/multi.svg", "filename": "multi.svg"}
            
            result = await create_chart(chart_data, "bar", "Quarterly Data")
            
            assert result is not None
            assert result["url"] == "http://test.com/multi.svg"
            mock_save_svg.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_chart_invalid_type_raises_error(self, sample_chart_data):
        """Test that invalid chart type raises KeyError."""
        chart_data = ChartData(**sample_chart_data)
        
        with pytest.raises(KeyError):
            await create_chart(chart_data, "invalid_type")
    
    @pytest.mark.asyncio 
    async def test_create_chart_empty_data(self, mock_storage_engine):
        """Test chart creation with empty data."""
        chart_data = ChartData(data={})
        
        with patch('app.services.chart_service.save_svg') as mock_save_svg:
            mock_save_svg.return_value = {"url": "http://test.com/empty.svg", "filename": "empty.svg"}
            
            result = await create_chart(chart_data, "bar", "Empty Chart")
            
            assert result is not None
            assert result["url"] == "http://test.com/empty.svg"
            mock_save_svg.assert_called_once()