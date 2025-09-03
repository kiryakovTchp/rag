"""Answer usage logging service."""

from typing import Optional

from sqlalchemy.orm import Session

from db.models import AnswerLog


def log_answer_usage(
    db: Session,
    tenant_id: Optional[str],
    query: str,
    provider: str,
    model: str,
    in_tokens: Optional[int],
    out_tokens: Optional[int],
    latency_ms: int,
    cost_usd: Optional[float],
) -> None:
    """Log answer usage to database.

    Args:
        db: Database session
        tenant_id: Tenant identifier
        query: User query
        provider: LLM provider name
        model: Model name
        in_tokens: Input tokens
        out_tokens: Output tokens
        latency_ms: Response latency in milliseconds
        cost_usd: Cost in USD (if known)
    """
    # Convert cost to string if provided
    cost_str = None
    if cost_usd is not None:
        cost_str = f"{cost_usd:.6f}"

    # Create log entry
    log_entry = AnswerLog(
        tenant_id=tenant_id,
        query=query,
        provider=provider,
        model=model,
        in_tokens=in_tokens,
        out_tokens=out_tokens,
        latency_ms=latency_ms,
        cost_usd=cost_str,
    )

    db.add(log_entry)
    db.commit()
