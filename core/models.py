# -*- coding: utf-8 -*-
"""
Data Models for Gemini TTS
==========================

Type-safe data structures replacing dictionary usage throughout the system.
Provides IDE support, validation, and clearer interfaces.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple, Union
from enum import Enum

class ProcessingMode(Enum):
    """Available text processing modes"""
    UNIFIED = "unified"
    TRADITIONAL = "traditional"
    HYBRID = "hybrid"
    AUTO = "auto"

class ContentType(Enum):
    """Content classification types"""
    INSTRUCTIONS = "instructions"
    FEATURES = "features"
    OPTIONS = "options"
    TECHNICAL = "technical"
    QA = "qa"
    GENERAL = "general"

class ComplexityLevel(Enum):
    """Content complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class PreprocessingStrategy(Enum):
    """Text preprocessing strategies"""
    MINIMAL = "minimal"
    STRUCTURAL = "structural"
    ENHANCED = "enhanced"
    COMPREHENSIVE = "comprehensive"

@dataclass
class TTSConfig:
    """Complete TTS configuration with validation and defaults"""
    
    # Basic settings
    api_key: str = ""
    model: str = "flash_unified"
    processing_mode: str = "unified"
    voice: str = "Zephyr"
    temperature: float = 0.0
    
    # Advanced settings
    thinking_budget: int = 0
    enable_cache: bool = True
    cache_days: int = 30
    enable_fallback: bool = True
    cache_preprocessing: bool = True
    
    # Processing settings
    preprocessing_style: str = "natural"
    enable_style_control: bool = True
    auto_detect_content: bool = True
    prefer_instructions: bool = True
    
    def validate(self) -> bool:
        """Validate configuration values"""
        if not self.api_key.strip():
            return False
        if self.temperature < 0.0 or self.temperature > 2.0:
            return False
        if self.thinking_budget < 0 or self.thinking_budget > 32768:
            return False
        if self.cache_days < 1 or self.cache_days > 365:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for legacy compatibility"""
        return {
            "api_key": self.api_key,
            "model": self.model,
            "processing_mode": self.processing_mode,
            "voice": self.voice,
            "temperature": self.temperature,
            "thinking_budget": self.thinking_budget,
            "enable_cache": self.enable_cache,
            "cache_days": self.cache_days,
            "enable_fallback": self.enable_fallback,
            "cache_preprocessing": self.cache_preprocessing,
            "preprocessing_style": self.preprocessing_style,
            "enable_style_control": self.enable_style_control,
            "auto_detect_content": self.auto_detect_content,
            "prefer_instructions": self.prefer_instructions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TTSConfig':
        """Create from dictionary with fallback to defaults"""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config

@dataclass
class ModelInfo:
    """Information about available TTS models"""
    model_id: str
    display_name: str
    description: str
    mode: str
    thinking_budget_range: Optional[Tuple[int, int]] = None
    
    @property
    def supports_unified(self) -> bool:
        """Check if model supports unified processing"""
        return self.mode == "unified"
    
    @property
    def supports_thinking(self) -> bool:
        """Check if model supports thinking budget"""
        return self.thinking_budget_range is not None

@dataclass
class ContentAnalysis:
    """Results of content structure analysis"""
    content_type: str
    complexity: str
    has_bullets: bool
    has_numbers: bool
    line_count: int
    avg_line_length: float
    suggested_thinking_budget: int
    preprocessing_strategy: str
    estimated_speech_time: float
    
    # Additional metadata
    has_nested_structure: bool = False
    has_special_chars: bool = False
    has_technical_terms: bool = False
    
    @property
    def needs_preprocessing(self) -> bool:
        """Determine if content needs advanced preprocessing"""
        return (self.has_bullets or self.has_numbers or 
                self.complexity != "low" or
                self.content_type in ["instructions", "technical"])
    
    @property
    def recommended_mode(self) -> ProcessingMode:
        """Get recommended processing mode"""
        if not self.needs_preprocessing:
            return ProcessingMode.TRADITIONAL
        elif self.complexity == "high" or self.content_type == "technical":
            return ProcessingMode.UNIFIED
        else:
            return ProcessingMode.HYBRID

@dataclass
class CacheFileInfo:
    """Metadata for cached audio files"""
    created: float
    accessed: float
    version: str
    cache_key: str
    file_size: int = 0
    
    @property
    def age_days(self) -> float:
        """Age of cache file in days"""
        import time
        return (time.time() - self.created) / (24 * 3600)

@dataclass
class CacheMetadata:
    """Complete cache metadata structure"""
    version: str = "2.0"
    files: Dict[str, CacheFileInfo] = field(default_factory=dict)
    
    def add_file(self, filename: str, cache_key: str, file_size: int = 0):
        """Add file to cache metadata"""
        import time
        current_time = time.time()
        self.files[filename] = CacheFileInfo(
            created=current_time,
            accessed=current_time,
            version=self.version,
            cache_key=cache_key,
            file_size=file_size
        )
    
    def update_access(self, filename: str):
        """Update file access time"""
        import time
        if filename in self.files:
            self.files[filename].accessed = time.time()
    
    def get_expired_files(self, max_age_days: int) -> list[str]:
        """Get list of expired cache files"""
        expired = []
        for filename, info in self.files.items():
            if info.age_days > max_age_days:
                expired.append(filename)
        return expired

@dataclass
class AudioGenerationRequest:
    """Request parameters for audio generation"""
    text: str
    config: TTSConfig
    processing_mode: Optional[str] = None
    use_cache: bool = True
    
    def __post_init__(self):
        """Validate request after initialization"""
        if not self.text.strip():
            raise ValueError("Text cannot be empty")
        if len(self.text) > 5000:
            raise ValueError("Text too long (max 5000 characters)")
        if self.processing_mode is None:
            self.processing_mode = self.config.processing_mode

@dataclass
class AudioGenerationResult:
    """Result of audio generation operation"""
    success: bool
    filename: Optional[str] = None
    error_message: Optional[str] = None
    used_cache: bool = False
    processing_mode: Optional[str] = None
    generation_time: float = 0.0
    
    @property
    def failed(self) -> bool:
        """Check if generation failed"""
        return not self.success

# Generic result type for operations
@dataclass
class Result:
    """Generic result wrapper for operations"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    @classmethod
    def success_result(cls, data: Any = None) -> 'Result':
        """Create successful result"""
        return cls(success=True, data=data)
    
    @classmethod
    def error_result(cls, error: str, error_code: Optional[str] = None) -> 'Result':
        """Create error result"""
        return cls(success=False, error=error, error_code=error_code)
    
    @property
    def failed(self) -> bool:
        """Check if operation failed"""
        return not self.success

# Validation result specifically for configuration
@dataclass
class ValidationResult(Result):
    """Result of configuration validation"""
    field_errors: Dict[str, str] = field(default_factory=dict)
    
    def add_field_error(self, field: str, error: str):
        """Add field-specific validation error"""
        self.field_errors[field] = error
        self.success = False
        if self.error:
            self.error += f"; {field}: {error}"
        else:
            self.error = f"{field}: {error}"

@dataclass 
class APITestResult(Result):
    """Result of API key testing"""
    response_time: float = 0.0
    audio_size: int = 0
    model_used: Optional[str] = None
    voice_used: Optional[str] = None