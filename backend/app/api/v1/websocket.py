import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import get_user_from_ws_token
from app.services.websocket_manager import websocket_manager
from app.services.request_manager import request_manager
from app.models.response import LLMResponse, ToolCall, ToolCallFunction

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for UI operators.
    Authenticates via JWT token in query parameter.
    """
    # Authenticate user from token
    try:
        username = get_user_from_ws_token(token)
    except Exception as e:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # Accept connection
    await websocket_manager.connect(websocket, username)

    # Send initial stats
    stats = request_manager.get_stats()
    await websocket_manager.send_personal(username, {
        "type": "stats_update",
        "data": stats
    })

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")
            message_data = message.get("data", {})

            # Handle different message types
            if message_type == "start_response":
                await handle_start_response(username, message_data)

            elif message_type == "response_chunk":
                await handle_response_chunk(username, message_data)

            elif message_type == "complete_response":
                await handle_complete_response(username, message_data)

            elif message_type == "add_tool_call":
                await handle_add_tool_call(username, message_data)

            elif message_type == "finish_response":
                await handle_finish_response(username, message_data)

            elif message_type == "reject_request":
                await handle_reject_request(username, message_data)

            else:
                await websocket_manager.send_error(
                    username,
                    "UNKNOWN_MESSAGE_TYPE",
                    f"Unknown message type: {message_type}"
                )

    except WebSocketDisconnect:
        await websocket_manager.disconnect(username)
    except Exception as e:
        print(f"WebSocket error for {username}: {e}")
        await websocket_manager.disconnect(username)


async def handle_start_response(username: str, data: dict):
    """Handle operator starting to respond"""
    request_id = data.get("request_id")
    mode = data.get("mode", "batch")

    if mode == "streaming":
        # Initialize streaming buffer
        await request_manager.start_streaming(request_id)


async def handle_response_chunk(username: str, data: dict):
    """Handle streaming response chunk"""
    request_id = data.get("request_id")
    content = data.get("content", "")

    try:
        await request_manager.add_chunk(request_id, content)
    except Exception as e:
        await websocket_manager.send_error(
            username,
            "CHUNK_ERROR",
            str(e),
            request_id
        )


async def handle_complete_response(username: str, data: dict):
    """Handle complete response (batch mode)"""
    request_id = data.get("request_id")
    content = data.get("content", "")
    tool_calls_data = data.get("tool_calls", [])
    finish_reason = data.get("finish_reason", "stop")

    # Convert tool calls
    tool_calls = None
    if tool_calls_data:
        tool_calls = [
            ToolCall(
                id=tc.get("id"),
                type="function",
                function=ToolCallFunction(
                    name=tc.get("function", {}).get("name"),
                    arguments=tc.get("function", {}).get("arguments")
                )
            )
            for tc in tool_calls_data
        ]

    # Create response
    response = LLMResponse(
        request_id=request_id,
        content=content,
        tool_calls=tool_calls,
        finish_reason=finish_reason
    )

    try:
        # Submit response
        await request_manager.submit_response(request_id, response)

        # Broadcast stats update
        stats = request_manager.get_stats()
        await websocket_manager.broadcast_stats(stats)

    except Exception as e:
        await websocket_manager.send_error(
            username,
            "SUBMIT_ERROR",
            str(e),
            request_id
        )


async def handle_add_tool_call(username: str, data: dict):
    """Handle adding a tool call (streaming mode)"""
    request_id = data.get("request_id")
    tool_call_data = data.get("tool_call", {})

    try:
        tool_call = ToolCall(
            id=tool_call_data.get("id"),
            type="function",
            function=ToolCallFunction(
                name=tool_call_data.get("function", {}).get("name"),
                arguments=tool_call_data.get("function", {}).get("arguments")
            )
        )

        await request_manager.add_tool_call(request_id, tool_call)

    except Exception as e:
        await websocket_manager.send_error(
            username,
            "TOOL_CALL_ERROR",
            str(e),
            request_id
        )


async def handle_finish_response(username: str, data: dict):
    """Handle finishing streaming response"""
    request_id = data.get("request_id")
    finish_reason = data.get("finish_reason", "stop")

    try:
        # Finish streaming and submit
        await request_manager.finish_streaming(request_id, finish_reason)

        # Broadcast stats update
        stats = request_manager.get_stats()
        await websocket_manager.broadcast_stats(stats)

    except Exception as e:
        await websocket_manager.send_error(
            username,
            "FINISH_ERROR",
            str(e),
            request_id
        )


async def handle_reject_request(username: str, data: dict):
    """Handle rejecting a request"""
    request_id = data.get("request_id")
    reason = data.get("reason", "rejected")

    try:
        # Cancel the request
        await request_manager.cancel_request(request_id, reason)

        # Broadcast cancellation
        await websocket_manager.broadcast_request_cancelled(request_id, reason)

        # Broadcast stats update
        stats = request_manager.get_stats()
        await websocket_manager.broadcast_stats(stats)

    except Exception as e:
        await websocket_manager.send_error(
            username,
            "REJECT_ERROR",
            str(e),
            request_id
        )
