# -*- coding: utf-8 -*-
"""
Async Operations Service
=======================

Non-blocking I/O operations for UI responsiveness.
"""

import threading
import concurrent.futures
from typing import Callable, Any, Optional

from ..core.models import AudioGenerationRequest, AudioGenerationResult, Result
from ..core.logging_config import TTSLogger

class AsyncTTSOperations:
    """Service for async TTS operations"""
    
    def __init__(self, audio_generator, config_service, logger: Optional[TTSLogger] = None):
        self.audio_generator = audio_generator
        self.config_service = config_service
        self.logger = logger or TTSLogger("async_operations")
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    
    def generate_audio_async(self, request: AudioGenerationRequest, 
                           callback: Callable[[AudioGenerationResult], None]):
        """Generate audio asynchronously"""
        
        def _generate():
            try:
                result = self.audio_generator.generate_audio(request)
                callback(result)
            except Exception as e:
                self.logger.error("Async generation failed", exception=e)
                callback(AudioGenerationResult(success=False, error_message=str(e)))
        
        self._executor.submit(_generate)
    
    def test_api_async(self, config, callback: Callable[[Result], None]):
        """Test API connection asynchronously"""
        
        def _test():
            try:
                result = self.config_service.test_api_key(config)
                callback(result)
            except Exception as e:
                self.logger.error("Async API test failed", exception=e)
                callback(Result.error_result(str(e)))
        
        self._executor.submit(_test)
    
    def cleanup_cache_async(self, cache_manager, callback: Optional[Callable[[int], None]] = None):
        """Clean cache asynchronously"""
        
        def _cleanup():
            try:
                removed = cache_manager.cleanup_expired_files()
                if callback:
                    callback(removed)
            except Exception as e:
                self.logger.error("Async cache cleanup failed", exception=e)
                if callback:
                    callback(0)
        
        self._executor.submit(_cleanup)
    
    def shutdown(self):
        """Shutdown async operations"""
        self._executor.shutdown(wait=True)