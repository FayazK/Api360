from weasyprint import HTML
from io import BytesIO
from typing import Optional


async def generate_pdf(html_content: str) -> bytes:
    """
    Generate PDF from HTML content.

    Args:
    html_content (str): The HTML content to convert to PDF

    Returns:
    bytes: The generated PDF content
    """
    # Create PDF in memory
    pdf_buffer = BytesIO()

    # Generate PDF from HTML
    HTML(string=html_content).write_pdf(pdf_buffer)

    # Get the PDF content
    pdf_content = pdf_buffer.getvalue()
    pdf_buffer.close()

    return pdf_content