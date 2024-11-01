from fastapi import APIRouter, HTTPException
from app.schemas.pdf import HTMLToPDFRequest
from app.services.pdf_service import generate_pdf
from app.utils.helpers import save_pdf

router = APIRouter()


@router.post("/generate", summary="Generate PDF from HTML")
async def create_pdf(request: HTMLToPDFRequest):
    """
    Generate a PDF from HTML content and return its URL.

    Args:
        request (HTMLToPDFRequest): The HTML content and optional filename

    Returns:
        JSONResponse containing the URL of the generated PDF
    """
    try:
        # Generate PDF content
        pdf_content = await generate_pdf(request.html_content)

        # Save PDF and get URL
        return save_pdf(pdf_content, request.filename)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )