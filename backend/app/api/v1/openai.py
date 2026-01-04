import uuid
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.schemas.openai import (
    OpenAIChatCompletionRequest,
    OpenAIChatCompletionResponse,
    OpenAIChoice,
    OpenAIMessageResponse,
    OpenAIUsage,
    OpenAIToolCall,
    OpenAIToolCallFunction,
    OpenAIChatCompletionChunk,
    OpenAIStreamingChoice,
    OpenAIDelta
)
from app.models.request import LLMRequest, Message, Tool, ToolFunction
from app.models.response import ToolCall as InternalToolCall
from app.core.security import validate_api_key
from app.services.request_manager import request_manager
from app.services.websocket_manager import websocket_manager
from app.config import settings
from app.core.rate_limit import limiter

router = APIRouter()


def convert_openai_to_internal(openai_request: OpenAIChatCompletionRequest, request_id: str) -> LLMRequest:
    """Convert OpenAI request to internal format"""
    # Extract system message
    system_message = None
    messages = []

    for msg in openai_request.messages:
        if msg.role == "system":
            system_message = msg.content
        else:
            messages.append(Message(role=msg.role, content=msg.content or ""))

    # Convert tools
    tools = None
    if openai_request.tools:
        tools = [
            Tool(
                type="function",
                function=ToolFunction(
                    name=tool.function.name,
                    description=tool.function.description,
                    parameters=tool.function.parameters.dict()
                )
            )
            for tool in openai_request.tools
        ]

    # Create internal request
    return LLMRequest(
        request_id=request_id,
        provider="openai",
        model=openai_request.model,
        messages=messages,
        system=system_message,
        tools=tools,
        parameters={
            "temperature": openai_request.temperature,
            "top_p": openai_request.top_p,
            "max_tokens": openai_request.max_tokens,
            "presence_penalty": openai_request.presence_penalty,
            "frequency_penalty": openai_request.frequency_penalty,
        },
        timeout_at=datetime.utcnow() + timedelta(seconds=settings.REQUEST_TIMEOUT_SECONDS)
    )


def convert_internal_to_openai(response, request_id: str, model: str) -> OpenAIChatCompletionResponse:
    """Convert internal response to OpenAI format"""
    # Convert tool calls
    tool_calls = None
    if response.tool_calls:
        tool_calls = [
            OpenAIToolCall(
                id=tc.id,
                type="function",
                function=OpenAIToolCallFunction(
                    name=tc.function.name,
                    arguments=tc.function.arguments
                )
            )
            for tc in response.tool_calls
        ]

    message = OpenAIMessageResponse(
        role="assistant",
        content=response.content if response.content else None,
        tool_calls=tool_calls
    )

    choice = OpenAIChoice(
        index=0,
        message=message,
        finish_reason=response.finish_reason
    )

    # Mock usage (we don't actually count tokens)
    usage = OpenAIUsage(
        prompt_tokens=10,
        completion_tokens=len(response.content.split()) if response.content else 0,
        total_tokens=10 + (len(response.content.split()) if response.content else 0)
    )

    return OpenAIChatCompletionResponse(
        id=f"chatcmpl-{request_id[:8]}",
        object="chat.completion",
        created=int(time.time()),
        model=model,
        choices=[choice],
        usage=usage
    )


@router.post("/chat/completions")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat_completions(
    request: Request,
    openai_request: OpenAIChatCompletionRequest,
    api_key: str = Depends(validate_api_key)
):
    """
    OpenAI-compatible chat completions endpoint.
    Blocks until human operator provides response.
    """
    # Generate request ID
    request_id = str(uuid.uuid4())

    # Convert to internal format
    internal_request = convert_openai_to_internal(openai_request, request_id)

    # Create request and get future
    future = await request_manager.create_request(internal_request)

    # Broadcast to all connected operators
    await websocket_manager.broadcast_new_request(internal_request)

    # If streaming requested, return SSE stream
    if openai_request.stream:
        return StreamingResponse(
            stream_openai_response(request_id, openai_request.model),
            media_type="text/event-stream"
        )

    # Wait for response (blocks here)
    response = await request_manager.wait_for_response(
        request_id,
        timeout=settings.REQUEST_TIMEOUT_SECONDS
    )

    # Convert back to OpenAI format
    openai_response = convert_internal_to_openai(response, request_id, openai_request.model)

    return openai_response


async def stream_openai_response(request_id: str, model: str):
    """
    Generator for streaming OpenAI responses.
    Yields Server-Sent Events (SSE) format.
    """
    import json
    import asyncio

    # Wait for human to start responding
    try:
        response = await request_manager.wait_for_response(
            request_id,
            timeout=settings.REQUEST_TIMEOUT_SECONDS
        )

        # For now, send the complete response as a single chunk
        # (Full streaming implementation would require monitoring the streaming buffer)
        chunk = OpenAIChatCompletionChunk(
            id=f"chatcmpl-{request_id[:8]}",
            object="chat.completion.chunk",
            created=int(time.time()),
            model=model,
            choices=[
                OpenAIStreamingChoice(
                    index=0,
                    delta=OpenAIDelta(
                        role="assistant",
                        content=response.content
                    ),
                    finish_reason=None
                )
            ]
        )

        yield f"data: {chunk.json()}\n\n"

        # Final chunk with finish_reason
        final_chunk = OpenAIChatCompletionChunk(
            id=f"chatcmpl-{request_id[:8]}",
            object="chat.completion.chunk",
            created=int(time.time()),
            model=model,
            choices=[
                OpenAIStreamingChoice(
                    index=0,
                    delta=OpenAIDelta(),
                    finish_reason=response.finish_reason
                )
            ]
        )

        yield f"data: {final_chunk.json()}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        # Send error and close stream
        error_data = {"error": {"message": str(e), "type": "server_error"}}
        yield f"data: {json.dumps(error_data)}\n\n"
