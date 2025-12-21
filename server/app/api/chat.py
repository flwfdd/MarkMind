"""Chat API - Intelligent conversation with RAG using LangGraph ReAct Agent"""

import json
import uuid
from typing import AsyncGenerator

import httpx
from app.config import settings
from app.database import db
from app.models import (
    ChatMessage,
    ChatRequest,
    ChatStreamEvent,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
    ToolCall,
)
from app.utils import get_embedding, llm
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langfuse import Langfuse

# Import Langfuse if enabled
langfuse_handler = None
if (
    settings.langfuse_enabled
    and settings.langfuse_secret_key
    and settings.langfuse_public_key
):
    try:
        from langfuse.langchain import CallbackHandler

        langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        langfuse_handler = CallbackHandler(public_key=settings.langfuse_public_key)
    except ImportError:
        print("Warning: Langfuse is enabled but langfuse package is not installed")

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _record_to_id(val) -> str:
    """Normalize a record-like value into a string ID"""
    if val is None:
        return ""
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


# System prompt for the agent
SYSTEM_PROMPT = """你是 MarkMind Agent，一个高超的个人知识库助手，基于用户的知识图谱进行智能问答和探索。
你的核心能力包括：搜索信息、检索文档详情以及深入探索相关概念。

请严格遵守以下行为准则：

1. **工具优先**：在回答问题之前，请务必优先调用可用工具以获取准确的事实信息，切勿仅凭记忆或猜测作答。
2. **引用格式（至关重要）**：
   当你在回复中提及知识图谱中的任何节点（如文档或概念）时，**必须**严格使用以下专用格式：
   `[[node:<node_id>|显示名称]]`
   * 正确示例：`[[node:doc:abc123|深度学习综述]]` `[[node:concept:abc123|大模型]]`
   * 错误示例：`[深度学习综述](doc:abc123)` 或使用了知识图谱中不存在的 ID 或名称。
3. **严禁编造 ID**：绝对不允许捏造节点 ID。你只能使用由工具查询或系统返回的真实 ID。外部链接不要用这种格式。
4. **内容整合**：当调用工具获取到文档或概念详情后，请将检索到的核心结果有机地整合进你的回答中，而不是简单罗列数据。

**输出规范**：
* 请全程使用 **Markdown** 格式，以便前端正确渲染。
* 请始终使用与用户提问相同的语言进行回复。
"""


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

    query_embedding = await get_embedding(query)
    chunk_results = db.vector_search_chunks(query_embedding, limit=5)
    concept_results = db.vector_search_concepts(query_embedding, limit=3)

    result_text = "## Search Results\n\n"

    if chunk_results:
        result_text += "### Relevant Content:\n"

        for i, (chunk, score) in enumerate(chunk_results, 1):
            text = chunk.get("text", "")[:300]
            source_raw = chunk.get("source")
            source_id = _record_to_id(source_raw) or "unknown"
            # Try to fetch document title for nicer display
            title = ""
            if source_id and source_id != "unknown":
                doc = db.get_doc(source_id)
                if doc:
                    title = doc.get("title", "")
            title_part = f" — {title}" if title else ""
            result_text += f"{i}. (Score: {score:.3f}, Source: {source_id}{title_part})\n{text}...\n\n"

    if concept_results:
        result_text += "### Related Concepts:\n"
        for concept, score in concept_results:
            concept_id = concept.get("id", "")
            name = concept.get("name") or concept_id
            desc = (concept.get("desc", "") or "").strip()
            result_text += (
                f"- [[node:{concept_id}|{name}]] (Score: {score:.3f}): {desc}\n"
            )

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

    # Find concepts directly connected to this document via mentions
    mentions = db.get_all_mentions()

    connected_concepts = [
        _record_to_id(m.get("out"))
        for m in mentions
        if _record_to_id(m.get("in")) == doc_id
    ]
    # Deduplicate while preserving order
    seen = set()
    connected_concepts = [
        x for x in connected_concepts if not (x in seen or seen.add(x))
    ]

    result = f"""## Document: {doc.get('title', 'Untitled')}

**Summary:** {doc.get('summary', '')}

**Type:** {doc.get('type', 'unknown')}

**Content:**
{doc.get('content', '')}
"""

    if connected_concepts:
        result += "\n**Connected Concepts:**\n"
        for cid in connected_concepts[:20]:
            c = db.get_concept(cid)
            name = c.get("name") if c else cid
            desc = (c.get("desc", "") if c else "").strip()
            result += f"- [[node:{cid}|{name}]]: {desc}\n"

    return result


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

    mentions = db.get_all_mentions()

    related_docs = [
        _record_to_id(m.get("in"))
        for m in mentions
        if _record_to_id(m.get("out")) == concept_id
    ]

    result = f"""## Concept: {concept.get('name', 'Unnamed Concept')}

**Description:** {concept.get('desc', '')}

**Mentioned in {len(related_docs)} documents:**
"""

    for doc_id in related_docs[:20]:
        doc = db.get_doc(doc_id)
        if doc:
            summary = (doc.get("summary", "") or "").strip()
            if summary:
                # Truncate long summaries for readability
                summary_short = (
                    (summary[:300] + "...") if len(summary) > 300 else summary
                )
                result += f"- [[node:{doc_id}|{doc.get('title', 'Untitled')}]] ({doc_id}) — {summary_short}\n"
            else:
                result += (
                    f"- [[node:{doc_id}|{doc.get('title', 'Untitled')}]] ({doc_id})\n"
                )

    # Also include related concepts (both outgoing and incoming edges)
    related_edges = db.get_all_related()
    neighbors: list[str] = []

    for r in related_edges:
        in_id = _record_to_id(r.get("in"))
        out_id = _record_to_id(r.get("out"))
        if in_id == concept_id and out_id != concept_id:
            neighbors.append(out_id)
        if out_id == concept_id and in_id != concept_id:
            neighbors.append(in_id)

    # Deduplicate
    seen = set()
    neighbors = [x for x in neighbors if not (x in seen or seen.add(x))]

    if neighbors:
        result += "\n**Related Concepts:**\n"
        for cid in neighbors[:20]:
            c = db.get_concept(cid)
            name = c.get("name") if c else cid
            desc = (c.get("desc", "") if c else "").strip()
            result += f"- [[node:{cid}|{name}]]: {desc}\n"

    return result


