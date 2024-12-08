from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class ExtractedDocument(BaseModel):
    filename: str
    mime_type: str
    text: str
    metadata: Dict[str, Any]
    extraction_timestamp: datetime

class ExtractionResponse(BaseModel):
    status: str
    data: ExtractedDocument
    message: str