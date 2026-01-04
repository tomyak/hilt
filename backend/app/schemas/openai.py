from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal, Union


# Request schemas

class OpenAIMessage(BaseModel):
    """OpenAI chat message"""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class OpenAIFunctionParameters(BaseModel):
    """Function parameters schema"""
    type: str = "object"
    properties: Dict[str, Any]
    required: Optional[List[str]] = None


class OpenAIFunction(BaseModel):
    """Function definition"""
    name: str
    description: str
    parameters: OpenAIFunctionParameters


class OpenAITool(BaseModel):
    """Tool definition"""
    type: Literal["function"] = "function"
    function: OpenAIFunction


class OpenAIChatCompletionRequest(BaseModel):
    """OpenAI chat completion request"""
    model: str
    messages: List[OpenAIMessage]
    temperature: Optional[float] = Field(default=1.0, ge=0, le=2)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    n: Optional[int] = Field(default=1, ge=1, le=10)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = Field(default=None, gt=0)
    presence_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    tools: Optional[List[OpenAITool]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    user: Optional[str] = None


# Response schemas

class OpenAIToolCallFunction(BaseModel):
    """Tool call function details"""
    name: str
    arguments: str  # JSON string


class OpenAIToolCall(BaseModel):
    """Tool call in response"""
    id: str
    type: Literal["function"] = "function"
    function: OpenAIToolCallFunction


class OpenAIMessageResponse(BaseModel):
    """Message in response"""
    role: Literal["assistant"]
    content: Optional[str] = None
    tool_calls: Optional[List[OpenAIToolCall]] = None


class OpenAIChoice(BaseModel):
    """Choice in response"""
    index: int
    message: OpenAIMessageResponse
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter"]] = None


class OpenAIUsage(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIChatCompletionResponse(BaseModel):
    """OpenAI chat completion response"""
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[OpenAIChoice]
    usage: OpenAIUsage


# Streaming response schemas

class OpenAIDelta(BaseModel):
    """Delta for streaming response"""
    role: Optional[Literal["assistant"]] = None
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class OpenAIStreamingChoice(BaseModel):
    """Streaming choice"""
    index: int
    delta: OpenAIDelta
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter"]] = None


class OpenAIChatCompletionChunk(BaseModel):
    """OpenAI streaming chunk"""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[OpenAIStreamingChoice]
