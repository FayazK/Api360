from fastapi import APIRouter, HTTPException
from app.schemas.pdf import HTMLToPDFRequest
import app.services.pdf_service as pdf_service
from app.utils.helpers import save_pdf
from anyio import to_thread
from fastapi.responses import Response

router = APIRouter()


@router.post("/generate", summary="Generate PDF from HTML (stores to public and returns URL)")
async def create_pdf(request: HTMLToPDFRequest):
    """
    Generate a PDF from HTML content and return its URL.

    Args:
        request (HTMLToPDFRequest): The HTML content and optional filename

    Returns:
        JSONResponse containing the URL of the generated PDF
    """
    try:
        pdf_content = await to_thread.run_sync(pdf_service.generate_pdf, request.html_content)
        return save_pdf(pdf_content, request.filename)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )


@router.post("/", summary="Generate PDF and return file")
async def create_pdf_inline(request: HTMLToPDFRequest):
    """Generate a PDF and return it directly as application/pdf with Content-Disposition."""
    try:
        pdf_content = await to_thread.run_sync(pdf_service.generate_pdf, request.html_content)
        filename = request.filename
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