# Tavily search tool
@tool
async def tavily_search(query: str) -> str:
    """Search the external Tavily API for relevant results.

    Uses the Tavily POST /search API schema and returns a markdown-like summary
    including the top results and any concise answer returned by Tavily.
    """
    # Ensure config
    if (
        not settings.tavily_enabled
        or not settings.tavily_api_key
        or not settings.tavily_host
    ):
        return "Tavily is not configured. Set TAVILY_ENABLED=true and provide TAVILY_API_KEY and TAVILY_HOST in your environment."

    payload = {
        "query": query,
        "search_depth": "basic",
        "auto_parameters": False,
        "max_results": 20,
        "include_raw_content": False,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.tavily_host.rstrip('/')}/search",
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.tavily_api_key}",
                    "Content-Type": "application/json",
                },
            )

            if resp.status_code != 200:
                return f"Tavily search failed: {resp.status_code} - {resp.text}"

            data = resp.json()

            # Return the raw Tavily JSON response as a string (no additional formatting)
            return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        return f"Tavily search error: {str(e)}"


# Create tools list
tools = [
    search_knowledge_graph,
    get_document_details,
    get_concept_details,
    tavily_search,
]

# Create the ReAct agent
agent_executor = create_agent(llm, tools)


def lc_message_to_chat_message(msg) -> ChatMessage:
    """Convert LangChain message to ChatMessage format"""
    if isinstance(msg, SystemMessage):
        content = str(msg.content) if msg.content else ""
        return ChatMessage(role="system", content=content)
    elif isinstance(msg, HumanMessage):
        content = str(msg.content) if msg.content else ""
        return ChatMessage(role="user", content=content)
    elif isinstance(msg, AIMessage):
        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.get("id") or str(uuid.uuid4()),
                    name=tc.get("name", ""),
                    arguments=json.dumps(tc.get("args", {}), ensure_ascii=False),
                )
                for tc in msg.tool_calls
            ]
        content = str(msg.content) if msg.content else None
        return ChatMessage(
            role="assistant",
            content=content,
            tool_calls=tool_calls if tool_calls else None,
        )
    elif isinstance(msg, ToolMessage):
        content = str(msg.content) if msg.content else ""
        return ChatMessage(
            role="tool",
            content=content,
            tool_call_id=msg.tool_call_id,
            name=msg.name,
        )
    else:
        content = str(msg.content) if hasattr(msg, "content") and msg.content else ""
        return ChatMessage(role="assistant", content=content)


