# -*- coding: utf-8 -*-
"""
Configuration Service
====================

Business logic for configuration validation, API testing, and model management.
"""

from typing import Dict, Any, List, Optional

from ..core.models import TTSConfig, ValidationResult, APITestResult, ModelInfo
from ..core.constants import ModelConstants, VoiceConstants, APIConstants
from ..core.exceptions import *
from ..core.logging_config import TTSLogger

class ConfigurationService:
    """Service for configuration management and validation"""
    
    def __init__(self, container, logger: Optional[TTSLogger] = None):
        self.container = container
        self.logger = logger or TTSLogger("config_service")

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration as a dictionary for the UI."""
        return self.container.get_config().to_dict()

    def save_config(self, config_dict: Dict[str, Any]) -> bool:
        """
        Save the configuration from a UI dictionary, returns success status.
        """
        try:
            config_obj = TTSConfig.from_dict(config_dict)
            self.container.update_config(config_obj)
            self.logger.info("Configuration saved successfully via service.")
            return True
        except Exception as e:
            self.logger.error("Failed to save configuration from dictionary", exception=e)
            return False

    def validate_config(self, config: TTSConfig) -> ValidationResult:
        """Validate complete configuration"""
        result = ValidationResult.success_result()
        
        # API key validation
        if not config.api_key.strip():
            result.add_field_error("api_key", "API key required")
        elif len(config.api_key) < APIConstants.MIN_API_KEY_LENGTH:
            result.add_field_error("api_key", "API key too short")
        
        # Model validation
        models = ModelConstants.get_model_definitions()
        if config.model not in models:
            result.add_field_error("model", f"Invalid model: {config.model}")
        else:
            model_info = models[config.model]
            if "thinking_budget_range" in model_info:
                min_budget, max_budget = model_info["thinking_budget_range"]
                if not (min_budget <= config.thinking_budget <= max_budget):
                    result.add_field_error("thinking_budget", 
                        f"Budget must be {min_budget}-{max_budget}")
        
        # Voice validation
        if config.voice not in VoiceConstants.get_all_voices():
            result.add_field_error("voice", f"Invalid voice: {config.voice}")
        
        # Parameter validation
        if not (0.0 <= config.temperature <= 2.0):
            result.add_field_error("temperature", "Temperature must be 0.0-2.0")
        
        if not (1 <= config.cache_days <= 365):
            result.add_field_error("cache_days", "Cache days must be 1-365")
        
        return result
    
    def test_api_key(self, config: TTSConfig) -> APITestResult:
        """Test API key by making test request"""
        validation = self.validate_config(config)
        if not validation.success:
            return APITestResult.error_result("Configuration invalid")
        
        try:
            audio_generator = self.container.get_audio_generator()
            if not audio_generator:
                return APITestResult.error_result("Audio generator unavailable")
            
            # Temporarily update config for test
            original_config = audio_generator.config
            audio_generator.config = config
            
            try:
                result = audio_generator.test_api_connection()
                
                if result.success:
                    data = result.data
                    return APITestResult.success_result({
                        "response_time": data.get("response_time", 0),
                        "audio_size": data.get("audio_size", 0),
                        "model_used": data.get("model"),
                        "voice_used": data.get("voice")
                    })
                else:
                    return APITestResult.error_result(result.error, result.error_code)
                    
            finally:
                audio_generator.config = original_config
                
        except Exception as e:
            error_msg = getattr(e, 'user_message', str(e))
            error_code = getattr(e, 'error_code', None)
            return APITestResult.error_result(error_msg, error_code)
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get detailed model information"""
        models = ModelConstants.get_model_definitions()
        if model_id not in models:
            return None
        
        data = models[model_id]
        return ModelInfo(
            model_id=data["model_id"],
            display_name=data["display_name"],
            description=data["description"],
            mode=data["mode"],
            thinking_budget_range=data.get("thinking_budget_range")
        )
    
    def get_all_models(self) -> List[ModelInfo]:
        """Get all available models"""
        models = []
        for model_id in ModelConstants.get_model_definitions():
            info = self.get_model_info(model_id)
            if info:
                models.append(info)
        return models
    
    def get_voice_categories(self) -> Dict[str, List[str]]:
        """Get voices organized by category"""
        return VoiceConstants.get_voice_categories()
    
    def get_recommended_settings(self, content_type: str = "general") -> Dict[str, Any]:
        """Get recommended settings for content type"""
        
        recommendations = {
            "general": {
                "model": "flash_unified",
                "voice": "Zephyr",
                "temperature": 0.0,
                "thinking_budget": 0,
                "preprocessing_style": "natural"
            },
            "technical": {
                "model": "pro_unified", 
                "voice": "Algieba",
                "temperature": 0.1,
                "thinking_budget": 1024,
                "preprocessing_style": "technical"
            },
            "instructions": {
                "model": "flash_unified",
                "voice": "Puck",
                "temperature": 0.0,
                "thinking_budget": 512,
                "preprocessing_style": "professional"
            }
        }
        
        return recommendations.get(content_type, recommendations["general"])
    
    def optimize_config_for_content(self, config: TTSConfig, content_analysis) -> TTSConfig:
        """Optimize configuration based on content analysis"""
        optimized = TTSConfig.from_dict(config.to_dict())
        
        # Adjust thinking budget based on complexity
        if hasattr(content_analysis, 'suggested_thinking_budget'):
            optimized.thinking_budget = content_analysis.suggested_thinking_budget
        
        # Adjust processing mode
        if hasattr(content_analysis, 'recommended_mode'):
            optimized.processing_mode = content_analysis.recommended_mode.value
        
        # Content-specific voice selection
        if hasattr(content_analysis, 'content_type'):
            if content_analysis.content_type == "technical":
                optimized.voice = "Algieba" if optimized.voice == "Zephyr" else optimized.voice
            elif content_analysis.content_type == "instructions":
                optimized.voice = "Puck" if optimized.voice == "Zephyr" else optimized.voice
        
        return optimized
    
    def export_config(self, config: TTSConfig) -> str:
        """Export configuration as JSON string"""
        import json
        return json.dumps(config.to_dict(), indent=2)
    
    def import_config(self, config_json: str) -> TTSConfig:
        """Import configuration from JSON string"""
        import json
        try:
            data = json.loads(config_json)
            return TTSConfig.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValidationException(f"Invalid JSON: {e}")
        except Exception as e:
            raise ConfigurationException(f"Import failed: {e}")
    
    def reset_to_defaults(self) -> TTSConfig:
        """Create default configuration"""
        return TTSConfig()
    
    def migrate_legacy_config(self, legacy_data: Dict[str, Any]) -> TTSConfig:
        """Migrate from legacy configuration format"""
        # Handle old field names
        migration_map = {
            "gemini_api_key": "api_key",
            "selected_model": "model",
            "selected_voice": "voice",
            "temp": "temperature",
            "thinking_tokens": "thinking_budget"
        }
        
        migrated_data = {}
        for old_key, new_key in migration_map.items():
            if old_key in legacy_data:
                migrated_data[new_key] = legacy_data[old_key]
        
        # Add remaining fields as-is
        for key, value in legacy_data.items():
            if key not in migration_map and key in TTSConfig.__dataclass_fields__:
                migrated_data[key] = value
        
        return TTSConfig.from_dict(migrated_data)
    
    def get_config_summary(self, config: TTSConfig) -> Dict[str, str]:
        """Get human-readable configuration summary"""
        model_info = self.get_model_info(config.model)
        model_name = model_info.display_name if model_info else config.model
        
        return {
            "Model": model_name,
            "Voice": config.voice,
            "Mode": config.processing_mode.title(),
            "Temperature": f"{config.temperature:.1f}",
            "Cache": f"{config.cache_days} days" if config.enable_cache else "Disabled",
            "Thinking Budget": str(config.thinking_budget) if config.thinking_budget > 0 else "None"
        }