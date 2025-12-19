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
    """Generate embeddings for multiple texts"""
    response = await embedding_client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
        dimensions=settings.embedding_dimension,
    )
    return [data.embedding for data in response.data]


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


async def extract_concepts(content: str, title: str) -> dict:
    """Extract concepts and relationships from document

    Returns:
        dict with 'concepts' (list of {name, desc}) and 'relations' (list of {from, to, desc})
    """
    prompt = f"""Analyze the following document and extract key concepts and their relationships.

Document Title: {title}
Document Content: {content[:3000]}

Please respond with a JSON object containing:
1. "concepts": A list of important concepts/entities, each with "name" and "desc" (one-sentence definition)
2. "relations": A list of relationships between concepts, each with "from" (concept name), "to" (concept name), and "desc"

Guidelines:
- Concept names should be human-readable and may include spaces and capitalization (e.g., "Machine Learning").
- Extract 3-8 most important concepts
- Only include clear, meaningful relationships
- Use simple relationship descriptions

Example format:
{{
  "concepts": [
    {{"name": "Machine Learning", "desc": "A field of AI that enables computers to learn from data"}},
    {{"name": "Neural Network", "desc": "A computing system inspired by biological neural networks"}}
  ],
  "relations": [
    {{"from": "Neural Network", "to": "Machine Learning", "desc": "is a technique used in"}}
  ]
}}

Respond with valid JSON only, no additional text."""

    messages = [
        SystemMessage(
            content="You are an expert at knowledge extraction. Always respond with valid JSON."
        ),
        HumanMessage(content=prompt),
    ]

    response = await llm.ainvoke(messages)
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
