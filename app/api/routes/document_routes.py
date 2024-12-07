from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
from pathlib import Path
import asyncio

from app.services.document_extractor import DocumentExtractor
from app.schemas.document import ExtractedDocument, ExtractionResponse

router = APIRouter()

# Initialize document extractor
document_extractor = DocumentExtractor(ocr_enabled=True)


@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
        file: UploadFile = File(...),
        enable_ocr: bool = True,
        extract_tables: bool = True,
        extract_metadata: bool = True,
        background_tasks: BackgroundTasks = None
) -> JSONResponse:
    """
    Extract text and metadata from a document.

    Args:
        file: The document file to process
        enable_ocr: Whether to enable OCR for images and scanned PDFs
        extract_tables: Whether to extract tables from documents
        extract_metadata: Whether to extract document metadata
        background_tasks: FastAPI background tasks

    Returns:
        JSONResponse containing extracted text and metadata
    """
    try:
        # Extract document content
        result = await document_extractor.extract_text(
            file=file
        )

        # Clean up temporary files in background
        if background_tasks:
            background_tasks.add_task(cleanup_temp_files)

        return JSONResponse(
            content={
                "status": "success",
                "data": result,
                "message": "Document extracted successfully"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@router.post("/batch-extract")
async def batch_extract_documents(
        files: List[UploadFile] = File(...),
        enable_ocr: bool = True,
        background_tasks: BackgroundTasks = None
) -> JSONResponse:
    """
    Extract text and metadata from multiple documents in parallel.

    Args:
        files: List of document files to process
        enable_ocr: Whether to enable OCR for images and scanned PDFs
        background_tasks: FastAPI background tasks

    Returns:
        JSONResponse containing extraction results for all documents
    """
    try:
        # Process documents in parallel
        extraction_tasks = [
            document_extractor.extract_text(file)
            for file in files
        ]
        results = await asyncio.gather(*extraction_tasks)

        # Clean up temporary files in background
        if background_tasks:
            background_tasks.add_task(cleanup_temp_files)

        return JSONResponse(
            content={
                "status": "success",
                "data": results,
                "message": f"Successfully processed {len(results)} documents"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing documents: {str(e)}"
        )


@router.get("/supported-formats")
async def get_supported_formats() -> JSONResponse:
    """Get list of supported document formats."""
    return JSONResponse(
        content={
            "supported_formats": DocumentExtractor.SUPPORTED_MIMETYPES,
            "ocr_enabled": document_extractor.ocr_enabled
        }
    )


async def cleanup_temp_files():
    """Clean up temporary files created during extraction."""
    temp_dir = Path("temp")
    if temp_dir.exists():
        for file in temp_dir.glob("*"):
            try:
                file.unlink()
            except Exception:
                pass
