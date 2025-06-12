# -*- coding: utf-8 -*-
"""
Audio Generation Service
=======================

Handles Gemini API communication and audio generation with caching support.
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Dict, Any, Tuple

from ..core.models import TTSConfig, AudioGenerationRequest, AudioGenerationResult, Result
from ..core.constants import APIConstants, ModelConstants, AudioConstants, VoiceConstants
from ..core.exceptions import *
from ..core.logging_config import TTSLogger, LoggedOperation

class AudioGenerator:
    """Service for generating audio via Gemini API"""
    
    def __init__(self, config: TTSConfig, cache_manager=None, text_processor=None, logger: Optional[TTSLogger] = None):
        self.config = config
        self.cache_manager = cache_manager
        self.text_processor = text_processor
        self.logger = logger or TTSLogger("audio_generator")
        
    def generate_audio(self, request: AudioGenerationRequest) -> AudioGenerationResult:
        """Generate audio from text request"""
        
        with LoggedOperation(self.logger, "generate_audio", 
                           mode=request.processing_mode, 
                           text_length=len(request.text),
                           use_cache=request.use_cache):
            
            # Check cache first
            if request.use_cache and self.cache_manager:
                cached_result = self._try_cache_lookup(request)
                if cached_result.success:
                    return cached_result
            
            # Generate new audio
            if request.processing_mode == "unified":
                return self._generate_unified(request)
            else:
                return self._generate_traditional(request)
    
    def _try_cache_lookup(self, request: AudioGenerationRequest) -> AudioGenerationResult:
        """Attempt to find cached audio"""
        try:
            cache_key = self._generate_cache_key(request)
            filename = self.cache_manager.get_cached_file(cache_key)
            
            if filename:
                self.logger.log_cache_operation("hit", cache_key=cache_key)
                return AudioGenerationResult(
                    success=True,
                    filename=filename,
                    used_cache=True,
                    processing_mode=request.processing_mode
                )
            else:
                self.logger.log_cache_operation("miss", cache_key=cache_key)
                
        except Exception as e:
            self.logger.warning("Cache lookup failed", exception=e)
        
        return AudioGenerationResult(success=False)
    
    def _generate_unified(self, request: AudioGenerationRequest) -> AudioGenerationResult:
        """Generate audio using unified preprocessing + TTS"""
        
        try:
            # Build unified prompt
            prompt = self._build_unified_prompt(request.text)
            
            # Make API call
            start_time = time.time()
            audio_data = self._call_gemini_api(
                model_id=ModelConstants.get_model_definitions()[self.config.model]["model_id"],
                prompt=prompt,
                voice=self.config.voice,
                temperature=self.config.temperature,
                thinking_budget=self.config.thinking_budget,
                timeout=APIConstants.UNIFIED_TIMEOUT
            )
            duration = time.time() - start_time
            
            self.logger.log_performance("unified_generation", duration, 
                                      audio_size=len(audio_data))
            
            # Save to cache and return
            return self._save_and_return(request, audio_data, "unified", duration)
            
        except Exception as e:
            self.logger.error("Unified generation failed", exception=e)
            return self._handle_generation_error(e, request)
    
    def _generate_traditional(self, request: AudioGenerationRequest) -> AudioGenerationResult:
        """Generate audio using traditional TTS"""
        
        try:
            # Preprocess text if needed
            processed_text = request.text
            if self.text_processor and self.config.enable_style_control:
                processed_text = self.text_processor.preprocess_text(request.text)
            
            # Make API call
            start_time = time.time()
            audio_data = self._call_gemini_api(
                model_id=ModelConstants.get_model_definitions()[self.config.model]["model_id"],
                prompt=f"Please convert this text to speech: {processed_text}",
                voice=self.config.voice,
                temperature=self.config.temperature,
                timeout=APIConstants.TRADITIONAL_TIMEOUT
            )
            duration = time.time() - start_time
            
            self.logger.log_performance("traditional_generation", duration,
                                      audio_size=len(audio_data))
            
            # Save to cache and return  
            return self._save_and_return(request, audio_data, "traditional", duration)
            
        except Exception as e:
            self.logger.error("Traditional generation failed", exception=e)
            return self._handle_generation_error(e, request)
    
    def _build_unified_prompt(self, text: str) -> str:
        """Build prompt for unified preprocessing + TTS"""
        
        base_prompt = f"""You are an expert text-to-speech specialist. Your task is to analyze the given text and convert it to natural, clear speech.

