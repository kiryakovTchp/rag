"""Answer generation API router."""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.deps import get_db
from api.auth import get_current_user
from api.schemas.answer import AnswerRequest, AnswerResponse
from api.middleware.rate_limit import check_rate_limit, check_daily_quota, update_quota_usage
from services.answer.orchestrator import AnswerOrchestrator
from services.answer.guard import AnswerGuard

router = APIRouter()


@router.post("/answer", response_model=AnswerResponse)
async def generate_answer(
    request: AnswerRequest,
    db: Session = Depends(get_db),
    http_request: Request = None,
    user: dict = Depends(get_current_user)
) -> AnswerResponse:
    """Generate an answer to a query."""
    # Get user info
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    # Check rate limit
    await check_rate_limit(http_request, user_id)
    
    # Validate input
    guard = AnswerGuard()
    guard.validate_query(request.query)
    
    try:
        # Check daily quota (estimate tokens)
        estimated_tokens = len(request.query.split()) * 2  # Rough estimate
        await check_daily_quota(tenant_id, estimated_tokens)
        
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
            tenant_id=tenant_id
        )
        
        # Update quota usage with actual tokens
        if result.get("usage"):
            total_tokens = (result["usage"].get("in_tokens", 0) + 
                          result["usage"].get("out_tokens", 0))
            await update_quota_usage(tenant_id, total_tokens)
        
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
    db: Session = Depends(get_db),
    http_request: Request = None,
    user: dict = Depends(get_current_user)
) -> StreamingResponse:
    """Generate a streaming answer to a query."""
    # Get user info
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    # Check rate limit
    await check_rate_limit(http_request, user_id)
    
    # Validate input
    guard = AnswerGuard()
    guard.validate_query(request.query)
    
    def generate_stream():
        try:
            # Check daily quota (estimate tokens)
            estimated_tokens = len(request.query.split()) * 2  # Rough estimate
            # Note: We can't use await in generator, so quota check is done before
            
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
                tenant_id=tenant_id
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
