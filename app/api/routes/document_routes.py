# app/api/routes/document_routes.py

from fastapi import APIRouter, UploadFile, File
from app.utils.document_converter import convert_to_markdown

router = APIRouter()

@router.post("/convert-to-markdown", summary="Convert PDF/DOC/DOCX to Markdown")
async def convert_document_to_markdown(file: UploadFile = File(...)):
    markdown_content = await convert_to_markdown(file)
    return {"markdown_content": markdown_content}