Text to process: {text}

Instructions:
1. Analyze the text structure and content type
2. Apply appropriate preprocessing for optimal speech synthesis
3. Generate natural, flowing speech output
4. Maintain the original meaning while optimizing for audio delivery"""

        if self.config.preprocessing_style != "natural":
            base_prompt += f"\n5. Use {self.config.preprocessing_style} style delivery"
            
        return base_prompt
    
    def _call_gemini_api(self, model_id: str, prompt: str, voice: str, 
                        temperature: float, timeout: float, thinking_budget: int = 0) -> bytes:
        """Make actual API call to Gemini"""
        
        # Build request payload
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "candidateCount": 1,
                "maxOutputTokens": 8192,
                "responseMimeType": AudioConstants.DEFAULT_MIME_TYPE
            },
            "voiceConfig": {
                "voice": voice
            }
        }
        
        # Add thinking budget for unified models
        if thinking_budget > 0:
            payload["generationConfig"]["thinkingBudget"] = thinking_budget
        
        # Build request
        url = f"{APIConstants.BASE_URL}/models/{model_id}:{APIConstants.GENERATE_CONTENT_ENDPOINT}"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.config.api_key
        }
        
        request_data = json.dumps(payload).encode('utf-8')
        request_obj = urllib.request.Request(url, data=request_data, headers=headers)
        
        # Make request with logging
        self.logger.log_api_call(url, "POST", duration=None, model=model_id, voice=voice)
        
        try:
            with urllib.request.urlopen(request_obj, timeout=timeout) as response:
                if response.status != 200:
                    raise create_api_exception(response.status, f"HTTP {response.status}")
                
                response_data = response.read()
                self.logger.log_api_call(url, "POST", status_code=response.status, 
                                       response_size=len(response_data))
                
                return self._extract_audio_data(response_data)
                
        except urllib.error.HTTPError as e:
            self.logger.log_api_call(url, "POST", status_code=e.code)
            raise handle_http_error(e)
        except urllib.error.URLError as e:
            raise handle_network_error(e)
        except Exception as e:
            raise APIException(f"API call failed: {str(e)}")
    
    def _extract_audio_data(self, response_data: bytes) -> bytes:
        """Extract audio data from API response"""
        
        try:
            # Parse JSON response
            response_json = json.loads(response_data.decode('utf-8'))
            
            # Extract audio content
            if "candidates" not in response_json:
                raise APIException("Invalid API response: no candidates")
            
            candidate = response_json["candidates"][0]
            if "content" not in candidate:
                raise APIException("Invalid API response: no content")
            
            content = candidate["content"]
            if "parts" not in content:
                raise APIException("Invalid API response: no parts")
            
            # Get audio data (base64 encoded)
            part = content["parts"][0]
            if "inlineData" not in part:
                raise APIException("Invalid API response: no audio data")
            
            audio_b64 = part["inlineData"]["data"]
            
            # Decode base64 audio
            import base64
            audio_data = base64.b64decode(audio_b64)
            
            # Validate audio data
            if len(audio_data) < AudioConstants.MIN_AUDIO_SIZE:
                raise AudioSizeException("Audio data too small", len(audio_data))
            
            if len(audio_data) > AudioConstants.MAX_AUDIO_SIZE:
                raise AudioSizeException("Audio data too large", len(audio_data))
            
            return audio_data
            
        except json.JSONDecodeError as e:
            raise APIException(f"Invalid JSON response: {str(e)}")
        except KeyError as e:
            raise APIException(f"Missing response field: {str(e)}")
        except Exception as e:
            raise AudioException(f"Audio extraction failed: {str(e)}")
    
    def _save_and_return(self, request: AudioGenerationRequest, audio_data: bytes, 
                        mode: str, duration: float) -> AudioGenerationResult:
        """Save audio to cache and return result"""
        
        filename = None
        
        # Try to save to cache
        if self.cache_manager and request.use_cache:
            try:
                cache_key = self._generate_cache_key(request)
                filename = self.cache_manager.save_audio(cache_key, audio_data)
                self.logger.log_cache_operation("save", cache_key=cache_key, 
                                              file_size=len(audio_data))
            except Exception as e:
                self.logger.warning("Cache save failed", exception=e)
                # Continue without cache - not critical
        
        return AudioGenerationResult(
            success=True,
            filename=filename,
            used_cache=False,
            processing_mode=mode,
            generation_time=duration
        )
    
    def _generate_cache_key(self, request: AudioGenerationRequest) -> str:
        """Generate cache key for request"""
        
        import hashlib
        
        key_data = {
            "text": request.text,
            "model": self.config.model,
            "voice": self.config.voice,
            "temperature": self.config.temperature,
            "mode": request.processing_mode,
            "style": self.config.preprocessing_style if self.config.enable_style_control else None,
            "thinking_budget": self.config.thinking_budget if request.processing_mode == "unified" else 0
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def _handle_generation_error(self, error: Exception, request: AudioGenerationRequest) -> AudioGenerationResult:
        """Handle generation errors with fallback logic"""
        
        # Try fallback if enabled and not already using fallback
        if (self.config.enable_fallback and 
            self.config.model != ModelConstants.DEFAULT_FALLBACK_MODEL and
            not isinstance(error, (InvalidAPIKeyException, RateLimitedException))):
            
            self.logger.info("Attempting fallback generation", 
                           original_model=self.config.model,
                           fallback_model=ModelConstants.DEFAULT_FALLBACK_MODEL)
            
            # Create fallback request
            fallback_config = TTSConfig.from_dict(self.config.to_dict())
            fallback_config.model = ModelConstants.DEFAULT_FALLBACK_MODEL
            
            # Update our config temporarily
            original_model = self.config.model
            self.config.model = ModelConstants.DEFAULT_FALLBACK_MODEL
            
            try:
                # Try traditional generation as fallback
                fallback_request = AudioGenerationRequest(
                    text=request.text,
                    config=fallback_config,
                    processing_mode="traditional",
                    use_cache=request.use_cache
                )
                
                result = self._generate_traditional(fallback_request)
                if result.success:
                    self.logger.info("Fallback generation succeeded")
                    return result
                    
            except Exception as fallback_error:
                self.logger.error("Fallback generation also failed", exception=fallback_error)
            finally:
                # Restore original model
                self.config.model = original_model
        
        # Return error result
        error_message = getattr(error, 'user_message', str(error))
        error_code = getattr(error, 'error_code', None)
        
        return AudioGenerationResult(
            success=False,
            error_message=error_message,
            processing_mode=request.processing_mode
        )
    
    def test_api_connection(self) -> Result:
        """Test API connection with current configuration"""
        
        with LoggedOperation(self.logger, "test_api_connection", model=self.config.model):
            
            test_text = "Testing API connection."
            
            try:
                start_time = time.time()
                
                # Use simple traditional call for testing
                audio_data = self._call_gemini_api(
                    model_id=ModelConstants.get_model_definitions()[self.config.model]["model_id"],
                    prompt=f"Please convert this text to speech: {test_text}",
                    voice=self.config.voice,
                    temperature=0.0,
                    timeout=APIConstants.TRADITIONAL_TIMEOUT
                )
                
                duration = time.time() - start_time
                
                return Result.success_result({
                    "response_time": round(duration, 2),
                    "audio_size": len(audio_data),
                    "model": self.config.model,
                    "voice": self.config.voice
                })
                
            except Exception as e:
                self.logger.error("API test failed", exception=e)
                error_message = getattr(e, 'user_message', str(e))
                error_code = getattr(e, 'error_code', None)
                return Result.error_result(error_message, error_code)
            
    def get_available_voices(self) -> list:
        """Get a list of available TTS voice names."""
        return VoiceConstants.get_all_voices()
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get available model definitions"""
        return ModelConstants.get_model_definitions()
    
    def validate_model_config(self) -> Result:
        """Validate current model configuration"""
        
        model_defs = self.get_available_models()
        
        if self.config.model not in model_defs:
            return Result.error_result(f"Invalid model: {self.config.model}")
        
        model_info = model_defs[self.config.model]
        
        # Check thinking budget range
        if "thinking_budget_range" in model_info:
            min_budget, max_budget = model_info["thinking_budget_range"]
            if not (min_budget <= self.config.thinking_budget <= max_budget):
                return Result.error_result(
                    f"Thinking budget {self.config.thinking_budget} outside range [{min_budget}, {max_budget}]"
                )
        
        return Result.success_result("Model configuration valid")