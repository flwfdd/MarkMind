"""Database models and schemas"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Document creation schema"""

    title: str
    content: str
    type: str = Field(..., pattern="^(pdf|md|xhs|text)$")
    url: Optional[str] = None


class DocumentResponse(BaseModel):
    """Document response schema"""

    id: str
    title: str
    summary: str
    content: str
    type: str
    created_at: datetime
    url: Optional[str] = None


class ConceptResponse(BaseModel):
    """Concept response schema"""

    id: str
    name: str
    desc: str


class GraphNode(BaseModel):
    """Graph node schema for visualization"""

    id: str
    type: str  # 'doc' or 'concept'
    label: str  # title or concept name
    desc: Optional[str] = None  # summary or concept desc
    url: Optional[str] = None
    doc_type: Optional[str] = None  # For documents: 'pdf' | 'md' | 'xhs' | 'text'
    created_at: Optional[datetime] = None


class GraphEdge(BaseModel):
    """Graph edge schema for visualization"""

    source: str
    target: str
    type: str  # 'mentions' or 'related'
    desc: Optional[str] = None


class GraphOverview(BaseModel):
    """Complete graph overview"""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class NodeDetail(BaseModel):
    """Node detail with recommendations"""

    node: GraphNode
    full_content: Optional[str] = None
    recommendations: list[GraphNode] = Field(default_factory=list)


class SearchRequest(BaseModel):
    """Search request schema"""

    query: str
    limit: int = 10


class SearchItem(BaseModel):
    score: float
    node: GraphNode


class SearchResult(BaseModel):
    """Search result schema (unified list of score+node)"""

    results: list[SearchItem]


class ToolCall(BaseModel):
    """Tool call schema for assistant messages"""

    id: str
    name: str
    arguments: str  # JSON string of arguments


class ChatMessage(BaseModel):
    """Chat message schema - compatible with OpenAI format"""

    role: str  # 'system', 'user', 'assistant', 'tool'
    content: Optional[str] = None
    # For assistant messages with tool calls
    tool_calls: Optional[list[ToolCall]] = None
    # For tool response messages
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # tool name for tool messages


class ChatRequest(BaseModel):
    """Chat request schema"""

    messages: list[ChatMessage]


class RecommendationRequest(BaseModel):
    """Request to generate recommended follow-up questions"""

    messages: list[ChatMessage] | None = None
    # Optional list of context textual snippets (e.g., title and short summary)
    context: Optional[list[str]] = None


class RecommendationItem(BaseModel):
    text: str


class RecommendationResponse(BaseModel):
    suggestions: list[RecommendationItem]


class ChatStreamEvent(BaseModel):
    """SSE event types for chat streaming"""

    event: str  # 'message_delta', 'message_complete', 'round_complete', 'error'
    # Message id to associate deltas/completion with a specific message
    message_id: Optional[str] = None
    # For message_delta: incremental content update
    delta: Optional[str] = None
    # For message_complete: the complete message
    message: Optional[ChatMessage] = None
    # For round_complete: full message history
    messages: Optional[list[ChatMessage]] = None
    # For error
    error: Optional[str] = None


class ParseRequest(BaseModel):
    """Parse request for document import"""

    url: Optional[str] = None  # URL to fetch content from
    file_content: Optional[str] = None  # Base64 encoded file content
    file_name: Optional[str] = None  # Original filename
    file_type: Optional[str] = None  # pdf, txt, md, html


class ParseResponse(BaseModel):
    """Parse response with extracted info"""

    title: str
    content: str
    type: str
    url: Optional[str] = None


class ExtractedConcept(BaseModel):
    """Extracted concept schema"""

    name: str
    desc: str


class ExtractedRelation(BaseModel):
    """Extracted relation schema"""

    from_concept: str  # concept name
    to_concept: str  # concept name
    desc: str


class DocumentPreview(BaseModel):
    """Document preview before final import"""

    title: str
    summary: str
    content: str
    type: str
    url: Optional[str] = None
    concepts: list[ExtractedConcept]  # Newly extracted concepts
    relations: list[ExtractedRelation]  # Relations between concepts
    existing_concepts: list[ConceptResponse]  # Existing concepts matched


class ConfirmImportRequest(BaseModel):
    """Confirm and finalize document import"""

    title: str
    summary: str
    content: str
    type: str
    url: Optional[str] = None
    concepts: list[ExtractedConcept]
    relations: list[ExtractedRelation]
