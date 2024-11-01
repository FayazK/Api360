from pydantic import BaseModel, Field
from typing import Optional

class HTMLToPDFRequest(BaseModel):
    html_content: str = Field(..., description="HTML content to convert to PDF")
    filename: Optional[str] = Field(None, description="Optional custom filename for the PDF")

    class Config:
        json_schema_extra = {
            "example": {
                "html_content": "<h1>Hello World</h1><p>This is a test PDF</p>",
                "filename": "my-document.pdf"
            }
        }