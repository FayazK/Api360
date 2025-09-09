from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List, Optional
import asyncio
from app.schemas.documents.extraction import (
    ExtractionResponse,
    BatchExtractionResponse,
    SupportedFormatsResponse,
    ExtractedDocument,
)
from app.services.documents.docling_extractor import DoclingExtractor
from app.services.common.exceptions import ValidationError, ServiceError

router = APIRouter()

# Initialize document extractor
document_extractor = DoclingExtractor()


@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    use_ocr: bool = Query(False, description="Enable OCR for scanned documents"),
):
    """
    Extract text and metadata from a document and convert to markdown format.

    Args:
        file: The document file to process
        background_tasks: FastAPI background tasks

    Returns:
        JSONResponse containing extracted text, markdown content, and enhanced metadata
    """
    try:
        # Extract document content using Docling library (async)
        result = await document_extractor.extract_text(file, use_ocr=use_ocr)

        # Create ExtractedDocument response
        extracted_doc = ExtractedDocument(
            filename=result["metadata"]["filename"],
            mime_type=result["metadata"]["mime_type"],
            text=result["text"],
            markdown=result["markdown"],
            metadata=result["metadata"]
        )

        return ExtractionResponse(
            status="success",
            data=extracted_doc,
            message="Document extracted and converted to markdown successfully",
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"error": e.error_code or "VALIDATION_ERROR", "message": e.message, "details": e.details})
    except ServiceError as e:
        raise HTTPException(status_code=500, detail={"error": e.error_code or "SERVICE_ERROR", "message": e.message, "details": e.details})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.post("/batch-extract", response_model=BatchExtractionResponse)
async def batch_extract_documents(
    files: List[UploadFile] = File(...),
    use_ocr: bool = Query(False, description="Enable OCR for scanned documents (applies to all files)"),
):
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
            return await document_extractor.extract_text(file, use_ocr=use_ocr)

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

        return BatchExtractionResponse(
            status="success" if not errors else "partial_success",
            data=extracted_docs,
            message=(
                f"Successfully processed {len(extracted_docs)} documents"
                + (f", with {len(errors)} errors: {'; '.join(errors)}" if errors else "")
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing documents: {str(e)}"
        )


@router.get("/supported-formats", response_model=SupportedFormatsResponse)
async def get_supported_formats() -> SupportedFormatsResponse:
    """Get list of supported document formats with categories and enhanced details."""
    formats_info = document_extractor.get_supported_formats()

    return SupportedFormatsResponse(**formats_info)


@router.post("/extract-url", response_model=ExtractionResponse)
async def extract_document_from_url(
    url: str = Query(..., description="Remote document URL"),
    filename: Optional[str] = Query(None, description="Optional filename hint"),
    use_ocr: bool = Query(False, description="Enable OCR for scanned documents"),
):
    """Fetch a remote document by URL and extract markdown/text using Docling."""
    try:
        result = await document_extractor.extract_text_from_url(url=url, filename=filename, use_ocr=use_ocr)

        extracted_doc = ExtractedDocument(
            filename=result["metadata"].get("filename") or "document",
            mime_type=result["metadata"].get("mime_type", ""),
            text=result["text"],
            markdown=result["markdown"],
            metadata=result["metadata"],
        )

        return ExtractionResponse(
            status="success",
            data=extracted_doc,
            message="Remote document extracted and converted to markdown successfully",
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"error": e.error_code or "VALIDATION_ERROR", "message": e.message, "details": e.details})
    except ServiceError as e:
        raise HTTPException(status_code=502, detail={"error": e.error_code or "SERVICE_ERROR", "message": e.message, "details": e.details})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing remote document: {str(e)}")
