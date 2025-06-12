# -*- coding: utf-8 -*-
"""
Dependency Injection Container
=============================

Manages service instantiation and dependencies for the Gemini TTS system.
Provides centralized dependency management and enables easier testing.
"""

from typing import Optional, Dict, Any
import os
from .models import TTSConfig
from .logging_config import TTSLogger

class TTSContainer:
    """
    Dependency injection container for TTS services.
    
    Manages the lifecycle and dependencies of all TTS components,
    enabling loose coupling and easier testing.
    """
    
    def __init__(self, anki_main_window=None):
        """
        Initialize container with Anki main window dependency.
        
        Args:
            anki_main_window: Anki's main window object (mw)
        """
        self._mw = anki_main_window
        self._logger = None
        self._config = None
        
        # Service instances (lazy loaded)
        self._config_service = None
        self._cache_manager = None
        self._content_analyzer = None
        self._text_processor = None
        self._audio_generator = None
        self._editor_integration = None
        
        # Initialize logger first
        self._setup_logging()
    
    def _setup_logging(self):
        """Initialize logging system"""
        try:
            from .logging_config import TTSLogger
            self._logger = TTSLogger()
            self._logger.info("TTS Container initialized")
        except ImportError:
            # Fallback if logging not available
            import logging
            self._logger = logging.getLogger("gemini_tts")
    
    @property
    def anki_main_window(self):
        """Get Anki main window reference"""
        if self._mw is None:
            try:
                from aqt import mw
                self._mw = mw
            except ImportError:
                raise RuntimeError("Anki main window not available")
        return self._mw
    
    @property
    def logger(self) -> TTSLogger:
        """Get logger instance"""
        if self._logger is None:
            self._setup_logging()
        return self._logger
    
    def get_media_dir(self) -> str:
        """Get Anki media directory path"""
        try:
            return self.anki_main_window.col.media.dir()
        except AttributeError:
            raise RuntimeError("Anki collection not available")
    
    def get_cache_dir(self) -> str:
        """Get cache directory path"""
        from .constants import CacheConstants
        media_dir = self.get_media_dir()
        cache_dir = os.path.join(media_dir, CacheConstants.CACHE_DIR_NAME)
        
        # Ensure cache directory exists and is secure
        if not cache_dir.startswith(media_dir):
            raise ValueError("Security error: Cache directory outside media folder")
        
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
    
    def get_config(self) -> TTSConfig:
        """Get current TTS configuration"""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def update_config(self, config: TTSConfig):
        """Update current configuration"""
        self._config = config
        self._save_config(config)
        
        # Clear dependent services that need to reload
        self._audio_generator = None
        self.logger.info("Configuration updated")
    
    def _load_config(self) -> TTSConfig:
        """Load configuration from Anki"""
        try:
            # Try modern Anki API first
            saved_config = self.anki_main_window.col.get_config("gemini_tts", {})
        except AttributeError:
            # Fallback for older Anki versions
            saved_config = self.anki_main_window.col.conf.get("gemini_tts", {})
        
        return TTSConfig.from_dict(saved_config)
    
    def _save_config(self, config: TTSConfig):
        """Save configuration to Anki"""
        try:
            # Try modern Anki API first
            self.anki_main_window.col.set_config("gemini_tts", config.to_dict())
        except AttributeError:
            # Fallback for older Anki versions
            self.anki_main_window.col.conf["gemini_tts"] = config.to_dict()
    
    def get_config_service(self):
        """Get configuration service instance"""
        if self._config_service is None:
            try:
                # This will be implemented when we create the services layer
                from ..services.config_service import ConfigurationService
                self._config_service = ConfigurationService(
                    container=self,
                    logger=self.logger
                )
            except ImportError:
                # Fallback - return None for now during migration
                self.logger.warning("ConfigurationService not yet implemented")
                return None
        return self._config_service
    
    def get_cache_manager(self):
        """Get cache manager instance"""
        if self._cache_manager is None:
            try:
                # This will be implemented when we create the services layer
                from ..services.cache_manager import CacheManager
                self._cache_manager = CacheManager(
                    cache_dir=self.get_cache_dir(),
                    config=self.get_config(),
                    logger=self.logger
                )
            except ImportError:
                # Fallback - return None for now during migration
                self.logger.warning("CacheManager not yet implemented")
                return None
        return self._cache_manager
    
    def get_content_analyzer(self):
        """Get content analyzer instance"""
        if self._content_analyzer is None:
            try:
                # Import the existing content analyzer
                from .content_analyzer import ContentAnalyzer
                self._content_analyzer = ContentAnalyzer()
            except ImportError:
                self.logger.warning("ContentAnalyzer not available")
                return None
        return self._content_analyzer
    
    def get_text_processor(self):
        """Get text processor instance"""
        if self._text_processor is None:
            try:
                # This will be implemented when we create the services layer
                from ..services.text_processor import TextProcessor
                self._text_processor = TextProcessor(
                    config=self.get_config(),
                    content_analyzer=self.get_content_analyzer(),
                    logger=self.logger
                )
            except ImportError:
                # Fallback - return None for now during migration
                self.logger.warning("TextProcessor not yet implemented")
                return None
        return self._text_processor
    
    def get_audio_generator(self):
        """Get audio generator instance"""
        if self._audio_generator is None:
            try:
                # This will be implemented when we create the services layer
                from ..services.audio_generator import AudioGenerator
                self._audio_generator = AudioGenerator(
                    config=self.get_config(),
                    cache_manager=self.get_cache_manager(),
                    text_processor=self.get_text_processor(),
                    logger=self.logger
                )
            except ImportError:
                # Fallback - return None for now during migration
                self.logger.warning("AudioGenerator not yet implemented")
                return None
        return self._audio_generator
    
    def get_editor_integration(self):
        """Get editor integration instance"""
        if self._editor_integration is None:
            try:
                # This will be implemented when we create the UI layer
                from ..ui.editor_integration import EditorIntegration
                self._editor_integration = EditorIntegration(
                    container=self,
                    logger=self.logger
                )
            except ImportError:
                # Fallback - return None for now during migration
                self.logger.warning("EditorIntegration not yet implemented")
                return None
        return self._editor_integration
    
    def cleanup(self):
        """Clean up resources and services"""
        self.logger.info("Cleaning up TTS container")
        
        # Clean up cache if available
        cache_manager = self.get_cache_manager()
        if cache_manager:
            try:
                cache_manager.cleanup_expired_files()
            except Exception as e:
                self.logger.error("Error during cache cleanup", exception=e)
        
        # Clear all service instances
        self._config_service = None
        self._cache_manager = None
        self._content_analyzer = None
        self._text_processor = None
        self._audio_generator = None
        self._editor_integration = None
        
        self.logger.info("TTS container cleanup completed")
    
    def reset_services(self):
        """Reset all services (useful for config changes)"""
        self.logger.info("Resetting TTS services")
        
        # Keep config and logger, clear everything else
        self._config_service = None
        self._cache_manager = None
        self._content_analyzer = None
        self._text_processor = None
        self._audio_generator = None
        self._editor_integration = None
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all services"""
        health = {}
        
        try:
            # Check Anki integration
            health["anki_main_window"] = self._mw is not None
            health["anki_collection"] = bool(self.get_media_dir())
            
            # Check configuration
            config = self.get_config()
            health["configuration"] = config.validate()
            
            # Check cache directory
            health["cache_directory"] = os.path.exists(self.get_cache_dir())
            
            # Check services (will be None during migration)
            health["config_service"] = self.get_config_service() is not None
            health["cache_manager"] = self.get_cache_manager() is not None
            health["content_analyzer"] = self.get_content_analyzer() is not None
            health["text_processor"] = self.get_text_processor() is not None
            health["audio_generator"] = self.get_audio_generator() is not None
            health["editor_integration"] = self.get_editor_integration() is not None
            
        except Exception as e:
            self.logger.error("Error during health check", exception=e)
            health["error"] = str(e)
        
        return health
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about loaded services"""
        return {
            "config_loaded": self._config is not None,
            "config_service_loaded": self._config_service is not None,
            "cache_manager_loaded": self._cache_manager is not None,
            "content_analyzer_loaded": self._content_analyzer is not None,
            "text_processor_loaded": self._text_processor is not None,
            "audio_generator_loaded": self._audio_generator is not None,
            "editor_integration_loaded": self._editor_integration is not None,
            "logger_available": self._logger is not None
        }

# Global container instance for backwards compatibility during migration
_global_container: Optional[TTSContainer] = None

def get_global_container() -> TTSContainer:
    """Get global container instance"""
    global _global_container
    if _global_container is None:
        _global_container = TTSContainer()
    return _global_container

def set_global_container(container: TTSContainer):
    """Set global container instance"""
    global _global_container
    _global_container = container

def cleanup_global_container():
    """Clean up global container"""
    global _global_container
    if _global_container:
        _global_container.cleanup()
        _global_container = None