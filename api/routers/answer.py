"""Answer generation API router."""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.dependencies.db import get_db_lazy
from api.schemas.answer import AnswerRequest, AnswerResponse
from api.middleware.rate_limit import check_quota, get_remaining_quota
from services.answer.orchestrator import AnswerOrchestrator

router = APIRouter()


@router.post("/answer", response_model=AnswerResponse)
async def generate_answer(
    request: AnswerRequest,
    db: Session = Depends(get_db_lazy),
    user: "User" = Depends(get_current_user)
) -> AnswerResponse:
    """Generate an answer to a query."""
    # Check daily quota (estimate tokens)
    estimated_tokens = len(request.query.split()) * 2  # Rough estimate
    if not check_quota(user.tenant_id, estimated_tokens):
        remaining = get_remaining_quota(user.tenant_id)
        raise HTTPException(
            status_code=402,
            detail=f"Daily token quota exceeded. Remaining: {remaining} tokens"
        )
    
    try:
        # Generate answer
        orchestrator = AnswerOrchestrator(db)
        result = orchestrator.generate_answer(
            query=request.query,
            top_k=request.top_k,
            rerank=request.rerank,
            max_ctx_tokens=request.max_ctx,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout_s=request.timeout_s,
            tenant_id=user.tenant_id
        )
        
        # Log answer usage
        if result.get("usage"):
            usage = result["usage"]
            # Lazy import for AnswerLog
            from db.models import AnswerLog
            answer_log = AnswerLog(
                tenant_id=user.tenant_id,
                query=request.query,
                provider=usage.get("provider", "unknown"),
                model=usage.get("model", "unknown"),
                in_tokens=usage.get("in_tokens", 0),
                out_tokens=usage.get("out_tokens", 0),
                latency_ms=usage.get("latency_ms", 0),
                cost_usd=str(usage.get("cost_usd", 0))
            )
            db.add(answer_log)
            db.commit()
        
        return AnswerResponse(
            answer=result["answer"],
            citations=result["citations"],
            usage=result["usage"]
        )
        
    except Exception as e:
        if "LLM_UNAVAILABLE" in str(e):
            raise HTTPException(
                status_code=503,
                detail=f"LLM service unavailable: {str(e)}"
            )
        elif "No relevant context" in str(e):
            raise HTTPException(
                status_code=404,
                detail="No relevant context found for the query"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Answer generation failed: {str(e)}"
            )


@router.post("/answer/stream")
async def stream_answer(
    request: AnswerRequest,
    db: Session = Depends(get_db_lazy),
    user: "User" = Depends(get_current_user)
) -> StreamingResponse:
    """Generate a streaming answer to a query."""
    # Check daily quota (estimate tokens)
    estimated_tokens = len(request.query.split()) * 2  # Rough estimate
    if not check_quota(user.tenant_id, estimated_tokens):
        remaining = get_remaining_quota(user.tenant_id)
        raise HTTPException(
            status_code=402,
            detail=f"Daily token quota exceeded. Remaining: {remaining} tokens"
        )
    
    def generate_stream():
        try:
            # Generate streaming answer
            orchestrator = AnswerOrchestrator(db)
            stream = orchestrator.stream_answer(
                query=request.query,
                top_k=request.top_k,
                rerank=request.rerank,
                max_ctx_tokens=request.max_ctx,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                timeout_s=request.timeout_s,
                tenant_id=user.tenant_id
            )
            
            for chunk in stream:
                if chunk["type"] == "chunk":
                    yield f"event: chunk\ndata: {json.dumps({'text': chunk['text']})}\n\n"
                elif chunk["type"] == "done":
                    yield f"event: done\ndata: {json.dumps({'citations': chunk['citations'], 'usage': chunk['usage']})}\n\n"
                    
        except Exception as e:
            error_data = {"error": str(e)}
            if "LLM_UNAVAILABLE" in str(e):
                error_data["code"] = "LLM_UNAVAILABLE"
            elif "No relevant context" in str(e):
                error_data["code"] = "NO_CONTEXT"
            
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )
