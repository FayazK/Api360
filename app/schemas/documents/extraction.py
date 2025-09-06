from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class ExtractedDocument(BaseModel):
    filename: str
    mime_type: str
    text: str
    markdown: str  # New field for markdown content
    metadata: Dict[str, Any]

class EnhancedMetadata(BaseModel):
    filename: str
    mime_type: str
    title: Optional[str] = None
    page_count: Optional[int] = None
    pages: Optional[List[int]] = None
    languages: Optional[List[str]] = None
    element_counts: Dict[str, int] = {}
    total_elements: int = 0
    first_element_metadata: Dict[str, Any] = {}
    extraction_timestamp: str

class ExtractionResponse(BaseModel):
    status: str
    data: ExtractedDocument
    message: str

class BatchExtractionResponse(BaseModel):
    status: str
    data: List[ExtractedDocument]
    message: str

class SupportedFormatsResponse(BaseModel):
    supported_formats: Dict[str, str]
    categories: Dict[str, List[str]]
    total_supported: int