def chat_message_to_lc_message(msg: ChatMessage):
    """Convert ChatMessage to LangChain message format"""
    if msg.role == "system":
        return SystemMessage(content=msg.content or "")
    elif msg.role == "user":
        return HumanMessage(content=msg.content or "")
    elif msg.role == "assistant":
        if msg.tool_calls:
            # Convert tool calls back to LangChain format
            lc_tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "args": json.loads(tc.arguments),
                }
                for tc in msg.tool_calls
            ]
            return AIMessage(content=msg.content or "", tool_calls=lc_tool_calls)
        return AIMessage(content=msg.content or "")
    elif msg.role == "tool":
        return ToolMessage(
            content=msg.content or "",
            tool_call_id=msg.tool_call_id or "",
            name=msg.name or "",
        )
    else:
        return HumanMessage(content=msg.content or "")


def emit_event(event: ChatStreamEvent) -> str:
    """Format SSE event"""
    return f"data: {event.model_dump_json()}\n\n"


async def stream_agent_response(
    messages: list[ChatMessage],
) -> AsyncGenerator[str, None]:
    """Stream agent responses with proper message structure"""

    # Convert input messages to LangChain format
    lc_messages = []

    # Add system message if not present
    has_system = any(msg.role == "system" for msg in messages)
    if not has_system:
        lc_messages.append(SystemMessage(content=SYSTEM_PROMPT))

    for msg in messages:
        lc_messages.append(chat_message_to_lc_message(msg))

    # Track new messages generated in this round
    new_messages: list[ChatMessage] = []
    current_ai_content = ""
    current_ai_tool_calls: list[ToolCall] = []
    current_ai_message_id: str | None = None

    # Prepare config with Langfuse callback if enabled
    config: dict[str, list] = {}
    if langfuse_handler:
        config["callbacks"] = [langfuse_handler]

    try:
        async for event in agent_executor.astream_events(
            {"messages": lc_messages},
            version="v2",
            config=config if langfuse_handler else None,  # type: ignore
        ):
            event_type = event.get("event", "")
            event_name = event.get("name", "")

            # Handle streaming AI content
            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if isinstance(chunk, AIMessageChunk):
                    # Ensure we have a message id for this streaming message
                    if current_ai_message_id is None:
                        current_ai_message_id = str(uuid.uuid4())

                    # Stream text content delta
                    if chunk.content:
                        delta = str(chunk.content) if chunk.content else ""
                        current_ai_content += delta
                        yield emit_event(
                            ChatStreamEvent(
                                event="message_delta",
                                message_id=current_ai_message_id,
                                delta=delta,
                            )
                        )

                    # Accumulate tool calls
                    if chunk.tool_call_chunks:
                        for tc_chunk in chunk.tool_call_chunks:
                            tc_id = tc_chunk.get("id")
                            tc_name = tc_chunk.get("name")
                            tc_args = tc_chunk.get("args", "")

                            if tc_id and tc_name:
                                # New tool call
                                current_ai_tool_calls.append(
                                    ToolCall(
                                        id=tc_id, name=tc_name, arguments=tc_args or ""
                                    )
                                )
                            elif current_ai_tool_calls and tc_args:
                                # Append to existing tool call arguments
                                current_ai_tool_calls[-1].arguments += tc_args

            # Handle AI message completion
            elif event_type == "on_chat_model_end":
                output = event.get("data", {}).get("output")
                if isinstance(output, AIMessage):
                    # Build complete AI message
                    tool_calls = None
                    if output.tool_calls:
                        tool_calls = [
                            ToolCall(
                                id=tc.get("id") or str(uuid.uuid4()),
                                name=tc.get("name", ""),
                                arguments=json.dumps(
                                    tc.get("args", {}), ensure_ascii=False
                                ),
                            )
                            for tc in output.tool_calls
                        ]

                    content = str(output.content) if output.content else None
                    ai_message = ChatMessage(
                        role="assistant",
                        content=content,
                        tool_calls=tool_calls,
                    )
                    new_messages.append(ai_message)
                    # Emit completion with message id so frontend can match
                    yield emit_event(
                        ChatStreamEvent(
                            event="message_complete",
                            message_id=current_ai_message_id,
                            message=ai_message,
                        )
                    )

                    # Reset accumulators
                    current_ai_content = ""
                    current_ai_tool_calls = []
                    current_ai_message_id = None

            # Handle tool execution completion
            elif event_type == "on_tool_end":
                output = event.get("data", {}).get("output")
                tool_name = event_name

                # Find the corresponding tool call id
                tool_call_id = None
                for msg in reversed(new_messages):
                    if msg.role == "assistant" and msg.tool_calls:
                        for tc in msg.tool_calls:
                            if tc.name == tool_name:
                                tool_call_id = tc.id
                                break
                        if tool_call_id:
                            break

                if tool_call_id is None:
                    tool_call_id = str(uuid.uuid4())

                tool_message = ChatMessage(
                    role="tool",
                    content=output.content if output else "",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
                new_messages.append(tool_message)
                yield emit_event(
                    ChatStreamEvent(
                        event="message_complete",
                        message_id=tool_call_id,
                        message=tool_message,
                    )
                )

        # Build complete history for round_complete
        # Start with original messages (excluding the system we might have added)
        complete_history: list[ChatMessage] = []

        # Add original user messages
        for msg in messages:
            complete_history.append(msg)

        # Add new messages from this round
        complete_history.extend(new_messages)

        yield emit_event(
            ChatStreamEvent(event="round_complete", messages=complete_history)
        )

    except Exception as e:
        yield emit_event(ChatStreamEvent(event="error", error=str(e)))


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with AI agent using ReAct pattern

    The agent can:
    - Search the knowledge graph
    - Retrieve document details
    - Explore concepts and relationships

    Returns a streaming response with structured events:
    - message_delta: Incremental content updates
    - message_complete: Complete message when finished
    - round_complete: Full conversation history at end
    - error: Error information
    """
    db.connect()

    try:
        return StreamingResponse(
            stream_agent_response(request.messages),
            media_type="text/event-stream",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/recommend")
async def recommend(request: RecommendationRequest):
    """Generate follow-up question recommendations based on provided context.

    Accepts:
    - `messages`: optional list of recent chat messages (ChatMessage)
    - `context`: optional list of strings (textual context, e.g., title + short summary)

    Returns a JSON list of recommendation strings (fixed max 5).
    """
    db.connect()

    req = request

    # Build prompt
    user_context = ""
    if req.messages:
        # use the last few messages (trim for safety)
        last_msgs = req.messages[-10:]
        user_context += "Recent messages:\n"
        for m in last_msgs:
            user_context += f"- {m.role}: {m.content}\n"

    if req.context:
        user_context += "\nContext snippets:\n"
        for c in req.context:
            user_context += f"- {c}\n"

    LIMIT = 3
    system = SystemMessage(
        content="You are an assistant that generates concise, actionable follow-up questions to help the user explore the knowledge graph or clarify their needs. Output a JSON array of short questions in the user's language."
    )
    prompt = f"请基于以下上下文（用户语言），生成不超过 {LIMIT} 条推荐性问题（简短、可直接发送）：\n\n{user_context}\n\n要求：只返回一个 JSON 对象：{ '{"suggestions": ["问法1","问法2"]}' }，不要包含额外文本。"

    messages = [system, HumanMessage(content=prompt)]

    try:
        resp = await llm.ainvoke(messages)
        raw = str(resp.content).strip()

        # Extract JSON if inside code block
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        data = json.loads(raw)
        suggestions = data.get("suggestions", [])
        # Ensure limit and sanitize
        suggestions = [s for s in suggestions if isinstance(s, str) and s.strip()][
            :LIMIT
        ]

        return RecommendationResponse(
            suggestions=[RecommendationItem(text=s) for s in suggestions]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")
