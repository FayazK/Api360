from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import UploadFile

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
except ImportError:
    raise ImportError("docling library is required. Install with: pip install docling")

from app.services.common.exceptions import ValidationError, ServiceError


class DoclingExtractor:
    """
    A unified document processor using the Docling library.
    It extracts content from various file formats and converts it to Markdown.
    """

    SUPPORTED_MIMETYPES = {
        # Text documents
        'text/plain': 'txt',
        'text/html': 'html',
        'text/csv': 'csv',
        'text/markdown': 'md',
        'text/rtf': 'rtf',
        # Microsoft Office
        'application/msword': 'doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/vnd.ms-excel': 'xls',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
        'application/vnd.ms-powerpoint': 'ppt',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
        # PDF
        'application/pdf': 'pdf',
        # OpenOffice/LibreOffice
        'application/vnd.oasis.opendocument.text': 'odt',
        'application/vnd.oasis.opendocument.presentation': 'odp',
        'application/vnd.oasis.opendocument.spreadsheet': 'ods',
        # Email (best-effort)
        'message/rfc822': 'eml',
        'application/vnd.ms-outlook': 'msg',
        # Images
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/tiff': 'tiff',
        'image/bmp': 'bmp',
        'image/gif': 'gif',
    }

    def __init__(self):
        """Initialize the DoclingExtractor."""
        pass

    async def extract_text(self, file: UploadFile, use_ocr: bool = False) -> Dict[str, Any]:
        """
        Extract text and metadata from a document and convert to markdown.

        Args:
            file (UploadFile): The uploaded file to process

        Returns:
            Dict containing extracted markdown content and metadata
        """
        try:
            mime_type = file.content_type
            if not mime_type or mime_type not in self.SUPPORTED_MIMETYPES:
                raise ValidationError(
                    f"Unsupported file type: {mime_type}.",
                    field="content_type",
                    value=mime_type,
                )

            # Read file bytes
            content = await file.read()

            # Use filename hint for better parsing
            filename = file.filename or f"document.{self.SUPPORTED_MIMETYPES[mime_type]}"

            # Configure Docling document converter
            converter = DocumentConverter()

            # Convert document from bytes
            result = converter.convert_single_document(content, filename=filename)

            # Extract outputs
            doc = result.document
            markdown_content = doc.export_to_markdown()
            text_content = doc.export_to_text()

            # Basic metadata (Docling exposes more via doc.metadata; keep schema stable)
            metadata: Dict[str, Any] = {
                "filename": filename,
                "mime_type": mime_type,
                "extraction_timestamp": datetime.now().isoformat(),
            }

            # Attach docling metadata if available without over-shaping
            try:
                dl_meta = getattr(doc, "metadata", None)
                if dl_meta:
                    # Convert to a plain dict conservatively
                    metadata["docling_metadata"] = dict(dl_meta) if hasattr(dl_meta, "items") else dl_meta
            except Exception:
                # Metadata attachment is best-effort
                pass

            return {
                "text": text_content or markdown_content,
                "markdown": markdown_content or text_content,
                "metadata": metadata,
            }

        except ValidationError:
            raise
        except Exception as e:
            raise ServiceError(
                f"Error processing document '{getattr(file, 'filename', 'unknown')}': {str(e)}",
                error_code="DOCUMENT_EXTRACTION_FAILED",
            )

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported document formats categorized by type."""
        categories = {
            "text": ["text/plain", "text/html", "text/csv", "text/markdown", "text/rtf"],
            "microsoft_office": [
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-powerpoint",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ],
            "pdf": ["application/pdf"],
            "open_office": [
                "application/vnd.oasis.opendocument.text",
                "application/vnd.oasis.opendocument.presentation",
                "application/vnd.oasis.opendocument.spreadsheet",
            ],
            "email": ["message/rfc822", "application/vnd.ms-outlook"],
            "images": ["image/jpeg", "image/png", "image/tiff", "image/bmp", "image/gif"],
        }

        return {
            "supported_formats": self.SUPPORTED_MIMETYPES,
            "categories": categories,
            "total_supported": len(self.SUPPORTED_MIMETYPES),
        }

    async def extract_text_from_url(
        self,
        url: str,
        filename: Optional[str] = None,
        use_ocr: bool = False,
    ) -> Dict[str, Any]:
        """Fetch a remote document by URL and extract text/markdown.

        Args:
            url: Remote URL to fetch document bytes from.
            filename: Optional filename hint to help Docling identify the format.
            use_ocr: Enable OCR in the pipeline configuration.
        """
        import httpx
        from urllib.parse import urlparse

        if not url:
            raise ValidationError("URL is required", field="url", value=url)

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url)
                status = resp.status_code
                if status != 200:
                    raise ServiceError(
                        f"Failed to fetch URL (status {status})",
                        error_code="REMOTE_FETCH_FAILED",
                        details={"status": status, "url": url},
                    )
                content = resp.content
                content_type = resp.headers.get("content-type", "").split(";")[0].strip()

            # Determine filename and mime type
            resolved_filename = (
                filename
                or (urlparse(url).path.rsplit("/", 1)[-1] if urlparse(url).path else None)
                or "document"
            )
            mime_type = content_type or None
            # Best-effort validation: if we know MIME, ensure it's in supported set
            if mime_type and (mime_type not in self.SUPPORTED_MIMETYPES):
                raise ValidationError(
                    f"Unsupported content-type from URL: {mime_type}",
                    field="content_type",
                    value=mime_type,
                )

            # Configure document converter
            converter = DocumentConverter()
            result = converter.convert_single_document(content, filename=resolved_filename)

            doc = result.document
            markdown_content = doc.export_to_markdown()
            text_content = doc.export_to_text()

            metadata: Dict[str, Any] = {
                "filename": resolved_filename,
                "mime_type": mime_type or "",
                "source_url": url,
                "extraction_timestamp": datetime.now().isoformat(),
            }
            try:
                dl_meta = getattr(doc, "metadata", None)
                if dl_meta:
                    metadata["docling_metadata"] = dict(dl_meta) if hasattr(dl_meta, "items") else dl_meta
            except Exception:
                pass

            return {
                "text": text_content or markdown_content,
                "markdown": markdown_content or text_content,
                "metadata": metadata,
            }
        except ValidationError:
            raise
        except ServiceError:
            raise
        except httpx.RequestError as e:
            raise ServiceError(
                f"Network error fetching URL: {str(e)}",
                error_code="REMOTE_FETCH_ERROR",
                details={"url": url},
            )
        except Exception as e:
            raise ServiceError(
                f"Error processing remote document: {str(e)}",
                error_code="DOCUMENT_EXTRACTION_FAILED",
            )
