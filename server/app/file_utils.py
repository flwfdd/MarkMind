"""File processing utilities"""

import io
import os
from typing import Optional

import aiofiles
from app.config import settings
from pypdf import PdfReader


async def save_upload_file(file_content: bytes, filename: str) -> str:
    """Save uploaded file to disk"""
    os.makedirs(settings.upload_dir, exist_ok=True)
    filepath = os.path.join(settings.upload_dir, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(file_content)

    return filepath


async def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    pdf_file = io.BytesIO(file_content)
    reader = PdfReader(pdf_file)

    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    return text.strip()


async def extract_text_from_markdown(file_content: bytes) -> str:
    """Extract text from Markdown file"""
    return file_content.decode("utf-8")


async def process_file(
    file_content: bytes, filename: str, file_type: str
) -> tuple[str, str]:
    """Process uploaded file and extract text

    Returns:
        tuple of (title, content)
    """
    title = os.path.splitext(filename)[0]

    if file_type == "pdf":
        content = await extract_text_from_pdf(file_content)
    elif file_type == "md":
        content = await extract_text_from_markdown(file_content)
    else:
        # Default to text
        try:
            content = file_content.decode("utf-8")
        except:
            content = file_content.decode("utf-8", errors="ignore")

    return title, content
