# -*- coding: utf-8 -*-
"""
Text Processing Service
======================

Handles text normalization and preprocessing for optimal TTS output.
"""

import re
from typing import Optional

from ..core.models import TTSConfig
from ..core.constants import ProcessingConstants
from ..core.logging_config import TTSLogger

class TextProcessor:
    """Service for text preprocessing and normalization"""
    
    def __init__(self, config: TTSConfig, content_analyzer=None, logger: Optional[TTSLogger] = None):
        self.config = config
        self.content_analyzer = content_analyzer
        self.logger = logger or TTSLogger("text_processor")
    
    def preprocess_text(self, text: str) -> str:
        """Main preprocessing entry point"""
        if not self.config.enable_style_control:
            return text
        
        # Apply preprocessing pipeline
        processed = self._normalize_whitespace(text)
        processed = self._handle_bullets(processed)
        processed = self._handle_numbers(processed)
        processed = self._normalize_punctuation(processed)
        processed = self._apply_style_formatting(processed)
        
        return processed
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace and line breaks"""
        # Collapse multiple spaces
        text = re.sub(r' +', ' ', text)
        # Normalize line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Trim lines
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)
    
    def _handle_bullets(self, text: str) -> str:
        """Convert bullet points to speech-friendly format"""
        # Convert various bullet formats
        text = re.sub(r'^\s*[-•*▪▫]\s*', 'Item: ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[►▬]\s*', 'Point: ', text, flags=re.MULTILINE)
        return text
    
    def _handle_numbers(self, text: str) -> str:
        """Convert numbered lists to speech format"""
        # Convert numbered lists
        text = re.sub(r'^\s*(\d+)\.\s*', r'Step \1: ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*(\d+)\)\s*', r'Number \1: ', text, flags=re.MULTILINE)
        return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation for better speech flow"""
        # Add pauses after colons
        text = re.sub(r':(?!\s)', ': ', text)
        # Normalize ellipsis
        text = re.sub(r'\.{3,}', '...', text)
        # Handle parenthetical content
        text = re.sub(r'\(([^)]+)\)', r', \1,', text)
        return text
    
    def _apply_style_formatting(self, text: str) -> str:
        """Apply style-specific formatting"""
        style = self.config.preprocessing_style
        
        if style == "professional":
            # Add formal transitions
            text = re.sub(r'\n([A-Z])', r'\n\nNext, \1', text)
        elif style == "conversational":
            # Add casual connectors
            text = re.sub(r'\n\n', '\n\nNow, ', text)
        elif style == "technical":
            # Preserve technical formatting
            pass
        
        return text
    
    def validate_text_length(self, text: str) -> bool:
        """Validate text is within API limits"""
        return len(text) <= 5000
    
    def truncate_text(self, text: str, max_length: int = 5000) -> str:
        """Safely truncate text to fit limits"""
        if len(text) <= max_length:
            return text
        
        # Find last complete sentence within limit
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        if last_period > max_length * 0.8:
            return truncated[:last_period + 1]
        
        return truncated.rstrip() + "..."