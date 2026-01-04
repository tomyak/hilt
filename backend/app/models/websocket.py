from pydantic import BaseModel
from typing import Literal, Optional, Any, Dict
from app.models.request import LLMRequest
from app.models.response import ToolCall


# Server → Client messages

class NewRequestMessage(BaseModel):
    """Notify UI of new LLM request"""
    type: Literal["new_request"] = "new_request"
    data: LLMRequest


class RequestCancelledMessage(BaseModel):
    """Notify UI that request was cancelled"""
    type: Literal["request_cancelled"] = "request_cancelled"
    data: Dict[str, str]  # {"request_id": "...", "reason": "..."}


class RequestTimeoutWarningMessage(BaseModel):
    """Warn UI that request is about to timeout"""
    type: Literal["request_timeout_warning"] = "request_timeout_warning"
    data: Dict[str, Any]  # {"request_id": "...", "seconds_remaining": 60}


class StatsUpdateMessage(BaseModel):
    """Update UI with stats"""
    type: Literal["stats_update"] = "stats_update"
    data: Dict[str, int]  # {"pending_requests": 2, "active_operators": 3}


class ErrorMessage(BaseModel):
    """Error message to UI"""
    type: Literal["error"] = "error"
    data: Dict[str, str]  # {"request_id": "...", "error_code": "...", "message": "..."}


# Client → Server messages

class StartResponseMessage(BaseModel):
    """Operator starts responding"""
    type: Literal["start_response"] = "start_response"
    data: Dict[str, str]  # {"request_id": "...", "mode": "streaming" | "batch"}


class ResponseChunkMessage(BaseModel):
    """Streaming response chunk from operator"""
    type: Literal["response_chunk"] = "response_chunk"
    data: Dict[str, Optional[str]]  # {"request_id": "...", "content": "..."}


class CompleteResponseMessage(BaseModel):
    """Complete response from operator (batch mode)"""
    type: Literal["complete_response"] = "complete_response"
    data: Dict[str, Any]  # {"request_id": "...", "content": "...", "tool_calls": [...], "finish_reason": "..."}


class AddToolCallMessage(BaseModel):
    """Add tool call to response (streaming mode)"""
    type: Literal["add_tool_call"] = "add_tool_call"
    data: Dict[str, Any]  # {"request_id": "...", "tool_call": {...}}


class FinishResponseMessage(BaseModel):
    """Finish streaming response"""
    type: Literal["finish_response"] = "finish_response"
    data: Dict[str, str]  # {"request_id": "...", "finish_reason": "..."}


class RejectRequestMessage(BaseModel):
    """Reject/cancel a request"""
    type: Literal["reject_request"] = "reject_request"
    data: Dict[str, str]  # {"request_id": "...", "reason": "...", "message": "..."}
