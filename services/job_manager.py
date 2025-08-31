"""Job management for pipeline tasks."""

import asyncio
from typing import Dict, Any
from datetime import datetime
from api.websocket import emit_job_event

class JobManager:
    """Manage job lifecycle and WebSocket events."""
    
    def __init__(self):
        self.jobs: Dict[int, Dict[str, Any]] = {}
        self.job_counter = 0
    
    def create_job(self, document_id: int, job_type: str, tenant_id: str) -> int:
        """Create a new job."""
        self.job_counter += 1
        job_id = self.job_counter
        
        self.jobs[job_id] = {
            "id": job_id,
            "document_id": document_id,
            "type": job_type,
            "tenant_id": tenant_id,
            "status": "created",
            "progress": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        return job_id
    
    async def emit_event(self, job_id: int, event: str, progress: int = 0, error: str = None):
        """Emit job event to WebSocket clients."""
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        job["status"] = event
        job["progress"] = progress
        job["updated_at"] = datetime.utcnow()
        
        if error:
            job["error"] = error
        
        event_data = {
            "event": event,
            "job_id": job_id,
            "document_id": job["document_id"],
            "type": job["type"],
            "progress": progress
        }
        
        if error:
            event_data["error"] = error
        
        await emit_job_event(job["tenant_id"], event_data)
    
    async def job_started(self, job_id: int):
        """Job started event."""
        await self.emit_event(job_id, "started", 0)
    
    async def job_progress(self, job_id: int, progress: int):
        """Job progress event."""
        await self.emit_event(job_id, "progress", progress)
    
    async def job_done(self, job_id: int):
        """Job completed successfully."""
        await self.emit_event(job_id, "done", 100)
    
    async def job_failed(self, job_id: int, error: str):
        """Job failed event."""
        await self.emit_event(job_id, "failed", 0, error)

# Global job manager instance
job_manager = JobManager()
