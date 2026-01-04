from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime


class ToolFunction(BaseModel):
    """Tool function definition"""
    name: str
    description: str
    parameters: Dict[str, Any]


class Tool(BaseModel):
    """Tool definition"""
    type: Literal["function"] = "function"
    function: ToolFunction


class Message(BaseModel):
    """Internal message format"""
    role: str
    content: str


class LLMRequest(BaseModel):
    """Internal LLM request format"""
    request_id: str
    provider: Literal["openai", "anthropic", "gemini"]
    model: str
    messages: List[Message]
    system: Optional[str] = None
    tools: Optional[List[Tool]] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    timeout_at: datetime


class RequestStatus(BaseModel):
    """Request status information"""
    request_id: str
    status: Literal["pending", "active", "completed", "timeout", "cancelled"]
    created_at: datetime
    timeout_at: datetime
