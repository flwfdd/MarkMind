"""Chat API - Intelligent conversation with RAG"""

import json
from typing import AsyncGenerator

from app.database import db
from app.models import ChatMessage, ChatRequest
from app.utils import get_embedding, llm
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])


# Define tools for the agent
@tool
async def search_knowledge_graph(query: str) -> str:
    """Search the knowledge graph for relevant information using semantic search.

    Args:
        query: The search query to find relevant documents and concepts

    Returns:
        A formatted string with search results
    """
    db.connect()

    # Get query embedding
    query_embedding = await get_embedding(query)

    # Search chunks and concepts
    chunk_results = db.vector_search_chunks(query_embedding, limit=5)
    concept_results = db.vector_search_concepts(query_embedding, limit=3)

    # Format results
    result_text = "## Search Results\n\n"

    if chunk_results:
        result_text += "### Relevant Content:\n"
        for i, (chunk, score) in enumerate(chunk_results, 1):
            text = chunk.get("text", "")[:300]  # Limit text length
            source_id = chunk.get("source", "unknown")
            result_text += (
                f"{i}. (Score: {score:.3f}, Source: {source_id})\n{text}...\n\n"
            )

    if concept_results:
        result_text += "### Related Concepts:\n"
        for concept, score in concept_results:
            concept_id = concept.get("id", "")
            desc = concept.get("desc", "")
            result_text += f"- **{concept_id}** (Score: {score:.3f}): {desc}\n"

    return result_text


@tool
async def get_document_details(doc_id: str) -> str:
    """Get full details of a specific document.

    Args:
        doc_id: The document ID (e.g., 'doc:abc123')

    Returns:
        Document content and metadata
    """
    db.connect()

    doc = db.get_doc(doc_id)
    if not doc:
        return f"Document {doc_id} not found"

    return f"""## Document: {doc.get('title', 'Untitled')}

**Summary:** {doc.get('summary', '')}

**Type:** {doc.get('type', 'unknown')}

**Content:**
{doc.get('content', '')}
"""


@tool
async def get_concept_details(concept_id: str) -> str:
    """Get details about a specific concept and find related documents.

    Args:
        concept_id: The concept ID (e.g., 'concept:machine_learning')

    Returns:
        Concept description and related documents
    """
    db.connect()

    concept = db.get_concept(concept_id)
    if not concept:
        return f"Concept {concept_id} not found"

    # Find documents mentioning this concept
    mentions = db.get_all_mentions()

    def _record_to_id(val) -> str:
        if val is None:
            return ""
        # SurrealDB RecordID object may contain attributes (table_name, record_id)
        if hasattr(val, "table_name") and hasattr(val, "record_id"):
            try:
                return f"{val.table_name}:{val.record_id}"
            except Exception:
                return str(val)
        if isinstance(val, dict):
            if "id" in val:
                return str(val["id"])
            if "table" in val and "id" in val:
                return f"{val['table']}:{val['id']}"
            return str(val)
        return str(val)

    related_docs = [
        _record_to_id(m.get("in"))
        for m in mentions
        if _record_to_id(m.get("out")) == concept_id
    ]

    result = f"""## Concept: {concept_id}

**Description:** {concept.get('desc', '')}

**Mentioned in {len(related_docs)} documents:**
"""

    for doc_id in related_docs[:5]:  # Limit to 5
        doc = db.get_doc(doc_id)
        if doc:
            result += f"- {doc.get('title', 'Untitled')} ({doc_id})\n"

    return result


# Create the ReAct agent
tools = [search_knowledge_graph, get_document_details, get_concept_details]
agent_executor = create_react_agent(llm, tools)


async def stream_agent_response(
    messages: list[ChatMessage],
) -> AsyncGenerator[str, None]:
    """Stream agent responses"""

    # Convert messages to LangChain format
    lc_messages = []

    # Add system message if not present
    has_system = any(msg.role == "system" for msg in messages)
    if not has_system:
        lc_messages.append(
            SystemMessage(
                content="""You are a helpful AI assistant with access to a knowledge graph. 
You can search for information, retrieve document details, and explore concepts.
Always use the available tools to find accurate information before answering questions."""
            )
        )

    for msg in messages:
        if msg.role == "system":
            lc_messages.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))
        elif msg.role == "tool":
            lc_messages.append(
                ToolMessage(content=msg.content, tool_call_id=msg.name or "unknown")
            )

    # Stream agent execution
    try:
        async for event in agent_executor.astream({"messages": lc_messages}):
            # Process different types of events
            if "agent" in event:
                agent_output = event["agent"]
                if "messages" in agent_output:
                    for message in agent_output["messages"]:
                        if hasattr(message, "content") and message.content:
                            # Stream agent thoughts/responses
                            yield f"data: {json.dumps({'type': 'agent', 'content': message.content})}\n\n"

            if "tools" in event:
                tools_output = event["tools"]
                if "messages" in tools_output:
                    for message in tools_output["messages"]:
                        if hasattr(message, "content"):
                            # Stream tool results
                            tool_name = getattr(message, "name", "unknown")
                            yield f"data: {json.dumps({'type': 'tool', 'tool': tool_name, 'content': message.content})}\n\n"

        # Send completion signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with AI agent using ReAct pattern

    The agent can:
    - Search the knowledge graph
    - Retrieve document details
    - Explore concepts and relationships

    Returns a streaming response with agent thoughts and tool calls
    """

    db.connect()

    try:
        return StreamingResponse(
            stream_agent_response(request.messages), media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
