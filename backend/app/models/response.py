from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ToolCallFunction(BaseModel):
    """Tool call function details"""
    name: str
    arguments: str  # JSON string


class ToolCall(BaseModel):
    """Tool call in response"""
    id: str
    type: Literal["function"] = "function"
    function: ToolCallFunction


class LLMResponse(BaseModel):
    """Internal LLM response format"""
    request_id: str
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Literal["stop", "tool_calls", "length"] = "stop"


class StreamingChunk(BaseModel):
    """Streaming response chunk"""
    request_id: str
    content: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    finish_reason: Optional[Literal["stop", "tool_calls", "length"]] = None
