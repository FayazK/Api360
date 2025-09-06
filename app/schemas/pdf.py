from pydantic import BaseModel, Field

class HTMLToPDFRequest(BaseModel):
    html_content: str = Field(..., description="HTML content to convert to PDF")
    filename: str = Field(..., description="Filename for the PDF (will be suffixed with .pdf if needed)")

    class Config:
        json_schema_extra = {
            "example": {
                "html_content": "<h1>Hello World</h1><p>This is a test PDF</p>",
                "filename": "my-document.pdf"
            }
        }
