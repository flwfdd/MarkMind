"""Graph API - Knowledge graph interaction"""

from typing import Optional

from app.database import db
from app.models import (
    GraphEdge,
    GraphNode,
    GraphOverview,
    NodeDetail,
    SearchItem,
    SearchRequest,
    SearchResult,
)
from app.utils import get_embedding
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/graph", tags=["graph"])


def format_node(node_data: dict, node_type: str) -> GraphNode:
    """Format database node to GraphNode"""
    # Ensure id is a string (RecordID from SurrealDB may be returned)
    id_str = str(node_data.get("id", ""))
    if node_type == "doc":
        return GraphNode(
            id=id_str,
            type="doc",
            label=node_data.get("title", "Untitled"),
            desc=node_data.get("summary", ""),
            meta=node_data.get("meta", {}),
            doc_type=node_data.get("type"),
            created_at=node_data.get("created_at"),
        )
    else:  # concept
        concept_name = node_data.get("name", "")
        return GraphNode(
            id=id_str,
            type="concept",
            label=concept_name,
            desc=node_data.get("desc", ""),
            created_at=node_data.get("created_at"),
        )


def _record_to_id(val) -> str:
    """Normalize relation 'in'/'out' values to a string ID.

    SurrealDB clients may return relations in different shapes:
    - {'id': 'doc:abc', ...}
    - {'table': 'doc', 'id': 'abc'}
    - a RecordID object with attributes (table_name, record_id)
    - a plain string like 'doc:abc'
    - other record objects
    """
    if val is None:
        return ""
    # SurrealDB RecordID object (ws client) often has table_name and record_id
    if hasattr(val, "table_name") and hasattr(val, "record_id"):
        try:
            return f"{val.table_name}:{val.record_id}"
        except Exception:
            return str(val)
    # If relation value is a dict and directly contains 'id'
    if isinstance(val, dict):
        if "id" in val:
            return str(val["id"])
        if "table" in val and "id" in val:
            return f"{val['table']}:{val['id']}"
        # Fallback to string representation
        return str(val)
    return str(val)


@router.get("/overview", response_model=GraphOverview)
async def get_graph_overview():
    """
    Get complete knowledge graph overview

    Returns all documents, concepts, and their relationships
    """
    db.connect()

    try:
        # Get all nodes
        docs = db.get_all_docs()
        concepts = db.get_all_concepts()

        # Format nodes
        nodes = []
        for doc in docs:
            nodes.append(format_node(doc, "doc"))
        for concept in concepts:
            nodes.append(format_node(concept, "concept"))

        # Get all edges
        mentions = db.get_all_mentions()
        related = db.get_all_related()

        # Format edges
        edges = []
        for mention in mentions:
            edges.append(
                GraphEdge(
                    source=_record_to_id(mention.get("in")),
                    target=_record_to_id(mention.get("out")),
                    type="mentions",
                    desc=mention.get("desc"),
                )
            )

        for relation in related:
            edges.append(
                GraphEdge(
                    source=_record_to_id(relation.get("in")),
                    target=_record_to_id(relation.get("out")),
                    type="related",
                    desc=relation.get("desc"),
                )
            )

        return GraphOverview(nodes=nodes, edges=edges)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching graph: {str(e)}")


