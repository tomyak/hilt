import asyncio
from typing import Dict
from datetime import datetime, timedelta
from app.models.request import LLMRequest
from app.models.response import LLMResponse, StreamingChunk, ToolCall
from app.core.exceptions import (
    RequestNotFoundException,
    RequestAlreadyHandledException,
    RequestTimeoutException
)


class StreamingBuffer:
    """Buffer for accumulating streaming response chunks"""
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.content_chunks: list[str] = []
        self.tool_calls: list[ToolCall] = []
        self.finish_reason: str = "stop"

    def add_chunk(self, content: str):
        """Add content chunk"""
        self.content_chunks.append(content)

    def add_tool_call(self, tool_call: ToolCall):
        """Add tool call"""
        self.tool_calls.append(tool_call)

    def set_finish_reason(self, reason: str):
        """Set finish reason"""
        self.finish_reason = reason

    def to_response(self) -> LLMResponse:
        """Convert buffer to complete response"""
        return LLMResponse(
            request_id=self.request_id,
            content="".join(self.content_chunks),
            tool_calls=self.tool_calls if self.tool_calls else None,
            finish_reason=self.finish_reason
        )


class RequestManager:
    """
    Manages LLM requests and responses using in-memory storage.

    Key responsibilities:
    - Store pending requests
    - Create asyncio.Future for each request to block HTTP response
    - Wait for human response via Future
    - Handle timeouts and cancellations
    """

    def __init__(self):
        self.pending_requests: Dict[str, LLMRequest] = {}
        self.active_requests: Dict[str, LLMRequest] = {}
        self.response_futures: Dict[str, asyncio.Future] = {}
        self.streaming_buffers: Dict[str, StreamingBuffer] = {}
        self.request_locks: Dict[str, asyncio.Lock] = {}

    async def create_request(self, request: LLMRequest) -> asyncio.Future:
        """
        Create a new request and return a Future that will be resolved
        when the human responds.
        """
        request_id = request.request_id

        # Store request
        self.pending_requests[request_id] = request
        self.active_requests[request_id] = request

        # Create Future for this request
        future = asyncio.get_event_loop().create_future()
        self.response_futures[request_id] = future

        # Create lock for this request
        self.request_locks[request_id] = asyncio.Lock()

        return future

    async def wait_for_response(self, request_id: str, timeout: int = 300) -> LLMResponse:
        """
        Wait for human response. Blocks until response is submitted or timeout.
        Raises RequestTimeoutException if timeout occurs.
        """
        if request_id not in self.response_futures:
            raise RequestNotFoundException(request_id)

        future = self.response_futures[request_id]

        try:
            # Wait for future to be resolved (with timeout)
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            # Cleanup on timeout
            await self.cancel_request(request_id, "timeout")
            raise RequestTimeoutException(request_id)

    async def submit_response(self, request_id: str, response: LLMResponse):
        """
        Submit a human response for a request.
        Resolves the Future, unblocking the waiting HTTP request.
        """
        async with self.request_locks.get(request_id, asyncio.Lock()):
            if request_id not in self.active_requests:
                raise RequestAlreadyHandledException(request_id)

            if request_id not in self.response_futures:
                raise RequestNotFoundException(request_id)

            future = self.response_futures[request_id]

            if future.done():
                raise RequestAlreadyHandledException(request_id)

            # Resolve the future with the response
            future.set_result(response)

            # Move from pending to completed (cleanup)
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]

            # Keep in active_requests briefly for status checks, then cleanup
            # (In a production system, might want to move to completed_requests)

    async def start_streaming(self, request_id: str):
        """Initialize streaming buffer for a request"""
        if request_id not in self.active_requests:
            raise RequestNotFoundException(request_id)

        self.streaming_buffers[request_id] = StreamingBuffer(request_id)

    async def add_chunk(self, request_id: str, content: str):
        """Add streaming chunk to buffer"""
        if request_id not in self.streaming_buffers:
            # Auto-initialize if not started
            await self.start_streaming(request_id)

        self.streaming_buffers[request_id].add_chunk(content)

    async def add_tool_call(self, request_id: str, tool_call: ToolCall):
        """Add tool call to streaming buffer"""
        if request_id not in self.streaming_buffers:
            await self.start_streaming(request_id)

        self.streaming_buffers[request_id].add_tool_call(tool_call)

    async def finish_streaming(self, request_id: str, finish_reason: str = "stop") -> LLMResponse:
        """
        Finish streaming and submit the complete response.
        Returns the complete response.
        """
        if request_id not in self.streaming_buffers:
            raise RequestNotFoundException(request_id)

        buffer = self.streaming_buffers[request_id]
        buffer.set_finish_reason(finish_reason)

        response = buffer.to_response()

        # Submit the complete response
        await self.submit_response(request_id, response)

        # Cleanup streaming buffer
        del self.streaming_buffers[request_id]

        return response

    async def cancel_request(self, request_id: str, reason: str = "cancelled"):
        """
        Cancel a request due to timeout or rejection.
        """
        # Remove from pending
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]

        # Remove from active
        if request_id in self.active_requests:
            del self.active_requests[request_id]

        # Cancel future if exists and not done
        if request_id in self.response_futures:
            future = self.response_futures[request_id]
            if not future.done():
                future.cancel()
            del self.response_futures[request_id]

        # Cleanup streaming buffer
        if request_id in self.streaming_buffers:
            del self.streaming_buffers[request_id]

        # Cleanup lock
        if request_id in self.request_locks:
            del self.request_locks[request_id]

    def get_request(self, request_id: str) -> LLMRequest | None:
        """Get a request by ID"""
        return self.active_requests.get(request_id)

    def get_pending_requests(self) -> list[LLMRequest]:
        """Get all pending requests"""
        return list(self.pending_requests.values())

    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            "pending_requests": len(self.pending_requests),
            "active_requests": len(self.active_requests),
            "streaming_requests": len(self.streaming_buffers)
        }


# Global singleton instance
request_manager = RequestManager()
