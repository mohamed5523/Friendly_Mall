from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    role: str
    email: str


class ChatRequest(BaseModel):
    query: str
    role: str = "customer"          # "customer" | "manager"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    context_count: int = 0
    model_used: str = ""
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime