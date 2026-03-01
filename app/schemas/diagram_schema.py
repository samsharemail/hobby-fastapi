from pydantic import BaseModel

class DiagramRequest(BaseModel):
    code: str
    detail_level: str  # simple or detailed