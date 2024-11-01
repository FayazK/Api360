import os
import uuid
from typing import Optional

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


import os
import uuid
from fastapi.responses import JSONResponse
from app.core.config import settings
from pathlib import Path


def save_pdf(pdf_data: bytes, filename: Optional[str] = None) -> JSONResponse:
    """
    Save the PDF data to a file and return the URL.

    Args:
    pdf_data (bytes): The PDF content to save
    filename (Optional[str]): Optional custom filename

    Returns:
    JSONResponse: A response containing the URL of the saved PDF file
    """
    # Generate filename if not provided
    if not filename:
        filename = f"{uuid.uuid4()}.pdf"
    elif not filename.endswith('.pdf'):
        filename = f"{filename}.pdf"

    # Ensure filename is URL-safe
    filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.')).lower()

    # Create directory if it doesn't exist
    pdf_dir = Path(settings.CHART_SAVE_DIR)  # Reusing the chart directory setting
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # Save the PDF file
    pdf_path = pdf_dir / filename

    with open(pdf_path, "wb") as f:
        f.write(pdf_data)

    # Construct the URL path
    url_path = f"{settings.CHART_URL_PATH}/{filename}"

    return JSONResponse(content={"url": url_path})