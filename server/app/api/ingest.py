"""Ingest API - Document upload and processing"""

import os
from typing import Optional

from app.database import db
from app.file_utils import process_file, save_upload_file
from app.models import DocumentCreate, DocumentResponse
from app.utils import (
    chunk_text,
    extract_concepts,
    generate_summary,
    get_embedding,
    get_embeddings,
)
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


async def process_document_pipeline(
    title: str, content: str, doc_type: str, meta: Optional[dict] = None
) -> str:
    """
    Complete document processing pipeline:
    1. Store doc with summary and embedding
    2. Create chunks with embeddings
    3. Extract concepts and relationships
    4. Link concepts
    """

    # Step 1: Generate summary
    print(f"Processing document: {title}")
    summary = await generate_summary(content)

    # Store document (no embedding, search via chunks)
    doc_id = db.create_doc(
        title=title,
        summary=summary,
        content=content,
        doc_type=doc_type,
        meta=meta or {},
    )
    print(f"Document stored: {doc_id}")

    # Step 2: Create chunks
    chunks = chunk_text(content)
    if chunks:
        chunk_embeddings = await get_embeddings(chunks)
        for chunk_text, chunk_embedding in zip(chunks, chunk_embeddings):
            db.create_chunk(chunk_text, chunk_embedding, doc_id)
        print(f"Created {len(chunks)} chunks")

    # Step 3: Extract concepts and relationships
    extracted = await extract_concepts(content, title)
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
    meta: Optional[str] = Form(None),
):
    """
    Upload and process a document (file or text)

    - **file**: Uploaded file (PDF or Markdown)
    - **title**: Document title (required if content provided)
    - **content**: Text content (if not uploading file)
    - **type**: Document type (pdf, md, text, xhs)
    - **meta**: JSON string with metadata
    """

    db.connect()

    try:
        # Process file upload
        if file:
            file_content = await file.read()

            # Determine file type from extension if not specified
            if type == "text":
                ext = os.path.splitext(file.filename)[1].lower()
                if ext == ".pdf":
                    type = "pdf"
                elif ext in [".md", ".markdown"]:
                    type = "md"

            # Extract text from file
            doc_title, doc_content = await process_file(
                file_content, file.filename, type
            )

            # Save file
            await save_upload_file(file_content, file.filename)

        # Process text input
        elif content and title:
            doc_title = title
            doc_content = content
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file or (title and content) must be provided",
            )

        # Parse metadata if provided
        import json

        doc_meta = {}
        if meta:
            try:
                doc_meta = json.loads(meta)
            except:
                pass

        # Process document through pipeline
        doc_id = await process_document_pipeline(
            title=doc_title, content=doc_content, doc_type=type, meta=doc_meta
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
        return [
            {
                "id": doc.get("id", ""),
                "title": doc.get("title", "Untitled"),
                "summary": doc.get("summary", ""),
                "type": doc.get("type", "unknown"),
                "created_at": doc.get("created_at", ""),
                "meta": doc.get("meta", {}),
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
