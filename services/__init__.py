# -*- coding: utf-8 -*-
"""
Services Layer
=============

Business logic services for Gemini TTS functionality.
"""

# Service imports with error handling
try:
    from .audio_generator import AudioGenerator
    from .cache_manager import CacheManager
    from .config_service import ConfigurationService
    from .content_analyzer import ContentAnalyzer
    from .text_processor import TextProcessor
    from .async_operations import AsyncTTSOperations
except ImportError as e:
    print(f"Services import error: {e}")
    AudioGenerator = None
    CacheManager = None
    ConfigurationService = None
    ContentAnalyzer = None
    TextProcessor = None
    AsyncTTSOperations = None

# Export list
__all__ = [
    "AudioGenerator",
    "CacheManager", 
    "ConfigurationService",
    "ContentAnalyzer",
    "TextProcessor",
    "AsyncTTSOperations"
]

def check_services() -> dict:
    """Check service availability"""
    return {
        "audio_generator": AudioGenerator is not None,
        "cache_manager": CacheManager is not None,
        "config_service": ConfigurationService is not None,
        "content_analyzer": ContentAnalyzer is not None,
        "text_processor": TextProcessor is not None,
        "async_operations": AsyncTTSOperations is not None
    }