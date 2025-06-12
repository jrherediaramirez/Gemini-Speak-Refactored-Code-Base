# -*- coding: utf-8 -*-
"""
Constants for Gemini TTS
========================

Centralized configuration constants to eliminate magic numbers
and hardcoded values throughout the codebase.
"""

from typing import Dict, Any, List

class APIConstants:
    """Gemini API configuration constants"""
    
    # Base URLs
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    GENERATE_CONTENT_ENDPOINT = "generateContent"
    
    # Timeouts (seconds)
    UNIFIED_TIMEOUT = 45  # Longer for AI preprocessing
    TRADITIONAL_TIMEOUT = 30  # Standard TTS timeout
    CONNECTION_TIMEOUT = 10  # Connection establishment
    
    # Request limits
    MAX_TEXT_LENGTH = 5000  # Characters
    MIN_API_KEY_LENGTH = 20  # Basic validation
    MAX_RETRIES = 3  # For rate limiting
    RETRY_DELAY = 1.0  # Initial retry delay (seconds)
    
    # Rate limiting
    REQUESTS_PER_MINUTE = 60  # Flash model limit
    TOKENS_PER_MINUTE = 80000  # Token limit

class ModelConstants:
    """Available Gemini models and their configurations"""
    
    # Model IDs
    FLASH_UNIFIED = "gemini-2.5-flash-preview-06-05"
    PRO_UNIFIED = "gemini-2.5-pro-preview-06-05"
    FLASH_TTS = "gemini-2.5-flash-preview-tts"
    PRO_TTS = "gemini-2.5-pro-preview-tts"
    
    # Thinking budget ranges (tokens)
    FLASH_THINKING_RANGE = (0, 24576)
    PRO_THINKING_RANGE = (128, 32768)
    
    # Default selections
    DEFAULT_MODEL = "flash_unified"
    DEFAULT_FALLBACK_MODEL = "flash_tts"
    
    @classmethod
    def get_model_definitions(cls) -> Dict[str, Dict[str, Any]]:
        """Get complete model definitions"""
        return {
            "flash_unified": {
                "model_id": cls.FLASH_UNIFIED,
                "display_name": "Gemini 2.5 Flash (Unified)",
                "description": "AI preprocessing + TTS in one call",
                "mode": "unified",
                "thinking_budget_range": cls.FLASH_THINKING_RANGE
            },
            "pro_unified": {
                "model_id": cls.PRO_UNIFIED,
                "display_name": "Gemini 2.5 Pro (Unified)",
                "description": "Best quality with AI preprocessing",
                "mode": "unified",
                "thinking_budget_range": cls.PRO_THINKING_RANGE
            },
            "flash_tts": {
                "model_id": cls.FLASH_TTS,
                "display_name": "Gemini 2.5 Flash (TTS Only)",
                "description": "Traditional TTS without preprocessing",
                "mode": "traditional"
            },
            "pro_tts": {
                "model_id": cls.PRO_TTS,
                "display_name": "Gemini 2.5 Pro (TTS Only)",
                "description": "High quality traditional TTS",
                "mode": "traditional"
            }
        }

class VoiceConstants:
    """Available Gemini TTS voices"""
    
    # Voice categories for organization
    NATURAL_VOICES = [
        "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda"
    ]
    
    EXPRESSIVE_VOICES = [
        "Orus", "Aoede", "Callirhoe", "Autonoe", "Enceladus", "Iapetus"
    ]
    
    TECHNICAL_VOICES = [
        "Umbriel", "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi"
    ]
    
    DRAMATIC_VOICES = [
        "Laomedeia", "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima"
    ]
    
    SPECIALIZED_VOICES = [
        "Achird", "Zubenelgenubi", "Vindemiatrix", "Sadachbia", 
        "Sadaltager", "Sulafat"
    ]
    
    DEFAULT_VOICE = "Zephyr"
    
    @classmethod
    def get_all_voices(cls) -> List[str]:
        """Get complete list of available voices"""
        return (cls.NATURAL_VOICES + cls.EXPRESSIVE_VOICES + 
                cls.TECHNICAL_VOICES + cls.DRAMATIC_VOICES + 
                cls.SPECIALIZED_VOICES)
    
    @classmethod
    def get_voice_categories(cls) -> Dict[str, List[str]]:
        """Get voices organized by category"""
        return {
            "Natural": cls.NATURAL_VOICES,
            "Expressive": cls.EXPRESSIVE_VOICES,
            "Technical": cls.TECHNICAL_VOICES,
            "Dramatic": cls.DRAMATIC_VOICES,
            "Specialized": cls.SPECIALIZED_VOICES
        }

class AudioConstants:
    """Audio processing constants"""
    
    # Audio format settings
    DEFAULT_SAMPLE_RATE = 24000  # Hz
    DEFAULT_CHANNELS = 1  # Mono
    DEFAULT_BITS_PER_SAMPLE = 16
    DEFAULT_MIME_TYPE = "audio/L16;rate=24000"
    
    # WAV file structure
    WAV_HEADER_SIZE = 44  # Bytes
    BYTES_PER_SAMPLE = 2  # 16-bit audio
    
    # Audio validation
    MIN_AUDIO_SIZE = 1000  # Bytes (sanity check)
    MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB limit
    
    # Speech estimation
    AVERAGE_WORDS_PER_MINUTE = 150  # For time estimation
    AVERAGE_CHARS_PER_WORD = 5  # For rough calculation

