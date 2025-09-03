#!/usr/bin/env python3
"""
Демонстрация API PromoAI RAG
"""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from services.retrieve.hybrid import HybridRetriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Demo API", version="1.0.0")

# Initialize retriever
retriever = HybridRetriever()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Demo API is running!"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/search")
async def search(query: str, top_k: int = 10):
    """Search endpoint using hybrid retriever."""
    try:
        logger.info(f"Searching for: {query} with top_k={top_k}")

        # Perform search
        results = retriever.retrieve(query, top_k=top_k, use_rerank=False)

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "chunk_id": result["chunk_id"],
                    "doc_id": result["doc_id"],
                    "page": result["page"],
                    "score": result["score"],
                    "snippet": result["snippet"],
                    "breadcrumbs": result["breadcrumbs"],
                }
            )

        return {
            "query": query,
            "results": formatted_results,
            "total": len(formatted_results),
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/rerank")
async def search_with_rerank(query: str, top_k: int = 10, rerank_k: int = 5):
    """Search endpoint with reranking enabled."""
    try:
        logger.info(f"Searching with rerank for: {query}")

        # Perform search with reranking
        results = retriever.retrieve(
            query, top_k=top_k, rerank_k=rerank_k, use_rerank=True
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "chunk_id": result["chunk_id"],
                    "doc_id": result["doc_id"],
                    "page": result["page"],
                    "score": result["score"],
                    "snippet": result["snippet"],
                    "breadcrumbs": result["breadcrumbs"],
                }
            )

        return {
            "query": query,
            "results": formatted_results,
            "total": len(formatted_results),
            "reranked": True,
        }

    except Exception as e:
        logger.error(f"Search with rerank failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500, content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
