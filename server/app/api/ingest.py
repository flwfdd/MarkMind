"""Ingest API - Document upload and processing"""

import base64
import os
from typing import Optional

from app.database import db
from app.file_utils import fetch_url_content, process_file, save_upload_file
from app.models import (
    ConceptResponse,
    ConfirmImportRequest,
    DocumentCreate,
    DocumentPreview,
    DocumentResponse,
    ExtractedConcept,
    ExtractedRelation,
    ParseRequest,
    ParseResponse,
)
from app.utils import (
    chunk_text,
    extract_concepts,
    generate_summary,
    generate_title_and_summary,
    get_embedding,
    get_embeddings,
    sanitize_text,
)
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("/parse", response_model=ParseResponse)
async def parse_document(request: ParseRequest):
    """
    Parse document from URL or uploaded file
    Returns extracted title, content, and type
    """
    try:
        # Handle URL
        if request.url:
            title, content, doc_type = await fetch_url_content(request.url)
            return ParseResponse(
                title=title, content=content, type=doc_type, url=request.url
            )

        # Handle file upload
        elif request.file_content and request.file_name:
            file_bytes = base64.b64decode(request.file_content)

            # Determine file type
            file_type = request.file_type or "text"
            if not request.file_type:
                ext = os.path.splitext(request.file_name)[1].lower()
                if ext == ".pdf":
                    file_type = "pdf"
                elif ext in [".md", ".markdown"]:
                    file_type = "md"
                elif ext in [".html", ".htm"]:
                    file_type = "html"

            # Process HTML files
            if file_type == "html":
                from markdownify import markdownify as md

                html_content = file_bytes.decode("utf-8", errors="ignore")
                content = md(html_content, heading_style="ATX")
                content = sanitize_text(content)
                title = os.path.splitext(request.file_name)[0]
                file_type = "md"
            else:
                title, content = await process_file(
                    file_bytes, request.file_name, file_type
                )

            # Ensure sanitized output
            content = sanitize_text(content)

            return ParseResponse(title=title, content=content, type=file_type)

        else:
            raise HTTPException(
                status_code=400, detail="Either url or file_content must be provided"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing document: {str(e)}")


@router.post("/preview", response_model=DocumentPreview)
async def preview_document(
    title: Optional[str] = Form(None),
    content: str = Form(...),
    type: str = Form(...),
    url: Optional[str] = Form(None),
):
    """
    Generate document preview with extracted concepts and relationships
    Does not persist to database
    """
    db.connect()

    try:
        # Sanitize content before any LLM calls
        content = sanitize_text(content)

        # Generate title and summary in a single LLM call
        gen_title, summary = await generate_title_and_summary(content)
        # Use generated title preferentially
        preview_title = gen_title or title or "Untitled Document"

        # Get existing concepts
        existing_concepts = db.get_all_concepts()

        # Extract concepts and relationships
        extracted = await extract_concepts(content, preview_title, existing_concepts)
        concepts_data = extracted.get("concepts", [])
        relations_data = extracted.get("relations", [])

        # Format concepts
        concepts = [
            ExtractedConcept(name=c["name"], desc=c["desc"]) for c in concepts_data
        ]

        # Format relations
        relations = [
            ExtractedRelation(
                from_concept=r.get("from", ""),
                to_concept=r.get("to", ""),
                desc=r.get("desc", ""),
            )
            for r in relations_data
        ]

        # Match with existing concepts
        existing_concept_names = {c.get("name", "").lower() for c in existing_concepts}
        matched_existing = [
            ConceptResponse(
                id=str(c.get("id")), name=c.get("name", ""), desc=c.get("desc", "")
            )
            for c in existing_concepts
            if c.get("name", "").lower()
            in [concept.name.lower() for concept in concepts]
        ]

        return DocumentPreview(
            title=preview_title,
            summary=summary,
            content=content,
            type=type,
            url=url if url else None,
            concepts=concepts,
            relations=relations,
            existing_concepts=matched_existing,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating preview: {str(e)}"
        )


@router.post("/confirm")
async def confirm_import(request: ConfirmImportRequest):
    """
    Confirm and finalize document import with extracted concepts
    This persists everything to database
    """
    db.connect()

    try:
        # Sanitize inputs to avoid serialization issues
        title = sanitize_text(request.title)
        summary = sanitize_text(request.summary)
        content = sanitize_text(request.content)

        # Sanitize url field
        raw_url = request.url or None
        url_clean = sanitize_text(raw_url) if raw_url else None

        # Step 1: Store document
        doc_id = db.create_doc(
            title=title,
            summary=summary,
            content=content,
            doc_type=request.type,
            url=url_clean,
        )
        print(f"Document created: {doc_id}")

        # Step 2: Create chunks
        chunks = chunk_text(content)
        if chunks:
            # Ensure chunks are sanitized as well
            chunks = [sanitize_text(c) for c in chunks]
            chunk_embeddings = await get_embeddings(chunks)
            for chunk_text_content, chunk_embedding in zip(chunks, chunk_embeddings):
                db.create_chunk(chunk_text_content, chunk_embedding, doc_id)
            print(f"Created {len(chunks)} chunks")

        # Step 3: Create or link concepts
        concept_ids = {}
        for concept_data in request.concepts:
            name = sanitize_text(concept_data.name)
            desc = sanitize_text(concept_data.desc)

            concept_embedding = await get_embedding(f"{name}: {desc}")
            concept_id = db.create_concept(name, desc, concept_embedding)
            concept_ids[name] = concept_id

            # Create mention edge
            db.create_mention(doc_id, concept_id, f"discusses {name}")

        print(f"Created/linked {len(concept_ids)} concepts")

        # Step 4: Create concept relationships
        for relation in request.relations:
            from_name = sanitize_text(relation.from_concept)
            to_name = sanitize_text(relation.to_concept)
            desc = sanitize_text(relation.desc)

            if from_name in concept_ids and to_name in concept_ids:
                db.create_related(
                    concept_ids[from_name],
                    concept_ids[to_name],
                    desc,
                )

        print(f"Created {len(request.relations)} relationships")
        print(f"Document import complete: {doc_id}")

        return {
            "success": True,
            "doc_id": doc_id,
            "message": "Document imported successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error confirming import: {str(e)}"
        )


async def process_document_pipeline(
    title: str, content: str, doc_type: str, url: Optional[str] = None
) -> str:
    """
    Complete document processing pipeline:
    1. Store doc with summary and embedding
    2. Create chunks with embeddings
    3. Extract concepts and relationships
    4. Link concepts
    """

    # Sanitize content
    content = sanitize_text(content)

    # Step 1: Generate summary
    print(f"Processing document: {title}")
    summary = await generate_summary(content)

    # Store document (no embedding, search via chunks)
    doc_id = db.create_doc(
        title=title,
        summary=summary,
        content=content,
        doc_type=doc_type,
        url=url,
    )
    print(f"Document stored: {doc_id}")

    # Step 2: Create chunks
    chunks = chunk_text(content)
    if chunks:
        chunk_embeddings = await get_embeddings(chunks)
        for chunk_text_, chunk_embedding in zip(chunks, chunk_embeddings):
            db.create_chunk(chunk_text_, chunk_embedding, doc_id)
        print(f"Created {len(chunks)} chunks")

    # Step 3: Extract concepts and relationships
    existing_concepts = db.get_all_concepts()
    extracted = await extract_concepts(content, title, existing_concepts)
    concepts = extracted.get("concepts", [])
    relations = extracted.get("relations", [])

    print(f"Extracted {len(concepts)} concepts and {len(relations)} relations")

    # Create concepts and mentions
    concept_ids = {}
    for concept_data in concepts:
        name = concept_data["name"]
        desc = concept_data["desc"]

        concept_embedding = await get_embedding(f"{name}: {desc}")
        concept_id = db.create_concept(name, desc, concept_embedding)
        concept_ids[name] = concept_id

        # Create mention edge
        db.create_mention(doc_id, concept_id, f"discusses {name}")

    # Step 4: Create concept relationships
    for relation in relations:
        from_name = relation.get("from", "")
        to_name = relation.get("to", "")

        if from_name in concept_ids and to_name in concept_ids:
            db.create_related(
                concept_ids[from_name],
                concept_ids[to_name],
                relation.get("desc", "related to"),
            )

    print(f"Document processing complete: {doc_id}")
    return doc_id


@router.post("/upload")
async def upload_document(
    file: Optional[UploadFile] = File(None),
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    type: str = Form("text"),
    url: Optional[str] = Form(None),
):
    """
    Upload and process a document (file or text)

    - **file**: Uploaded file (PDF or Markdown)
    - **title**: Document title (required if content provided)
    - **content**: Text content (if not uploading file)
    - **type**: Document type (pdf, md, text, xhs)
    - **url**: Optional URL to associate with the document
    """

    db.connect()

    try:
        # Process file upload
        if file:
            file_content = await file.read()

            filename = file.filename or "upload"

            # Determine file type from extension if not specified
            if type == "text":
                ext = os.path.splitext(filename)[1].lower()
                if ext == ".pdf":
                    type = "pdf"
                elif ext in [".md", ".markdown"]:
                    type = "md"

            # Extract text from file
            doc_title, doc_content = await process_file(file_content, filename, type)

            # Save file
            await save_upload_file(file_content, filename)

        # Process text input
        elif content and title:
            doc_title = title
            doc_content = content
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file or (title and content) must be provided",
            )

        # Use provided URL if any
        doc_url = None
        if url:
            doc_url = sanitize_text(url)

        # Process document through pipeline
        doc_id = await process_document_pipeline(
            title=doc_title, content=doc_content, doc_type=type, url=doc_url
        )

        return {
            "success": True,
            "doc_id": doc_id,
            "message": "Document processed successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing document: {str(e)}"
        )


@router.get("/documents")
async def get_documents():
    """
    Get all documents with metadata
    """
    db.connect()

    try:
        docs = db.get_all_docs()

        def _fmt_dt(val):
            if hasattr(val, "isoformat"):
                try:
                    return val.isoformat()
                except Exception:
                    return str(val)
            return val

        return [
            {
                "id": doc.get("id", ""),
                "title": doc.get("title", "Untitled"),
                "summary": doc.get("summary", ""),
                "type": doc.get("type", "unknown"),
                "created_at": _fmt_dt(doc.get("created_at", "")),
                "url": doc.get("url", None),
            }
            for doc in docs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching documents: {str(e)}"
        )


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document and all related data
    """
    db.connect()

    try:
        # Delete document (SurrealDB will handle cascade deletion of relationships)
        db.delete_doc(doc_id)

        return {"success": True, "message": f"Document {doc_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting document: {str(e)}"
        )
