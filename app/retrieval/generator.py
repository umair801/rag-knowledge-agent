"""
Answer generation module.
Feeds retrieved chunks to GPT-4o-mini and returns a grounded answer.
"""
import os
from typing import List
from openai import OpenAI
import structlog

logger = structlog.get_logger()

# Initialize client once at module load
_openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an enterprise knowledge base assistant.
Answer the user's question using ONLY the context provided below.
If the answer is not in the context, say: "I don't have enough information in the knowledge base to answer that."
Always be concise, accurate, and cite which source your answer comes from.
Do not make up information."""


def build_context(chunks: List[dict]) -> str:
    """Format retrieved chunks into a context block for the prompt."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("filename") or chunk.get("source_url") or "Unknown"
        context_parts.append(
            f"[Source {i}: {source}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(context_parts)


def generate_answer(
    query: str,
    chunks: List[dict],
    chat_history: List[dict] | None = None,
) -> str:
    """
    Generate a grounded answer using GPT-4o-mini.

    Args:
        query: User's question
        chunks: Retrieved context chunks from Pinecone
        chat_history: Optional prior messages for multi-turn context

    Returns:
        Answer string
    """
    if not chunks:
        return "I don't have enough information in the knowledge base to answer that."

    client = _openai_client
    context = build_context(chunks)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add chat history if present (for multi-turn, added in Step 5)
    if chat_history:
        messages.extend(chat_history)

    # Add context + question
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {query}",
    })

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,  # Low temp = more factual, less creative
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        logger.info("answer_generated", query=query[:60], tokens=response.usage.total_tokens)
        return answer

    except Exception as e:
        logger.error("generation_failed", error=str(e))
        raise