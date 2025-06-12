# -*- coding: utf-8 -*-
"""
Gemini TTS Core Module
======================

Refactored core functionality with type-safe models, dependency injection,
structured logging, and proper error handling.
"""

# Version information
__version__ = "2.0.0"
__author__ = "Jesus Heredia Ramirez"

# Core imports with graceful error handling
try:
    # Data models - primary interface
    from .models import (
        TTSConfig,
        ModelInfo,
        ContentAnalysis,
        AudioGenerationRequest,
        AudioGenerationResult,
        Result,
        ValidationResult,
        APITestResult,
        ProcessingMode,
        ContentType,
        ComplexityLevel
    )
    
    # Constants - configuration values
    from .constants import (
        APIConstants,
        ModelConstants,
        VoiceConstants,
        AudioConstants,
        CacheConstants,
        ProcessingConstants,
        UIConstants,
        ErrorConstants
    )
    
    # Dependency injection
    from .container import (
        TTSContainer,
        get_global_container,
        set_global_container,
        cleanup_global_container
    )
    
    # Exception hierarchy
    from .exceptions import (
        TTSException,
        APIException,
        InvalidAPIKeyException,
        RateLimitedException,
        NetworkException,
        ConfigurationException,
        ValidationException,
        TextValidationException,
        CacheException,
        AudioException,
        create_api_exception,
        handle_http_error,
        handle_network_error
    )
    
    # Logging system
    from .logging_config import (
        TTSLogger,
        get_logger,
        setup_logging,
        LoggedOperation,
        log_operation
    )
    
    # Legacy content analyzer (until moved to services)
    try:
        from .content_analyzer import ContentAnalyzer
        _content_analyzer_available = True
    except ImportError:
        ContentAnalyzer = None
        _content_analyzer_available = False
    
except ImportError as e:
    # Fallback imports for backward compatibility
    print(f"Core module import warning: {e}")
    
    # Minimal fallbacks
    TTSConfig = None
    TTSContainer = None
    TTSLogger = None
    ContentAnalyzer = None
    _content_analyzer_available = False

# Export list for controlled imports
__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Core models
    "TTSConfig",
    "ModelInfo", 
    "ContentAnalysis",
    "AudioGenerationRequest",
    "AudioGenerationResult",
    "Result",
    "ValidationResult",
    "APITestResult",
    
    # Enums
    "ProcessingMode",
    "ContentType", 
    "ComplexityLevel",
    
    # Constants
    "APIConstants",
    "ModelConstants",
    "VoiceConstants",
    "AudioConstants",
    "CacheConstants",
    "ProcessingConstants",
    "UIConstants",
    "ErrorConstants",
    
    # Container
    "TTSContainer",
    "get_global_container",
    "set_global_container", 
    "cleanup_global_container",
    
    # Exceptions
    "TTSException",
    "APIException",
    "InvalidAPIKeyException",
    "RateLimitedException", 
    "NetworkException",
    "ConfigurationException",
    "ValidationException",
    "TextValidationException",
    "CacheException",
    "AudioException",
    "create_api_exception",
    "handle_http_error",
    "handle_network_error",
    
    # Logging
    "TTSLogger",
    "get_logger",
    "setup_logging",
    "LoggedOperation",
    "log_operation",
    
    # Legacy components
    "ContentAnalyzer"
]

def get_version() -> str:
    """Get core module version"""
    return __version__

def check_dependencies() -> dict:
    """Check availability of core dependencies"""
    return {
        "models": TTSConfig is not None,
        "container": TTSContainer is not None,
        "logging": TTSLogger is not None,
        "content_analyzer": _content_analyzer_available,
        "exceptions": TTSException is not None
    }

def create_default_config() -> 'TTSConfig':
    """Create default configuration instance"""
    if TTSConfig is None:
        raise ImportError("TTSConfig not available")
    return TTSConfig()

def create_container(anki_main_window=None) -> 'TTSContainer':
    """Create dependency injection container"""
    if TTSContainer is None:
        raise ImportError("TTSContainer not available") 
    return TTSContainer(anki_main_window)

def setup_core_logging(level: str = "INFO") -> 'TTSLogger':
    """Initialize core logging system"""
    if setup_logging is None:
        raise ImportError("Logging system not available")
    return setup_logging(level)

# Module initialization
def _initialize_core():
    """Initialize core module components"""
    try:
        # Set up basic logging
        logger = get_logger("gemini_tts.core")
        logger.info("Core module initialized", version=__version__)
        
        # Log dependency status
        deps = check_dependencies()
        logger.debug("Core dependencies", **deps)
        
    except Exception as e:
        print(f"Core initialization warning: {e}")

# Initialize on import
_initialize_core()