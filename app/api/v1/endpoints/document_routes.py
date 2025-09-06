from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import List
from pathlib import Path
import asyncio
from app.schemas.documents.extraction import (
    ExtractionResponse, 
    BatchExtractionResponse, 
    SupportedFormatsResponse,
    ExtractedDocument
)
from app.services.documents.unstructured_extractor import UnstructuredExtractor

router = APIRouter()

# Initialize document extractor
document_extractor = UnstructuredExtractor()


@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
        file: UploadFile = File(...),
        background_tasks: BackgroundTasks = None
) -> JSONResponse:
    """
    Extract text and metadata from a document and convert to markdown format.

    Args:
        file: The document file to process
        background_tasks: FastAPI background tasks

    Returns:
        JSONResponse containing extracted text, markdown content, and enhanced metadata
    """
    try:
        # Extract document content using unstructured library
        # Run in thread pool to avoid blocking the event loop
        result = await run_in_threadpool(
            lambda: asyncio.run(document_extractor.extract_text(file))
        )

        # Create ExtractedDocument response
        extracted_doc = ExtractedDocument(
            filename=result["metadata"]["filename"],
            mime_type=result["metadata"]["mime_type"],
            text=result["text"],
            markdown=result["markdown"],
            metadata=result["metadata"]
        )

        # Clean up temporary files in background
        if background_tasks:
            background_tasks.add_task(cleanup_temp_files)

        return JSONResponse(
            content={
                "status": "success",
                "data": extracted_doc.model_dump(),
                "message": "Document extracted and converted to markdown successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@router.post("/batch-extract", response_model=BatchExtractionResponse)
async def batch_extract_documents(
        files: List[UploadFile] = File(...),
        background_tasks: BackgroundTasks = None
) -> JSONResponse:
    """
    Extract text and metadata from multiple documents in parallel and convert to markdown.

    Args:
        files: List of document files to process
        background_tasks: FastAPI background tasks

    Returns:
        JSONResponse containing extraction results for all documents
    """
    try:
        # Process documents in parallel using thread pool
        async def process_single_file(file: UploadFile):
            return await run_in_threadpool(
                lambda: asyncio.run(document_extractor.extract_text(file))
            )

        extraction_tasks = [process_single_file(file) for file in files]
        results = await asyncio.gather(*extraction_tasks, return_exceptions=True)

        # Convert results to ExtractedDocument objects, handling exceptions
        extracted_docs = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"File {files[i].filename}: {str(result)}")
            else:
                try:
                    extracted_doc = ExtractedDocument(
                        filename=result["metadata"]["filename"],
                        mime_type=result["metadata"]["mime_type"],
                        text=result["text"],
                        markdown=result["markdown"],
                        metadata=result["metadata"]
                    )
                    extracted_docs.append(extracted_doc)
                except Exception as e:
                    errors.append(f"File {files[i].filename}: Failed to create response - {str(e)}")

        # Clean up temporary files in background
        if background_tasks:
            background_tasks.add_task(cleanup_temp_files)

        response_data = {
            "status": "success" if not errors else "partial_success",
            "data": [doc.model_dump() for doc in extracted_docs],
            "message": f"Successfully processed {len(extracted_docs)} documents" + 
                      (f", with {len(errors)} errors: {'; '.join(errors)}" if errors else "")
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing documents: {str(e)}"
        )


@router.get("/supported-formats", response_model=SupportedFormatsResponse)
async def get_supported_formats() -> JSONResponse:
    """Get list of supported document formats with categories and enhanced details."""
    formats_info = document_extractor.get_supported_formats()
    
    return JSONResponse(content=formats_info)


async def cleanup_temp_files():
    """Clean up temporary files created during extraction."""
    temp_dir = Path("temp")
    if temp_dir.exists():
        for file in temp_dir.glob("*"):
            try:
                file.unlink()
            except Exception:
                pass