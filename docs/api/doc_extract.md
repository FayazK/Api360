# Document Extraction API

This API extracts text and markdown from local uploads or remote URLs using the Docling SDK. OCR can be enabled per request. Responses include the extracted `text`, `markdown`, and `metadata`.

- Base URL: `/api/documents`
- Content types: `multipart/form-data` for file uploads, `application/json` for JSON responses
- Default behavior: OCR is disabled unless `use_ocr=true`

## Endpoints

### POST `/extract`
Extract a single uploaded document.

- Form fields:
  - `file`: required, the document to parse
- Query params:
  - `use_ocr` (bool, default false): enable OCR for scanned documents

Example (curl):
```
curl -sS -X POST \
  -F "file=@sample.pdf" \
  "http://localhost:8000/api/documents/extract?use_ocr=true"
```

Success response (200):
```
{
  "status": "success",
  "data": {
    "filename": "sample.pdf",
    "mime_type": "application/pdf",
    "text": "...plain text...",
    "markdown": "# Title\n...content...",
    "metadata": {
      "filename": "sample.pdf",
      "mime_type": "application/pdf",
      "extraction_timestamp": "2025-09-09T12:34:56.789012",
      "docling_metadata": { "...": "..." }
    }
  },
  "message": "Document extracted and converted to markdown successfully"
}
```

Errors:
- 400: validation error (e.g., unsupported content-type)
- 500: unexpected service error

### POST `/batch-extract`
Extract multiple uploaded documents in parallel.

- Form fields (repeat):
  - `files`: required, multiple documents to parse
- Query params:
  - `use_ocr` (bool, default false): enable OCR for all files

Example (curl):
```
curl -sS -X POST \
  -F "files=@doc1.pdf" -F "files=@doc2.docx" \
  "http://localhost:8000/api/documents/batch-extract?use_ocr=false"
```

Success response (200):
```
{
  "status": "success" | "partial_success",
  "data": [
    {
      "filename": "doc1.pdf",
      "mime_type": "application/pdf",
      "text": "...",
      "markdown": "...",
      "metadata": { "filename": "doc1.pdf", "mime_type": "application/pdf", "extraction_timestamp": "..." }
    },
    {
      "filename": "doc2.docx",
      "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text": "...",
      "markdown": "...",
      "metadata": { "filename": "doc2.docx", "mime_type": "application/...", "extraction_timestamp": "..." }
    }
  ],
  "message": "Successfully processed 2 documents"
}
```

Errors:
- 500: unexpected batch processing error

### POST `/extract-url`
Fetch and extract a remote document by URL.

- Query params:
  - `url` (string, required): remote document URL
  - `filename` (string, optional): filename hint to improve parsing
  - `use_ocr` (bool, default false): enable OCR

Example (curl):
```
curl -sS -X POST \
  "http://localhost:8000/api/documents/extract-url?url=https://example.com/report.pdf&use_ocr=true"
```

Success response (200):
```
{
  "status": "success",
  "data": {
    "filename": "report.pdf",
    "mime_type": "application/pdf",
    "text": "...",
    "markdown": "...",
    "metadata": {
      "filename": "report.pdf",
      "mime_type": "application/pdf",
      "source_url": "https://example.com/report.pdf",
      "extraction_timestamp": "..."
    }
  },
  "message": "Remote document extracted and converted to markdown successfully"
}
```

Errors:
- 400: validation error (e.g., unsupported `content-type` from URL)
- 502: remote fetch or upstream error (e.g., non-200 response)
- 500: unexpected service error

### GET `/supported-formats`
List supported MIME types and categories.

Example:
```
curl -sS "http://localhost:8000/api/documents/supported-formats"
```

Response (200):
```
{
  "supported_formats": {
    "application/pdf": "pdf",
    "text/plain": "txt",
    "image/png": "png",
    "...": "..."
  },
  "categories": {
    "text": ["text/plain", "text/html", "text/csv", "text/markdown", "text/rtf"],
    "microsoft_office": ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "..."],
    "pdf": ["application/pdf"],
    "open_office": ["application/vnd.oasis.opendocument.text", "..."],
    "email": ["message/rfc822", "application/vnd.ms-outlook"],
    "images": ["image/jpeg", "image/png", "image/tiff", "image/bmp", "image/gif"]
  },
  "total_supported": 17
}
```

## Notes & Limits

- OCR: Disabled by default. Enable per request with `use_ocr=true`. Requires Docling OCR support (installed by default in this project via `docling[all]`).
- File size: Uploads are limited by server settings. Large files may return `413 Payload Too Large`.
- Content types: If the content type is unknown, provide a `filename` hint (e.g., `filename=report.pdf`) for `/extract-url`.
- Performance: For very large documents, consider disabling heavy features or splitting documents.

