"""Initialize database with mock data"""

import asyncio

from app.database import db
from app.utils import get_embedding


async def init_mock_data():
    """Initialize database with mock data for testing"""
    db.connect()

    print("Initializing database schema...")
    db.init_schema()

    print("Creating mock documents...")

    # Mock Document 1: Machine Learning
    ml_content = """Machine Learning is a subset of artificial intelligence that focuses on the development of algorithms and statistical models that enable computers to improve their performance on a specific task through experience.

The core idea is to build systems that can learn from and make decisions based on data. Machine learning algorithms can be categorized into three main types: supervised learning, unsupervised learning, and reinforcement learning.

Neural networks are a key technique in modern machine learning, inspired by the structure and function of the human brain. Deep learning, which uses multi-layered neural networks, has achieved remarkable success in areas like image recognition, natural language processing, and game playing."""

    ml_summary = "An overview of machine learning, its core concepts, and main approaches including supervised, unsupervised learning and neural networks."

    doc1_id = db.create_doc(
        title="Introduction to Machine Learning",
        summary=ml_summary,
        content=ml_content,
        doc_type="text",
        meta={"author": "System", "source": "mock"},
    )

    # Mock Document 2: Deep Learning
    dl_content = """Deep Learning is a specialized branch of machine learning that uses artificial neural networks with multiple layers (deep neural networks) to progressively extract higher-level features from raw input.

The "deep" in deep learning refers to the number of layers in the network. Traditional neural networks might have 2-3 layers, while deep networks can have dozens or even hundreds of layers.

Deep learning has revolutionized many fields including computer vision, natural language processing, and speech recognition. Key architectures include Convolutional Neural Networks (CNNs) for image processing and Recurrent Neural Networks (RNNs) for sequence data."""

    dl_summary = "Deep learning uses multi-layered neural networks to learn hierarchical representations, achieving breakthroughs in vision, NLP, and more."

    doc2_id = db.create_doc(
        title="Deep Learning Fundamentals",
        summary=dl_summary,
        content=dl_content,
        doc_type="text",
        meta={"author": "System", "source": "mock"},
    )

    # Mock Document 3: Natural Language Processing
    nlp_content = """Natural Language Processing (NLP) is a field at the intersection of computer science, artificial intelligence, and linguistics. Its goal is to enable computers to understand, interpret, and generate human language in a valuable way.

NLP encompasses a wide range of tasks including text classification, sentiment analysis, machine translation, question answering, and text generation. Modern NLP heavily relies on deep learning techniques, particularly transformer models like BERT and GPT.

The transformer architecture, introduced in 2017, has become the dominant paradigm in NLP. It uses attention mechanisms to process sequential data more effectively than previous approaches."""

    nlp_summary = "NLP enables computers to understand and generate human language, with modern approaches based on transformer architectures."

    doc3_id = db.create_doc(
        title="Natural Language Processing Overview",
        summary=nlp_summary,
        content=nlp_content,
        doc_type="text",
        meta={"author": "System", "source": "mock"},
    )

    print("Creating mock concepts...")

    # Create concepts (human-readable names; preserve spaces and case)
    concepts_data = [
        (
            "Machine Learning",
            "A subset of AI focused on algorithms that learn from data",
        ),
        ("Neural Network", "Computing systems inspired by biological neural networks"),
        ("Deep Learning", "Machine learning using multi-layered neural networks"),
        ("Supervised Learning", "Learning from labeled training data"),
        ("Unsupervised Learning", "Learning from unlabeled data to find patterns"),
        (
            "Natural Language Processing",
            "AI field focused on understanding and generating human language",
        ),
        ("Transformer", "Neural network architecture using attention mechanisms"),
        (
            "Computer Vision",
            "Field focused on enabling computers to understand visual information",
        ),
    ]

    concept_ids = {}
    for name, desc in concepts_data:
        embedding = await get_embedding(f"{name}: {desc}")
        concept_id = db.create_concept(name, desc, embedding)
        concept_ids[name] = concept_id

    print("Creating relationships...")

    # Create mentions (doc -> concept)
    db.create_mention(doc1_id, concept_ids["Machine Learning"], "primary topic")
    db.create_mention(doc1_id, concept_ids["Neural Network"], "discussed technique")
    db.create_mention(doc1_id, concept_ids["Supervised Learning"], "learning type")
    db.create_mention(doc1_id, concept_ids["Unsupervised Learning"], "learning type")

    db.create_mention(doc2_id, concept_ids["Deep Learning"], "primary topic")
    db.create_mention(doc2_id, concept_ids["Neural Network"], "core technique")
    db.create_mention(doc2_id, concept_ids["Computer Vision"], "application area")

    db.create_mention(
        doc3_id, concept_ids["Natural Language Processing"], "primary topic"
    )
    db.create_mention(doc3_id, concept_ids["Transformer"], "key architecture")
    db.create_mention(doc3_id, concept_ids["Deep Learning"], "underlying technique")

    # Create concept relationships
    db.create_related(
        concept_ids["Deep Learning"],
        concept_ids["Machine Learning"],
        "is a specialized branch of",
    )
    db.create_related(
        concept_ids["Neural Network"],
        concept_ids["Machine Learning"],
        "is a key technique in",
    )
    db.create_related(
        concept_ids["Transformer"],
        concept_ids["Deep Learning"],
        "is an architecture used in",
    )
    db.create_related(
        concept_ids["Natural Language Processing"],
        concept_ids["Deep Learning"],
        "heavily relies on",
    )
    db.create_related(
        concept_ids["Computer Vision"],
        concept_ids["Deep Learning"],
        "heavily relies on",
    )

    # Create chunks for better retrieval
    print("Creating chunks...")
    chunks = [
        (ml_content[:500], doc1_id),
        (ml_content[500:1000], doc1_id),
        (ml_content[1000:], doc1_id),
        (dl_content[:500], doc2_id),
        (dl_content[500:1000], doc2_id),
        (dl_content[1000:], doc2_id),
        (nlp_content[:500], doc3_id),
        (nlp_content[500:1000], doc3_id),
        (nlp_content[1000:], doc3_id),
    ]

    for i, (text, source_id) in enumerate(chunks, 1):
        if text.strip():
            chunk_embedding = await get_embedding(text)
            chunk_id = db.create_chunk(text, chunk_embedding, source_id)
            if chunk_id:
                print(f"  Created chunk {i}/{len(chunks)}: {chunk_id[:50]}...")
            else:
                print(f"  Failed to create chunk {i}/{len(chunks)}")

    print("Mock data initialized successfully!")
    print(
        f"Created 3 documents, {len(concepts_data)} concepts, and {len(chunks)} chunks"
    )


if __name__ == "__main__":
    asyncio.run(init_mock_data())
