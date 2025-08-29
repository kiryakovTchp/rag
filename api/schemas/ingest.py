from pydantic import BaseModel


class IngestResponse(BaseModel):
    job_id: str
    status: str


class IngestRequest(BaseModel):
    # TODO: Add fields as needed
    pass
