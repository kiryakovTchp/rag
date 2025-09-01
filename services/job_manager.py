"""Job manager for WebSocket event emission."""

import asyncio
from datetime import datetime
from typing import Optional
from services.events.bus import publish_event


class JobManager:
    """Manage job events and WebSocket emission."""
    
    def __init__(self):
        self.heartbeat_interval = 5  # seconds
    
    async def job_started(self, job_id: int, tenant_id: str = "", document_id: Optional[int] = None, job_type: Optional[str] = None):
        """Emit job started event."""
        if not tenant_id:
            return
            
        topic = f"{tenant_id}.jobs"
        event_data = {
            "event": f"{job_type or 'job'}_started",
            "job_id": job_id,
            "document_id": document_id,
            "type": job_type or "job",
            "progress": 0,
            "ts": datetime.utcnow().isoformat()
        }
        await publish_event(topic, event_data)
    
    async def job_progress(self, job_id: int, progress: int, tenant_id: str = "", document_id: Optional[int] = None, job_type: Optional[str] = None):
        """Emit job progress event."""
        if not tenant_id:
            return
            
        topic = f"{tenant_id}.jobs"
        event_data = {
            "event": f"{job_type or 'job'}_progress",
            "job_id": job_id,
            "document_id": document_id,
            "type": job_type or "job",
            "progress": progress,
            "ts": datetime.utcnow().isoformat()
        }
        await publish_event(topic, event_data)
    
    async def job_done(self, job_id: int, tenant_id: str = "", document_id: Optional[int] = None, job_type: Optional[str] = None):
        """Emit job done event."""
        if not tenant_id:
            return
            
        topic = f"{tenant_id}.jobs"
        event_data = {
            "event": f"{job_type or 'job'}_done",
            "job_id": job_id,
            "document_id": document_id,
            "type": job_type or "job",
            "progress": 100,
            "ts": datetime.utcnow().isoformat()
        }
        await publish_event(topic, event_data)
    
    async def job_failed(self, job_id: int, error: str, tenant_id: str = "", document_id: Optional[int] = None, job_type: Optional[str] = None):
        """Emit job failed event."""
        if not tenant_id:
            return
            
        topic = f"{tenant_id}.jobs"
        event_data = {
            "event": f"{job_type or 'job'}_failed",
            "job_id": job_id,
            "document_id": document_id,
            "type": job_type or "job",
            "progress": 0,
            "error": error,
            "ts": datetime.utcnow().isoformat()
        }
        await publish_event(topic, event_data)
    
    async def heartbeat(self, job_id: int, tenant_id: str = "", document_id: Optional[int] = None, job_type: Optional[str] = None):
        """Emit heartbeat event."""
        if not tenant_id:
            return
            
        topic = f"{tenant_id}.jobs"
        event_data = {
            "event": "heartbeat",
            "job_id": job_id,
            "document_id": document_id,
            "type": job_type or "job",
            "ts": datetime.utcnow().isoformat()
        }
        await publish_event(topic, event_data)


# Global instance
job_manager = JobManager()
