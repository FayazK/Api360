from typing import Dict, Any, Optional
import pygal
from app.schemas.chart import ChartData
from app.services.common.base_service import BaseService
from app.services.common.exceptions import ValidationError, ServiceError


class ChartService(BaseService):
    
    SUPPORTED_CHART_TYPES = {
        "bar": pygal.Bar,
        "pie": pygal.Pie,
        "line": pygal.Line,
        "area": pygal.StackedLine
    }
    
    def __init__(self):
        super().__init__("ChartService")
    
    async def create_chart(
        self,
        chart_data: ChartData,
        chart_type: str,
        title: Optional[str] = None,
    ) -> bytes:
        try:
            self.log_operation("create_chart", {"chart_type": chart_type})
            
            self._validate_chart_type(chart_type)
            
            chart = self._create_chart_instance(chart_type)
            
            if title:
                chart.title = title
            
            for key, values in chart_data.data.items():
                chart.add(key, values)
            
            svg_data = chart.render()
            return svg_data
            
        except Exception as error:
            self.handle_error(error, "chart creation")
    
    def _validate_chart_type(self, chart_type: str) -> None:
        self.validate_enum_value(
            chart_type,
            list(self.SUPPORTED_CHART_TYPES.keys()),
            "chart_type"
        )
    
    def _create_chart_instance(self, chart_type: str):
        try:
            return self.SUPPORTED_CHART_TYPES[chart_type]()
        except KeyError:
            raise ValidationError(
                f"Unsupported chart type: {chart_type}",
                field="chart_type",
                value=chart_type
            )
    
chart_service = ChartService()


async def create_chart(chart_data: ChartData, chart_type: str, title: str = None) -> bytes:
    return await chart_service.create_chart(chart_data, chart_type, title)
