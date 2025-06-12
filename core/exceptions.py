# -*- coding: utf-8 -*-
"""
Custom Exception Hierarchy
==========================

Structured exception handling for Gemini TTS operations.
Provides specific error types for different failure modes.
"""

from typing import Optional, Dict, Any

class TTSException(Exception):
    """Base exception for all TTS operations"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.user_message = message  # Default user-friendly message
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.args[0]}"
        return self.args[0]

class APIException(TTSException):
    """API-related errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)
        self.status_code = status_code
        
        # Set user-friendly messages based on status code
        if status_code == 403:
            self.user_message = "Invalid API key. Check your configuration."
        elif status_code == 429:
            self.user_message = "Rate limited. Wait a moment and try again."
        elif status_code == 400:
            self.user_message = "Invalid request. Check your text and settings."
        else:
            self.user_message = message

class InvalidAPIKeyException(APIException):
    """Invalid or missing API key"""
    
    def __init__(self, message: str = "Invalid API key or access denied"):
        super().__init__(message, status_code=403, error_code="INVALID_API_KEY")

class RateLimitedException(APIException):
    """API rate limit exceeded"""
    
    def __init__(self, message: str = "Rate limited - please wait and try again", retry_after: Optional[int] = None):
        super().__init__(message, status_code=429, error_code="RATE_LIMITED")
        self.retry_after = retry_after
        if retry_after:
            self.user_message = f"Rate limited. Try again in {retry_after} seconds."

class BadRequestException(APIException):
    """Invalid API request"""
    
    def __init__(self, message: str = "Invalid request - check API key and text"):
        super().__init__(message, status_code=400, error_code="BAD_REQUEST")

class NetworkException(TTSException):
    """Network connectivity errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, timeout: bool = False):
        super().__init__(message, error_code)
        self.timeout = timeout
        
        if timeout:
            self.user_message = "Network timeout. Check your connection."
        elif "connection" in message.lower():
            self.user_message = "Connection failed. Check your internet."
        else:
            self.user_message = "Network error. Check your connection."

class TimeoutException(NetworkException):
    """Network timeout errors"""
    
    def __init__(self, message: str = "Network timeout", timeout_seconds: Optional[float] = None):
        super().__init__(message, error_code="TIMEOUT", timeout=True)
        self.timeout_seconds = timeout_seconds

class ConnectionException(NetworkException):
    """Network connection errors"""
    
    def __init__(self, message: str = "Connection failed"):
        super().__init__(message, error_code="CONNECTION_ERROR")

class ConfigurationException(TTSException):
    """Configuration-related errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code)
        self.field = field
        self.user_message = "Configuration error. Check your settings."

class InvalidConfigException(ConfigurationException):
    """Invalid configuration values"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field, error_code="INVALID_CONFIG")

class MissingConfigException(ConfigurationException):
    """Missing required configuration"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field, error_code="MISSING_CONFIG")
        if field == "api_key":
            self.user_message = "Please configure API key first"

class ValidationException(TTSException):
    """Data validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, error_code: Optional[str] = None):
        super().__init__(message, error_code)
        self.field = field
        self.value = value
        self.user_message = message

class TextValidationException(ValidationException):
    """Text input validation errors"""
    
    def __init__(self, message: str, text_length: Optional[int] = None):
        super().__init__(message, error_code="INVALID_TEXT")
        self.text_length = text_length
        
        if text_length and text_length > 5000:
            self.user_message = "Text too long - select shorter text"
        elif text_length == 0:
            self.user_message = "Please select some text first"

class EmptyTextException(TextValidationException):
    """Empty text provided"""
    
    def __init__(self, message: str = "No text provided"):
        super().__init__(message, text_length=0)

class TextTooLongException(TextValidationException):
    """Text exceeds maximum length"""
    
    def __init__(self, message: str = "Text too long", text_length: int = 0, max_length: int = 5000):
        super().__init__(message, text_length=text_length)
        self.max_length = max_length
        self.user_message = f"Text too long ({text_length} chars). Maximum: {max_length}"

class CacheException(TTSException):
    """Cache operation errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, critical: bool = False):
        super().__init__(message, error_code)
        self.critical = critical
        
        # Cache errors are usually not critical for user experience
        if not critical:
            self.user_message = "Cache error. Audio may not be saved for reuse."
        else:
            self.user_message = message

