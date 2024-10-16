import pygal
from app.schemas.chart import ChartData
from app.utils.helpers import save_svg


async def create_chart(chart_data: ChartData, chart_type: str, title: str = None):
    chart = get_chart_instance(chart_type)
    if title:
        chart.title = title
    for key, values in chart_data.data.items():
        chart.add(key, values)
    svg_data = chart.render()
    return save_svg(svg_data)


def get_chart_instance(chart_type: str):
    chart_types = {
        "bar": pygal.Bar,
        "pie": pygal.Pie,
        "line": pygal.Line,
        "area": pygal.StackedLine
    }
    return chart_types[chart_type]()