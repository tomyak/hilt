from fastapi import HTTPException, status


class RequestTimeoutException(HTTPException):
    """Raised when a request times out waiting for human response"""
    def __init__(self, request_id: str):
        super().__init__(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Request {request_id} timed out - no human response received"
        )


class RequestNotFoundException(HTTPException):
    """Raised when a request ID is not found"""
    def __init__(self, request_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request {request_id} not found"
        )


class RequestAlreadyHandledException(HTTPException):
    """Raised when trying to respond to an already handled request"""
    def __init__(self, request_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Request {request_id} has already been handled"
        )


class InvalidCredentialsException(HTTPException):
    """Raised when login credentials are invalid"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
