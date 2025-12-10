"""Custom exceptions for Magick Mind SDK."""


class MagickMindError(Exception):
    """Base exception for all Magick Mind SDK errors."""
    
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(MagickMindError):
    """Raised when authentication fails."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""
    pass


class APIError(MagickMindError):
    """Raised when an API request fails."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int | None = None,
        response_data: dict | None = None
    ):
        super().__init__(message, status_code)
        self.response_data = response_data


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass


class ValidationError(MagickMindError):
    """Raised when request validation fails."""
    pass