class CacheWriteException(CacheException):
    """Cache write operation failed"""
    
    def __init__(self, message: str = "Failed to write cache file", file_path: Optional[str] = None):
        super().__init__(message, error_code="CACHE_WRITE_ERROR")
        self.file_path = file_path

class CacheReadException(CacheException):
    """Cache read operation failed"""
    
    def __init__(self, message: str = "Failed to read cache file", file_path: Optional[str] = None):
        super().__init__(message, error_code="CACHE_READ_ERROR")
        self.file_path = file_path

class CacheCorruptedException(CacheException):
    """Cache file is corrupted"""
    
    def __init__(self, message: str = "Cache file corrupted", file_path: Optional[str] = None):
        super().__init__(message, error_code="CACHE_CORRUPTED", critical=True)
        self.file_path = file_path

class UIException(TTSException):
    """User interface errors"""
    
    def __init__(self, message: str, component: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code)
        self.component = component
        self.user_message = "UI error. Some features may not work."

class EditorException(UIException):
    """Anki editor integration errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message, component="editor", error_code=error_code)
        self.user_message = "Editor error. Try refreshing the editor."

class ButtonException(UIException):
    """UI button creation/handling errors"""
    
    def __init__(self, message: str, button_name: Optional[str] = None):
        super().__init__(message, component="button", error_code="BUTTON_ERROR")
        self.button_name = button_name
        self.user_message = "Button error. Some buttons may not work."

class AudioException(TTSException):
    """Audio processing errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, audio_data_size: Optional[int] = None):
        super().__init__(message, error_code)
        self.audio_data_size = audio_data_size
        self.user_message = "Audio processing error."

class AudioConversionException(AudioException):
    """Audio format conversion errors"""
    
    def __init__(self, message: str = "Failed to convert audio format", source_format: Optional[str] = None, target_format: Optional[str] = None):
        super().__init__(message, error_code="AUDIO_CONVERSION_ERROR")
        self.source_format = source_format
        self.target_format = target_format

class AudioSizeException(AudioException):
    """Audio data size validation errors"""
    
    def __init__(self, message: str = "Invalid audio data size", actual_size: int = 0, expected_min: int = 1000):
        super().__init__(message, error_code="AUDIO_SIZE_ERROR", audio_data_size=actual_size)
        self.expected_min = expected_min
        self.user_message = "Audio generation failed - invalid audio data received"

class SecurityException(TTSException):
    """Security-related errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, file_path: Optional[str] = None):
        super().__init__(message, error_code)
        self.file_path = file_path
        self.user_message = "Security error. Operation blocked."

class PathSecurityException(SecurityException):
    """File path security violations"""
    
    def __init__(self, message: str = "Invalid file path", attempted_path: Optional[str] = None, allowed_base: Optional[str] = None):
        super().__init__(message, error_code="PATH_SECURITY_ERROR", file_path=attempted_path)
        self.attempted_path = attempted_path
        self.allowed_base = allowed_base

# Exception mapping for HTTP status codes
HTTP_STATUS_EXCEPTIONS = {
    400: BadRequestException,
    401: InvalidAPIKeyException,
    403: InvalidAPIKeyException,
    429: RateLimitedException,
}

def create_api_exception(status_code: int, message: str, details: Optional[Dict[str, Any]] = None) -> APIException:
    """
    Create appropriate API exception based on HTTP status code.
    
    Args:
        status_code: HTTP status code
        message: Error message
        details: Additional error details
    
    Returns:
        Specific API exception instance
    """
    exception_class = HTTP_STATUS_EXCEPTIONS.get(status_code, APIException)
    
    if exception_class == APIException:
        return APIException(message, status_code=status_code, details=details)
    else:
        return exception_class(message)

def handle_http_error(error) -> APIException:
    """
    Convert HTTP error to appropriate TTS exception.
    
    Args:
        error: HTTP error object (urllib.error.HTTPError)
    
    Returns:
        Appropriate API exception
    """
    try:
        status_code = error.code
        reason = getattr(error, 'reason', 'Unknown error')
        message = f"HTTP {status_code}: {reason}"
        
        return create_api_exception(status_code, message)
        
    except AttributeError:
        return APIException(str(error))

def handle_network_error(error) -> NetworkException:
    """
    Convert network error to appropriate TTS exception.
    
    Args:
        error: Network error object
    
    Returns:
        Appropriate network exception
    """
    error_str = str(error).lower()
    
    if "timeout" in error_str:
        return TimeoutException(str(error))
    elif "connection" in error_str:
        return ConnectionException(str(error))
    else:
        return NetworkException(str(error))