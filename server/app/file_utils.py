"""File processing utilities"""

import io
import os
from typing import Optional

import aiofiles
import aiohttp
from app.config import settings
from app.utils import sanitize_text
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

    # Sanitize extracted content to remove problematic characters
    content = sanitize_text(content)

    return title, content


async def fetch_url_content(url: str) -> tuple[str, str, str]:
    """Fetch content from URL and convert to markdown if HTML

    Returns:
        tuple of (title, content, detected_type)
    """

    # Special handling for Xiaohongshu explore pages using included spider
    try:
        if "xiaohongshu.com" in url and "/explore/" in url:
            # Use the utility wrapper which imports spider_xhs low-level APIs safely
            from app.spiders.xhs import fetch_xhs_note  # type: ignore

            success, msg, note_info = fetch_xhs_note(url)

            if success and note_info:
                # Build a readable content string from note_info
                title = note_info.get("title") or url.split("/")[-1]
                parts = [f"# {title}", ""]
                desc = note_info.get("desc")
                # Include author information
                author = note_info.get("nickname")
                home = note_info.get("home_url")
                if author:
                    author_line = f"作者: {author}"
                    if home:
                        author_line = f"{author_line} ({home})"
                    parts.append(author_line)
                    parts.append("")
                if desc:
                    parts.append(desc)
                    parts.append("")

                # Append metadata
                meta_lines = []
                for k in [
                    "liked_count",
                    "collected_count",
                    "comment_count",
                    "share_count",
                    "upload_time",
                ]:
                    if note_info.get(k) is not None:
                        meta_lines.append(f"{k}: {note_info.get(k)}")
                if meta_lines:
                    parts.append("---")
                    parts.extend(meta_lines)

                content = "\n".join(parts)
                content = sanitize_text(content)
                return title, content, "xhs"
    except Exception as e:
        print(
            f"Xiaohongshu spider failed, falling back to normal URL fetching. Error: {e}"
        )
        # If anything failed with spider, we fall back to normal fetching below
        pass

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            content_bytes = await response.read()

            # Handle PDF
            if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                title = url.split("/")[-1].replace(".pdf", "")
                content = await extract_text_from_pdf(content_bytes)
                return title, content, "pdf"

            # Handle HTML - convert to markdown
            elif "text/html" in content_type:
                from markdownify import markdownify as md

                html_content = content_bytes.decode("utf-8", errors="ignore")
                content = md(html_content, heading_style="ATX")

                # Try to extract title from HTML
                import re

                title_match = re.search(
                    r"<title>(.*?)</title>", html_content, re.IGNORECASE
                )
                title = title_match.group(1) if title_match else url.split("/")[-1]

                return title, content, "md"

            # Handle plain text/markdown
            else:
                content = content_bytes.decode("utf-8", errors="ignore")
                title = url.split("/")[-1]
                return title, content, "text"
