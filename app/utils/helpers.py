import os
import uuid
from fastapi.responses import JSONResponse

def save_svg(svg_data: bytes) -> JSONResponse:
    """
    Save the SVG data to a file and return the URL.

    Args:
    svg_data (bytes): The SVG content to save.

    Returns:
    JSONResponse: A response containing the URL of the saved SVG file.
    """
    # Generate a unique filename
    svg_filename = f"{uuid.uuid4()}.svg"
    svg_dir = "static/charts"  # Directory to save SVG files
    os.makedirs(svg_dir, exist_ok=True)
    svg_path = os.path.join(svg_dir, svg_filename)

    # Save the SVG file
    with open(svg_path, "wb") as f:
        f.write(svg_data)

    # Construct the full URL to the SVG file
    # Note: In a production environment, you'd want to use a configurable base URL
    full_url = f"/static/charts/{svg_filename}"

    # Return the full URL in the response
    return JSONResponse(content={"url": full_url})