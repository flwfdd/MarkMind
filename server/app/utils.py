"""Utility functions for text processing and LLM operations"""

import asyncio
import json
import re
from typing import Optional

from app.config import settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import AsyncOpenAI

# Initialize LLM
llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    temperature=0.7,
)

# Initialize embedding client
embedding_client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    length_function=len,
)


async def get_embedding(text: str) -> list[float]:
    """Generate embedding for text"""
    response = await embedding_client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
        dimensions=settings.embedding_dimension,
    )
    return response.data[0].embedding


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts.

    The OpenAI-like embedding endpoint limits batch sizes (e.g., max 10). This function
    splits the input into batches of size `settings.embedding_batch_size` and calls the
    embedding API multiple times, preserving order.
    """
    if not texts:
        return []

    batch_size = getattr(settings, "embedding_batch_size", 10)
    results: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = await embedding_client.embeddings.create(
            model=settings.openai_embedding_model,
            input=batch,
            dimensions=settings.embedding_dimension,
        )
        # response.data is a list of embeddings corresponding to batch order
        batch_embeddings = [data.embedding for data in response.data]
        results.extend(batch_embeddings)

    return results


async def generate_summary(content: str) -> str:
    """Generate summary for document"""
    messages = [
        SystemMessage(
            content="You are a helpful assistant that generates concise summaries."
        ),
        HumanMessage(
            content=f"Please generate a brief summary (2-3 sentences) for the following document:\n\n{content[:2000]}"
        ),
    ]
    response = await llm.ainvoke(messages)
    return response.content


async def generate_title_and_summary(content: str) -> tuple[str, str]:
    """Generate both a concise title and a brief summary for the document in a single LLM call.

    Returns a tuple (title, summary). If parsing fails, returns ("", summary_from_fallback).
    """
    prompt = f"""请阅读以下文档内容，并生成：
1) 一个简洁精准的标题（15字以内），准确概括文档主旨。
2) 一段简短摘要（2-3句话）。

请仅返回一个JSON对象，格式如下：
{{
  "title": "简短的描述性标题",
  "summary": "两到三句话的摘要内容。"
}}

文档内容：
{content}
"""

    messages = [
        SystemMessage(
            content="You are an expert summarization assistant. Always respond with valid JSON."
        ),
        HumanMessage(content=prompt),
    ]

    response = await llm.ainvoke(messages)
    raw = response.content.strip()

    # Extract JSON from code blocks if present
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(raw)
        title = (
            data.get("title", "").strip()
            if isinstance(data.get("title", ""), str)
            else ""
        )
        summary = (
            data.get("summary", "").strip()
            if isinstance(data.get("summary", ""), str)
            else ""
        )
        return title, summary
    except json.JSONDecodeError:
        # Fallback: attempt to extract lines heuristically
        print(f"Failed to parse JSON for title+summary: {raw}")
        # Try to extract first line as title and generate summary separately
        title_guess = ""
        first_line = content.strip().splitlines()[0] if content.strip() else ""
        if first_line and len(first_line) < 120:
            title_guess = first_line
        # Fallback to generate summary via existing function
        try:
            summary_fallback = await generate_summary(content)
        except Exception:
            summary_fallback = ""
        return title_guess, summary_fallback


async def extract_concepts(
    content: str, title: str, existing_concepts: Optional[list[dict]] = None
) -> dict:
    """Extract concepts and relationships from document

    Args:
        content: Document content
        title: Document title
        existing_concepts: List of existing concepts with 'id', 'name', 'desc'

    Returns:
        dict with 'concepts' (list of {name, desc}) and 'relations' (list of {from, to, desc})
    """
    # Build existing concepts context
    existing_context = ""
    if existing_concepts:
        existing_context = "\n\n现有概念库:\n"
        for concept in existing_concepts:
            existing_context += f"- {concept.get('name')}: {concept.get('desc', '')}\n"

    prompt = f"""请深入分析以下文档，提取核心概念（实体）及其实体间的逻辑关系。

【执行准则】
1. **概念提取 (Concepts)**:
   - **精准凝练**: 仅提取具有独立语义的概念或实体（如地名、人名、机构、技术术语等），严禁提取宽泛、无意义的通用词，也不要提取过于狭义的小众词。
   - **实体对齐 (关键)**: 请先检查【现有概念库】。如果文中概念与库中现有概念同义或指代同一事物（例如文中用“LLM”，库中有“大模型”），**必须直接复用库中的标准名称**，不要创建新词。只有当概念确实是全新的时，才创建新条目。
   - **数量控制**: 提取至少 1 个，不超过 5 个对理解本文最关键的节点，尽量精简，只提取最核心的，除特殊情况外至少提取一个。
   - **定义简洁**: 每个概念的描述 ("desc") 必须控制在 20 字以内，做到言简意赅，突出本质特征，不与特定文档内容绑定。

2. **关系构建 (Relations)**:
   - 可选。仅提取普遍的、文中明确表述的、有事实依据的关系，不要臆断或推测，也不要过于狭隘特殊。
   - 关系描述 ("desc") 必须是简练的谓语动词或短语，禁止使用长句。

【输出格式】
请仅返回一个纯净的 JSON 对象，格式如下：
{{
  "concepts": [
    {{"name": "标准概念名", "desc": "20字以内的精简定义"}}
  ],
  "relations": [
    {{"from": "概念A", "to": "概念B", "desc": "简短关系描述"}}
  ]
}}

【输入数据】
现有概念库: {existing_context}
文档标题: {title}
文档内容: {content}
"""

    print(prompt)

    messages = [
        SystemMessage(
            content="You are an expert at knowledge extraction. Always respond with valid JSON."
        ),
        HumanMessage(content=prompt),
    ]

    response = await llm.ainvoke(messages)
    print("LLM response for concept extraction:", response.content)
    content = response.content.strip()

    # Extract JSON from markdown code blocks if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        result = json.loads(content)
        # Validate structure
        if "concepts" not in result:
            result["concepts"] = []
        if "relations" not in result:
            result["relations"] = []
        return result
    except json.JSONDecodeError:
        print(f"Failed to parse JSON from LLM response: {content}")
        return {"concepts": [], "relations": []}


def chunk_text(text: str) -> list[str]:
    """Split text into chunks"""
    return text_splitter.split_text(text)


def sanitize_text(text: str) -> str:
    """Sanitize text for storage and API calls.

    - Remove null bytes which can break serialization/storage
    - Trim surrounding whitespace
    """
    if not isinstance(text, str):
        return text
    # Remove null bytes and normalize whitespace
    return text.replace("\x00", "").strip()
