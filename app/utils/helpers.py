from typing import Optional

from fastapi.responses import JSONResponse
from app.core.storage_engine import get_storage_engine, StorageType

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
    
    # Use storage engine to save the file
    storage = get_storage_engine()
    file_info = storage.store_bytes(
        data=svg_data,
        category="charts",
        filename=svg_filename,
        content_type="image/svg+xml",
        storage_type=StorageType.PUBLIC
    )

    # Return the full URL in the response
    return JSONResponse(content={"url": file_info["url"]})


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

    # Use storage engine to save the file
    storage = get_storage_engine()
    file_info = storage.store_bytes(
        data=pdf_data,
        category="pdfs",
        filename=filename,
        content_type="application/pdf",
        storage_type=StorageType.PUBLIC
    )

    return JSONResponse(content={"url": file_info["url"]})