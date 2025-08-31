"""Prompt builder for answer generation."""

import tiktoken
from typing import List, Tuple
from db.models import Chunk


def build_messages(query: str, contexts: List[Chunk], max_ctx_tokens: int) -> Tuple[List[dict], int]:
    """Build messages for LLM generation.
    
    Args:
        query: User query
        contexts: List of relevant chunks
        max_ctx_tokens: Maximum context tokens
        
    Returns:
        Tuple of (messages, remaining_tokens)
    """
    # System instructions
    system_instruction = """Отвечай кратко и только по данным из контекста.
Обязательно цитируй источники в тексте в формате [doc:{doc_id} chunk:{chunk_id}].
Если ответа в контексте нет, ответь: "Не найдено в источниках."."""
    
    # Build context from chunks
    context_parts = []
    total_tokens = 0
    
    # Estimate tokens for system + query
    encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
    system_tokens = len(encoding.encode(system_instruction))
    query_tokens = len(encoding.encode(query))
    
    # Reserve tokens for system + query + some buffer
    reserved_tokens = system_tokens + query_tokens + 100
    available_tokens = max_ctx_tokens - reserved_tokens
    
    for chunk in contexts:
        # Clean and prepare chunk text
        chunk_text = chunk.text.strip()
        if not chunk_text:
            continue
        
        # Add chunk metadata
        chunk_info = f"[doc:{chunk.document_id} chunk:{chunk.id}"
        if chunk.page:
            chunk_info += f" page:{chunk.page}"
        chunk_info += "]"
        
        full_chunk = f"{chunk_info}\n{chunk_text}\n"
        
        # Estimate tokens for this chunk
        chunk_tokens = len(encoding.encode(full_chunk))
        
        if total_tokens + chunk_tokens <= available_tokens:
            context_parts.append(full_chunk)
            total_tokens += chunk_tokens
        else:
            break
    
    # Build context text
    context_text = "\n\n".join(context_parts)
    
    # Build user message with system instruction
    user_message = f"{system_instruction}\n\nКонтекст:\n{context_text}\n\nВопрос: {query}"
    
    messages = [
        {"role": "user", "content": user_message}
    ]
    
    remaining_tokens = available_tokens - total_tokens
    
    return messages, remaining_tokens
