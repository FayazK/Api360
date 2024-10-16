# app/utils/document_converter.py

import pypandoc
import pdfplumber
import os
from fastapi import UploadFile, HTTPException
from typing import Optional


async def convert_to_markdown(file: UploadFile) -> str:
    try:
        content = await file.read()
        extension = os.path.splitext(file.filename)[1].lower()

        if extension == '.pdf':
            return await convert_pdf_to_markdown(content)
        elif extension in ['.doc', '.docx']:
            return await convert_doc_to_markdown(content, extension)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {extension}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting file: {str(e)}")


async def convert_pdf_to_markdown(content: bytes) -> str:
    try:
        with pdfplumber.open(content) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting PDF: {str(e)}")


async def convert_doc_to_markdown(content: bytes, extension: str) -> str:
    try:
        input_format = 'docx' if extension == '.docx' else 'doc'
        output = pypandoc.convert_text(content, 'md', format=input_format)
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting DOC/DOCX: {str(e)}")