@router.get("/node/{node_id}", response_model=NodeDetail)
async def get_node_detail(node_id: str):
    """
    Get node details and recommendations

    Returns:
    - Node information
    - Full content (for docs)
    - Top 5 related recommendations based on vector similarity
    """
    db.connect()

    try:
        # Determine node type from ID
        if node_id.startswith("doc:"):
            node_data = db.get_doc(node_id)
            if not node_data:
                raise HTTPException(status_code=404, detail="Document not found")

            node = format_node(node_data, "doc")
            full_content = node_data.get("content", "")

            # Get recommendations using document embedding.
            # If document has stored embedding, use it. Otherwise try to build embedding
            # from its chunks' embeddings (average) to avoid calling external API.
            embedding = node_data.get("embedding", [])
            if not embedding:
                # Try to compute embedding by averaging chunk embeddings
                chunks = db.get_chunks_by_doc(node_id)
                chunk_embs = [c.get("embedding") for c in chunks if c.get("embedding")]
                if chunk_embs:
                    # Average element-wise
                    count = len(chunk_embs)
                    dim = len(chunk_embs[0])
                    avg = [0.0] * dim
                    for e in chunk_embs:
                        for i, v in enumerate(e):
                            avg[i] += float(v)
                    embedding = [x / count for x in avg]

            # As a fallback, we could call get_embedding(full_content) but prefer
            # local aggregation to avoid external calls during tests.
            if embedding:
                try:
                    # Request more candidates to ensure we can find other docs after filtering out this doc
                    similar_docs = db.vector_search_docs(embedding, limit=30)
                except Exception:
                    similar_docs = []

                # Keep unique docs excluding the current one
                seen = set()
                recommendations = []
                for doc, score in similar_docs:
                    doc_id_str = str(doc.get("id"))
                    if doc_id_str == node_id:
                        continue
                    if doc_id_str in seen:
                        continue
                    seen.add(doc_id_str)
                    recommendations.append(format_node(doc, "doc"))
                    if len(recommendations) >= 5:
                        break

                # If we still lack recommendations, fall back to concept-based related docs
                if len(recommendations) < 5:
                    mentions = db.get_all_mentions()
                    # Find concepts mentioned by this doc
                    concepts = [
                        _record_to_id(m.get("out"))
                        for m in mentions
                        if _record_to_id(m.get("in")) == node_id
                    ]
                    for concept_id in concepts:
                        # find other docs that mention the same concept
                        for m in mentions:
                            if _record_to_id(m.get("out")) == concept_id:
                                candidate_doc_id = _record_to_id(m.get("in"))
                                if (
                                    candidate_doc_id
                                    and candidate_doc_id != node_id
                                    and candidate_doc_id not in seen
                                ):
                                    doc = db.get_doc(candidate_doc_id)
                                    if doc:
                                        seen.add(candidate_doc_id)
                                        recommendations.append(format_node(doc, "doc"))
                                        if len(recommendations) >= 5:
                                            break
                        if len(recommendations) >= 5:
                            break
            else:
                # No embedding and no chunks -> try concept based only
                mentions = db.get_all_mentions()
                seen = set()
                recommendations = []
                concepts = [
                    _record_to_id(m.get("out"))
                    for m in mentions
                    if _record_to_id(m.get("in")) == node_id
                ]
                for concept_id in concepts:
                    for m in mentions:
                        if _record_to_id(m.get("out")) == concept_id:
                            candidate_doc_id = _record_to_id(m.get("in"))
                            if (
                                candidate_doc_id
                                and candidate_doc_id != node_id
                                and candidate_doc_id not in seen
                            ):
                                doc = db.get_doc(candidate_doc_id)
                                if doc:
                                    seen.add(candidate_doc_id)
                                    recommendations.append(format_node(doc, "doc"))
                                    if len(recommendations) >= 5:
                                        break
                        if len(recommendations) >= 5:
                            break

        elif node_id.startswith("concept:"):
            node_data = db.get_concept(node_id)
            if not node_data:
                raise HTTPException(status_code=404, detail="Concept not found")

            node = format_node(node_data, "concept")
            full_content = node_data.get("desc", "")

            # Get recommendations using concept embedding
            embedding = node_data.get("embedding", [])
            recommendations = []
            if embedding:
                similar_docs = db.vector_search_docs(embedding, limit=30)
                seen = set()
                for doc, score in similar_docs:
                    doc_id_str = str(doc.get("id"))
                    if doc_id_str in seen:
                        continue
                    seen.add(doc_id_str)
                    recommendations.append(format_node(doc, "doc"))
                    if len(recommendations) >= 5:
                        break

            # Fallback: find docs that mention this concept if vector results are insufficient
            if len(recommendations) < 5:
                mentions = db.get_all_mentions()
                seen = {r.id for r in recommendations}
                for m in mentions:
                    if _record_to_id(m.get("out")) == node_id:
                        cand = _record_to_id(m.get("in"))
                        if cand and cand not in seen:
                            doc = db.get_doc(cand)
                            if doc:
                                recommendations.append(format_node(doc, "doc"))
                                seen.add(cand)
                                if len(recommendations) >= 5:
                                    break
        else:
            raise HTTPException(status_code=400, detail="Invalid node ID format")

        return NodeDetail(
            node=node, full_content=full_content, recommendations=recommendations
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching node: {str(e)}")


@router.post("/search", response_model=SearchResult)
async def search_graph(request: SearchRequest):
    """
    Search knowledge graph using semantic similarity

    Searches both chunks and concepts, returns most relevant nodes
    """
    db.connect()

    try:
        # Generate query embedding
        query_embedding = await get_embedding(request.query)

        # Search chunks and concepts
        chunk_results = db.vector_search_chunks(query_embedding, limit=request.limit)
        concept_results = db.vector_search_concepts(
            query_embedding, limit=request.limit
        )

        # Combine and deduplicate results
        all_results = []
        seen_ids = set()

        # Add documents from chunk results
        for chunk, score in chunk_results:
            # Normalize source value to a string ID (may be RecordID, dict, or string)
            source_id = _record_to_id(chunk.get("source"))
            if source_id and source_id not in seen_ids:
                doc = db.get_doc(source_id)
                if doc:
                    all_results.append((format_node(doc, "doc"), score))
                    seen_ids.add(source_id)

        # Add concepts
        for concept, score in concept_results:
            # Normalize concept id to a string (may be RecordID/dict)
            concept_id = _record_to_id(concept.get("id"))
            if concept_id and concept_id not in seen_ids:
                all_results.append((format_node(concept, "concept"), score))
                seen_ids.add(concept_id)

        # Sort by score and limit
        all_results.sort(key=lambda x: x[1], reverse=True)
        all_results = all_results[: request.limit]

        results = [SearchItem(score=score, node=node) for node, score in all_results]

        return SearchResult(results=results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")
