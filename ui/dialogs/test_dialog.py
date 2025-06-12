# -*- coding: utf-8 -*-
"""
TTS Testing Dialog
==================

Specialized dialog for testing TTS functionality with detailed results.
"""

import time
from typing import Dict, Any, Callable, Tuple
from aqt.qt import (QVBoxLayout, QHBoxLayout, QFormLayout, QTextEdit, QLineEdit,
                    QComboBox, QPushButton, QProgressBar, QLabel, QGroupBox,
                    QTabWidget, QWidget, QSpinBox, QCheckBox)

from .base_dialog import BaseDialog


class TestDialog(BaseDialog):
    """Comprehensive TTS testing interface."""
    
    def __init__(self, 
                 get_config: Callable[[], Dict[str, Any]],
                 get_models: Callable[[], Dict[str, Dict[str, Any]]],
                 get_voices: Callable[[], list],
                 test_api_key: Callable[[Dict[str, Any]], Tuple[bool, str]],
                 test_audio_generation: Callable[[str, Dict[str, Any]], Tuple[bool, str, float]],
                 analyze_content: Callable[[str], Dict[str, Any]],
                 parent=None):
        """
        Initialize test dialog with service injection.
        
        Args:
            get_config: Function to retrieve current configuration
            get_models: Function to get available models
            get_voices: Function to get available voices
            test_api_key: Function to test API key (returns success, message)
            test_audio_generation: Function to test audio generation (returns success, message, duration)
            analyze_content: Function to analyze content structure
            parent: Parent widget
        """
        super().__init__(parent, "TTS Testing Suite", 700, 600)
        
        # Inject service functions
        self._get_config = get_config
        self._get_models = get_models
        self._get_voices = get_voices
        self._test_api_key = test_api_key
        self._test_audio_generation = test_audio_generation
        self._analyze_content = analyze_content
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        """Setup test dialog UI with tabs."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # API Testing Tab
        api_tab = QWidget()
        self._setup_api_tab(api_tab)
        self.tab_widget.addTab(api_tab, "API Testing")
        
        # Audio Generation Tab
        audio_tab = QWidget()
        self._setup_audio_tab(audio_tab)
        self.tab_widget.addTab(audio_tab, "Audio Generation")
        
        # Content Analysis Tab
        analysis_tab = QWidget()
        self._setup_analysis_tab(analysis_tab)
        self.tab_widget.addTab(analysis_tab, "Content Analysis")
        
        layout.addWidget(self.tab_widget)
        
        # Results area
        self._create_results_section(layout)
        
        # Button section
        buttons = {
            "Close": self.accept
        }
        layout.addLayout(self.create_button_box(buttons))
    
    def _setup_api_tab(self, tab):
        """Setup API testing tab."""
        layout = QVBoxLayout(tab)
        
        # API Configuration
        config_group = QGroupBox("API Configuration")
        config_layout = QFormLayout(config_group)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter API key to test")
        config_layout.addRow("API Key:", self.api_key_input)
        
        self.model_combo = QComboBox()
        config_layout.addRow("Model:", self.model_combo)
        
        layout.addWidget(config_group)
        
        # Test Controls
        test_group = QGroupBox("API Tests")
        test_layout = QVBoxLayout(test_group)
        
        # Basic API test
        api_test_layout = QHBoxLayout()
        api_test_btn = QPushButton("Test API Key")
        api_test_btn.clicked.connect(self._test_api_key_action)
        api_test_layout.addWidget(api_test_btn)
        
        self.api_test_progress = QProgressBar()
        self.api_test_progress.setVisible(False)
        api_test_layout.addWidget(self.api_test_progress)
        
        test_layout.addLayout(api_test_layout)
        
        # Connection test
        conn_test_layout = QHBoxLayout()
        conn_test_btn = QPushButton("Test Connection")
        conn_test_btn.clicked.connect(self._test_connection)
        conn_test_layout.addWidget(conn_test_btn)
        
        self.conn_test_progress = QProgressBar()
        self.conn_test_progress.setVisible(False)
        conn_test_layout.addWidget(self.conn_test_progress)
        
        test_layout.addLayout(conn_test_layout)
        
        layout.addWidget(test_group)
        layout.addStretch()
    
    def _setup_audio_tab(self, tab):
        """Setup audio generation testing tab."""
        layout = QVBoxLayout(tab)
        
        # Test Configuration
        config_group = QGroupBox("Generation Settings")
        config_layout = QFormLayout(config_group)
        
        self.voice_combo = QComboBox()
        config_layout.addRow("Voice:", self.voice_combo)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Unified", "Traditional", "Hybrid", "Auto"])
        config_layout.addRow("Mode:", self.mode_combo)
        
        self.thinking_budget = QSpinBox()
        self.thinking_budget.setRange(0, 1024)
        self.thinking_budget.setSuffix(" tokens")
        config_layout.addRow("Thinking Budget:", self.thinking_budget)
        
        layout.addWidget(config_group)
        
        # Test Text Input
        text_group = QGroupBox("Test Text")
        text_layout = QVBoxLayout(text_group)
        
        self.test_text = QTextEdit()
        self.test_text.setPlaceholderText("Enter text to test audio generation...")
        self.test_text.setMaximumHeight(100)
        text_layout.addWidget(self.test_text)
        
        # Preset text buttons
        preset_layout = QHBoxLayout()
        
        simple_btn = QPushButton("Simple Text")
        simple_btn.clicked.connect(lambda: self.test_text.setText("Hello, this is a simple test."))
        preset_layout.addWidget(simple_btn)
        
        list_btn = QPushButton("Bullet List")
        list_btn.clicked.connect(lambda: self.test_text.setText("Key features:\n• High quality audio\n• Fast processing\n• Multiple voices"))
        preset_layout.addWidget(list_btn)
        
        complex_btn = Q