class CacheConstants:
    """Caching system constants"""
    
    # Directory and file names
    CACHE_DIR_NAME = ".gemini_cache"
    METADATA_FILENAME = "cache_metadata.json"
    TEMP_FILE_PREFIX = ".cache_tmp_"
    TEMP_METADATA_PREFIX = ".metadata_tmp_"
    
    # Cache settings
    DEFAULT_CACHE_DAYS = 30
    MIN_CACHE_DAYS = 1
    MAX_CACHE_DAYS = 365
    TEMP_FILE_CLEANUP_HOURS = 1  # Clean up abandoned temp files
    
    # Cache file extensions
    CACHE_AUDIO_EXT = ".wav"
    CACHE_METADATA_EXT = ".json"
    
    # Versioning
    CACHE_VERSION = "2.0"
    LEGACY_VERSION = "1.0"

class ProcessingConstants:
    """Text processing constants"""
    
    # Content analysis thresholds
    MIN_BULLET_COUNT = 2  # Minimum bullets to detect list
    MIN_NUMBERED_COUNT = 2  # Minimum numbers to detect list
    COMPLEX_LINE_THRESHOLD = 100  # Characters per line for complexity
    LARGE_CONTENT_THRESHOLD = 1000  # Characters for large content
    MANY_LINES_THRESHOLD = 10  # Lines count for complexity
    
    # Technical content indicators
    TECHNICAL_KEYWORDS = [
        'api', 'http', 'url', 'json', 'xml', 'sql', 'css', 'html',
        'function', 'class', 'method', 'variable', 'parameter',
        'config', 'settings', 'database', 'server', 'client',
        'algorithm', 'code', 'syntax', 'compile', 'debug'
    ]
    
    # Step indicators for instruction detection
    STEP_KEYWORDS = [
        'first', 'second', 'third', 'next', 'then', 'finally',
        'step', 'stage', 'phase', 'install', 'configure', 'setup'
    ]
    
    # Feature indicators
    FEATURE_KEYWORDS = [
        'feature', 'benefit', 'advantage', 'capability', 'includes',
        'offers', 'provides', 'supports', 'enables'
    ]
    
    # Option indicators
    OPTION_KEYWORDS = [
        'option', 'choice', 'alternative', 'can', 'may', 'either',
        'plan', 'package', 'version', 'tier'
    ]
    
    # Processing styles
    PROCESSING_STYLES = [
        "natural", "professional", "conversational", "technical"
    ]
    
    DEFAULT_STYLE = "natural"

class UIConstants:
    """User interface constants"""
    
    # Window dimensions
    CONFIG_WINDOW_MIN_WIDTH = 600
    CONFIG_WINDOW_MIN_HEIGHT = 700
    
    # Button labels and shortcuts
    TTS_SHORTCUT = "Ctrl+G"
    TTS_BUTTON_TOOLTIP = "Generate Gemini TTS (Ctrl+G)"
    
    # Field detection priorities
    PREFERRED_FIELD_NAMES = ["Front", "Question", "Text", "Word"]
    DEFAULT_FIELD_NAME = "Front"
    
    # Tooltip durations (milliseconds)
    SHORT_TOOLTIP = 2000
    LONG_TOOLTIP = 4000
    ERROR_TOOLTIP = 5000
    
    # Progress indicators
    PROCESSING_MESSAGES = {
        "unified": "Generating TTS with AI preprocessing...",
        "traditional": "Generating TTS...",
        "testing": "Testing API connection...",
        "caching": "Saving to cache..."
    }

class ErrorConstants:
    """Error handling constants"""
    
    # HTTP status codes
    HTTP_BAD_REQUEST = 400
    HTTP_UNAUTHORIZED = 401
    HTTP_FORBIDDEN = 403
    HTTP_NOT_FOUND = 404
    HTTP_RATE_LIMITED = 429
    HTTP_INTERNAL_ERROR = 500
    
    # Error categories
    API_ERRORS = {
        HTTP_BAD_REQUEST: "Invalid request - check API key and text",
        HTTP_FORBIDDEN: "Invalid API key or access denied", 
        HTTP_RATE_LIMITED: "Rate limited - please wait and try again"
    }
    
    # User-friendly error messages
    NETWORK_ERROR = "Network error - check your connection"
    CONFIG_ERROR = "Configuration error - check your settings"
    CACHE_ERROR = "Cache error - audio may not be saved for reuse"
    TEXT_TOO_LONG = "Text too long - select shorter text"
    NO_TEXT_SELECTED = "Please select some text first"
    NO_API_KEY = "Please configure API key first"
    
    # Error codes for programmatic handling
    ERROR_CODES = {
        "INVALID_API_KEY": "invalid_api_key",
        "RATE_LIMITED": "rate_limited",
        "NETWORK_ERROR": "network_error",
        "TEXT_TOO_LONG": "text_too_long",
        "NO_TEXT": "no_text",
        "CONFIG_ERROR": "config_error",
        "CACHE_ERROR": "cache_error"
    }

class FileConstants:
    """File system constants"""
    
    # Security constraints
    MAX_FILENAME_LENGTH = 255
    FORBIDDEN_CHARS = r'<>:"/\|?*'
    
    # File naming patterns
    AUDIO_FILENAME_PATTERN = "gemini_tts_{cache_key}_{timestamp}.wav"
    TEMP_FILENAME_PATTERN = ".cache_tmp_{cache_key}_{timestamp}.wav"
    
    # File size limits
    MAX_CACHE_SIZE_MB = 1000  # Total cache size limit
    MAX_SINGLE_FILE_MB = 50   # Single audio file limit
    
    # Cleanup patterns
    CLEANUP_EXTENSIONS = [".wav", ".json", ".tmp"]
    CLEANUP_PREFIXES = [".cache_tmp_", ".metadata_tmp_"]