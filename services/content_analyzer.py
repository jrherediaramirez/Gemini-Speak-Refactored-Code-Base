# -*- coding: utf-8 -*-
"""
Content Analysis Service
========================

Analyzes text structure and complexity for optimal TTS processing.
"""

import re
from typing import Optional

from ..core.models import ContentAnalysis, ProcessingMode, ContentType, ComplexityLevel
from ..core.constants import ProcessingConstants
from ..core.logging_config import TTSLogger

class ContentAnalyzer:
    """Service for analyzing text content structure"""
    
    def __init__(self, logger: Optional[TTSLogger] = None):
        self.logger = logger or TTSLogger("content_analyzer")
    
    def analyze_content(self, text: str) -> ContentAnalysis:
        """Analyze text and return structured analysis"""
        
        lines = text.strip().split('\n')
        line_count = len(lines)
        avg_line_length = sum(len(line) for line in lines) / max(line_count, 1)
        
        # Structure detection
        has_bullets = self._detect_bullets(text)
        has_numbers = self._detect_numbers(text)
        has_nested = self._detect_nested_structure(text)
        has_special_chars = self._detect_special_chars(text)
        has_technical = self._detect_technical_content(text)
        
        # Content type classification
        content_type = self._classify_content_type(text)
        complexity = self._assess_complexity(text, line_count, avg_line_length)
        
        # Processing recommendations
        thinking_budget = self._suggest_thinking_budget(content_type, complexity, has_bullets, has_numbers)
        preprocessing_strategy = self._suggest_preprocessing_strategy(content_type, complexity)
        
        # Speech time estimation
        speech_time = self._estimate_speech_time(text)
        
        return ContentAnalysis(
            content_type=content_type.value,
            complexity=complexity.value,
            has_bullets=has_bullets,
            has_numbers=has_numbers,
            line_count=line_count,
            avg_line_length=avg_line_length,
            suggested_thinking_budget=thinking_budget,
            preprocessing_strategy=preprocessing_strategy.value,
            estimated_speech_time=speech_time,
            has_nested_structure=has_nested,
            has_special_chars=has_special_chars,
            has_technical_terms=has_technical
        )
    
    def _detect_bullets(self, text: str) -> bool:
        """Detect bullet points or list markers"""
        bullet_patterns = [
            r'^\s*[-•*]\s',  # Dash, bullet, asterisk
            r'^\s*\d+\.\s',  # Numbered lists
            r'^\s*[a-zA-Z]\.\s',  # Lettered lists
            r'^\s*[►▪▫▬]\s'  # Special bullets
        ]
        
        bullet_count = 0
        for line in text.split('\n'):
            if any(re.match(pattern, line) for pattern in bullet_patterns):
                bullet_count += 1
        
        return bullet_count >= ProcessingConstants.MIN_BULLET_COUNT
    
    def _detect_numbers(self, text: str) -> bool:
        """Detect numbered sequences or structured data"""
        number_patterns = [
            r'\b\d+\.\s',  # "1. "
            r'\b\d+\)\s',  # "1) "
            r'Step\s+\d+',  # "Step 1"
            r'\(\d+\)',    # "(1)"
            r'\b\d{2,}\b'  # Multi-digit numbers
        ]
        
        number_count = sum(len(re.findall(pattern, text, re.IGNORECASE)) 
                          for pattern in number_patterns)
        
        return number_count >= ProcessingConstants.MIN_NUMBERED_COUNT
    
    def _detect_nested_structure(self, text: str) -> bool:
        """Detect nested or hierarchical content"""
        nested_patterns = [
            r'^\s{2,}[-•*]\s',  # Indented bullets
            r'^\s+\w+:',       # Indented labels
            r'^\s{4,}\S'       # Deep indentation
        ]
        
        return any(re.search(pattern, text, re.MULTILINE) for pattern in nested_patterns)
    
    def _detect_special_chars(self, text: str) -> bool:
        """Detect special characters that need processing"""
        special_chars = ['©', '®', '™', '§', '¶', '†', '‡', '•', '→', '←', '↑', '↓']
        return any(char in text for char in special_chars)
    
    def _detect_technical_content(self, text: str) -> bool:
        """Detect technical terminology"""
        text_lower = text.lower()
        technical_count = sum(1 for keyword in ProcessingConstants.TECHNICAL_KEYWORDS 
                             if keyword in text_lower)
        return technical_count >= 3
    
    def _classify_content_type(self, text: str) -> ContentType:
        """Classify content type based on keywords and structure"""
        text_lower = text.lower()
        
        # Check for instruction indicators
        step_count = sum(1 for keyword in ProcessingConstants.STEP_KEYWORDS 
                        if keyword in text_lower)
        if step_count >= 2:
            return ContentType.INSTRUCTIONS
        
        # Check for feature descriptions
        feature_count = sum(1 for keyword in ProcessingConstants.FEATURE_KEYWORDS 
                           if keyword in text_lower)
        if feature_count >= 2:
            return ContentType.FEATURES
        
        # Check for options/choices
        option_count = sum(1 for keyword in ProcessingConstants.OPTION_KEYWORDS 
                          if keyword in text_lower)
        if option_count >= 2:
            return ContentType.OPTIONS
        
        # Check for technical content
        if self._detect_technical_content(text):
            return ContentType.TECHNICAL
        
        # Check for Q&A format
        if re.search(r'\?.*\n.*\w', text) or 'question' in text_lower:
            return ContentType.QA
        
        return ContentType.GENERAL
    
    def _assess_complexity(self, text: str, line_count: int, avg_line_length: float) -> ComplexityLevel:
        """Assess content complexity"""
        complexity_score = 0
        
        # Length factors
        if len(text) > ProcessingConstants.LARGE_CONTENT_THRESHOLD:
            complexity_score += 1
        if line_count > ProcessingConstants.MANY_LINES_THRESHOLD:
            complexity_score += 1
        if avg_line_length > ProcessingConstants.COMPLEX_LINE_THRESHOLD:
            complexity_score += 1
        
        # Structure factors
        if self._detect_bullets(text):
            complexity_score += 1
        if self._detect_numbers(text):
            complexity_score += 1
        if self._detect_nested_structure(text):
            complexity_score += 1
        if self._detect_technical_content(text):
            complexity_score += 2
        
        if complexity_score >= 5:
            return ComplexityLevel.HIGH
        elif complexity_score >= 2:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.LOW
    
    def _suggest_thinking_budget(self, content_type: ContentType, complexity: ComplexityLevel, 
                               has_bullets: bool, has_numbers: bool) -> int:
        """Suggest thinking budget based on content analysis"""
        
        base_budget = {
            ContentType.GENERAL: 0,
            ContentType.INSTRUCTIONS: 512,
            ContentType.FEATURES: 256,
            ContentType.OPTIONS: 256,
            ContentType.TECHNICAL: 1024,
            ContentType.QA: 512
        }
        
        budget = base_budget.get(content_type, 0)
        
        # Complexity adjustments
        if complexity == ComplexityLevel.HIGH:
            budget = int(budget * 1.5)
        elif complexity == ComplexityLevel.MEDIUM:
            budget = int(budget * 1.2)
        
        # Structure adjustments
        if has_bullets and has_numbers:
            budget += 256
        elif has_bullets or has_numbers:
            budget += 128
        
        return min(budget, 2048)  # Cap at reasonable limit
    
    def _suggest_preprocessing_strategy(self, content_type: ContentType, 
                                      complexity: ComplexityLevel) -> ProcessingMode:
        """Suggest preprocessing strategy"""
        
        if content_type in [ContentType.TECHNICAL, ContentType.INSTRUCTIONS]:
            return ProcessingMode.UNIFIED
        elif complexity == ComplexityLevel.HIGH:
            return ProcessingMode.UNIFIED
        elif complexity == ComplexityLevel.MEDIUM:
            return ProcessingMode.HYBRID
        else:
            return ProcessingMode.TRADITIONAL
    
    def _estimate_speech_time(self, text: str) -> float:
        """Estimate speech duration in seconds"""
        word_count = len(text.split())
        return (word_count / ProcessingConstants.AVERAGE_WORDS_PER_MINUTE) * 60