import os
import uuid
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import pygal
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/charts", StaticFiles(directory="charts"), name="charts")


class ChartData(BaseModel):
    data: Dict[str, List[int]]


@app.post(
    "/chart",
    summary="Create Chart",
    description="Creates a chart based on the provided data and type."
)
async def chart(
        chart_data: ChartData,
        chart_type: str = Query(..., description="Type of the chart", regex="^(bar|pie|line|area)$"),
        title: Optional[str] = Query(None, description="Title of the chart")
):
    """
    Create a chart with the specified data and type.

    - **chart_data**: The data to be used in the chart, structured as a dictionary of lists of floats.
      Example:
        {
            "data": {
                "label1": [1, 2, 3, 4],
                "label2": [5, 6, 7]
            }
        }

    - **chart_type**: The type of chart to create. Must be one of 'bar', 'pie', 'line', or 'area'.
    - **title**: (Optional) The title of the chart.

    This endpoint generates a chart based on the input data and type provided by the user.

    Returns:
    - An SVG image of the generated chart.
    """
    chart = None

    # Create the appropriate chart type
    if chart_type == "bar":
        chart = pygal.Bar()
    elif chart_type == "pie":
        chart = pygal.Pie()
    elif chart_type == "line":
        chart = pygal.Line()
    elif chart_type == "area":
        chart = pygal.StackedLine(fill=True)
    else:
        raise HTTPException(status_code=400, detail="Invalid chart type provided")

    # Set the title if provided
    if title:
        chart.title = title

    # Add data to the chart
    for key, values in chart_data.data.items():
        chart.add(key, values)

    # Render the chart to SVG
    svg_data = chart.render()

    # Generate a unique filename
    svg_filename = f"{uuid.uuid4()}.svg"
    svg_dir = "../charts"  # Directory to save SVG files
    os.makedirs(svg_dir, exist_ok=True)
    svg_path = os.path.join(svg_dir, svg_filename)

    # Save the SVG file
    with open(svg_path, "wb") as f:
        f.write(svg_data)

    # Construct the full URL to the SVG file
    full_url = f"https://fast.three60.click/{svg_dir}/{svg_filename}"

    # Return the full URL in the response
    return JSONResponse(content={"url": full_url})
