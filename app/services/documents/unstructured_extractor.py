from typing import Dict, Any, IO, List
from datetime import datetime
from fastapi import UploadFile
import uuid
from pathlib import Path

try:
    from unstructured.partition.auto import partition
    from unstructured.staging.base import elements_to_md
    from unstructured.documents.elements import Element, Title
except ImportError:
    raise ImportError("unstructured library is required. Install with: pip install 'unstructured[all-docs]'")


from app.services.common.exceptions import ValidationError, ServiceError


class UnstructuredExtractor:
    """
    A unified document processor using the 'unstructured' library.
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
        # Email
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
        """Initialize the UnstructuredExtractor."""
        pass

    def _extract_metadata(self, elements: List[Element], file_name: str, content_type: str) -> Dict[str, Any]:
        """Helper function to aggregate metadata from document elements."""
        
        # Find the first element of type Title to use as the document title
        doc_title = next((el.text for el in elements if isinstance(el, Title)), None)

        # Extract metadata from the first element if available
        first_element_metadata = elements[0].metadata.to_dict() if elements else {}
        
        # Count different element types
        element_counts = {}
        for element in elements:
            element_type = type(element).__name__
            element_counts[element_type] = element_counts.get(element_type, 0) + 1

        # Extract page information
        pages = set()
        languages = set()
        for element in elements:
            if hasattr(element.metadata, 'page_number') and element.metadata.page_number:
                pages.add(element.metadata.page_number)
            if hasattr(element.metadata, 'languages') and element.metadata.languages:
                languages.update(element.metadata.languages)

        return {
            "filename": file_name,
            "mime_type": content_type,
            "title": doc_title,
            "page_count": len(pages) if pages else None,
            "pages": sorted(list(pages)) if pages else None,
            "languages": list(languages) if languages else None,
            "element_counts": element_counts,
            "total_elements": len(elements),
            "first_element_metadata": first_element_metadata,
            "extraction_timestamp": datetime.now().isoformat()
        }

    async def extract_text(self, file: UploadFile) -> Dict[str, Any]:
        """
        Extract text and metadata from a document and convert to markdown.

        Args:
            file (UploadFile): The uploaded file to process

        Returns:
            Dict containing extracted markdown content and metadata
        """
        try:
            # Validate file type
            mime_type = file.content_type
            if not mime_type or mime_type not in self.SUPPORTED_MIMETYPES:
                raise ValidationError(
                    f"Unsupported file type: {mime_type}.",
                    field="content_type",
                    value=mime_type,
                )

            # Use storage engine for temporary file handling
            from app.core.storage_engine import get_storage_engine

            content = await file.read()
            storage = get_storage_engine()

            # Create temporary file with storage engine
            file_extension = self.SUPPORTED_MIMETYPES[mime_type]

            with storage.temp_file(suffix=f".{file_extension}") as (temp_path, temp_fs):
                # Write content to temp file
                with temp_fs.open(temp_path, 'wb') as f:
                    f.write(content)

                # Reset file position for unstructured
                await file.seek(0)

                # Partition the document using unstructured
                elements = partition(
                    file=file.file,
                    file_filename=file.filename,
                    content_type=mime_type,
                    strategy="auto",
                    include_page_breaks=True,
                )

                # Convert elements to markdown
                markdown_content = elements_to_md(elements)

                # Extract metadata
                metadata = self._extract_metadata(elements, file.filename, mime_type)

                return {
                    "text": markdown_content,
                    "markdown": markdown_content,
                    "metadata": metadata,
                }

        except ValidationError:
            raise
        except Exception as e:
            raise ServiceError(
                f"Error processing document '{file.filename}': {str(e)}",
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
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            ],
            "pdf": ["application/pdf"],
            "open_office": [
                "application/vnd.oasis.opendocument.text",
                "application/vnd.oasis.opendocument.presentation",
                "application/vnd.oasis.opendocument.spreadsheet"
            ],
            "email": ["message/rfc822", "application/vnd.ms-outlook"],
            "images": ["image/jpeg", "image/png", "image/tiff", "image/bmp", "image/gif"]
        }
        
        return {
            "supported_formats": self.SUPPORTED_MIMETYPES,
            "categories": categories,
            "total_supported": len(self.SUPPORTED_MIMETYPES)
        }
