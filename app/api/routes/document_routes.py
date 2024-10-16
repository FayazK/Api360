# app/api/routes/document_routes.py

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.utils.document_converter import convert_to_markdown

router = APIRouter()


@router.post("/doc-to-md", summary="Convert PDF/DOC/DOCX to Markdown")
async def convert_document_to_markdown(file: UploadFile = File(...)):
    if file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    markdown_content = await convert_to_markdown(file)
    return {"markdown_content": markdown_content}