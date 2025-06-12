# -*- coding: utf-8 -*-
"""
Configuration Dialog - Pure UI Implementation
=============================================

Qt-based configuration interface with dependency injection.
Separated from business logic for testability.
"""

from typing import Dict, Any, Optional, Callable
from aqt import mw
from aqt.theme import theme_manager
from aqt.qt import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
                    QCheckBox, QPushButton, QSpinBox, QDoubleSpinBox, QMessageBox,
                    QHBoxLayout, QLabel, QGroupBox, QTabWidget, QWidget,
                    QSlider, QTextEdit, Qt)

from .dialogs.base_dialog import BaseDialog

class ConfigDialog(BaseDialog):
    """Pure UI configuration dialog with service injection."""
    
    def __init__(self, 
                 get_config: Callable[[], Dict[str, Any]],
                 save_config: Callable[[Dict[str, Any]], bool],
                 get_models: Callable[[], Dict[str, Dict[str, Any]]],
                 get_voices: Callable[[], list],
                 test_api_key: Callable[[Dict[str, Any]], tuple],
                 test_unified_mode: Callable[[Dict[str, Any]], tuple],
                 cleanup_cache: Callable[[], int],
                 preview_processing: Callable[[str, Dict[str, Any]], str],
                 parent=None):
        """
        Initialize dialog with injected service functions.
        
        Args:
            get_config: Function to retrieve current configuration
            save_config: Function to save configuration (returns success bool)
            get_models: Function to get available models
            get_voices: Function to get available voices
            test_api_key: Function to test API key (returns success, message)
            test_unified_mode: Function to test unified mode (returns success, message) 
            cleanup_cache: Function to cleanup cache (returns cleaned count)
            preview_processing: Function to preview text processing
            parent: Parent widget
        """
        super().__init__(parent or mw, "Gemini TTS Configuration", 600, 700)
        
        # Inject service functions
        self._get_config = get_config
        self._save_config = save_config
        self._get_models = get_models
        self._get_voices = get_voices
        self._test_api_key = test_api_key
        self._test_unified_mode = test_unified_mode
        self._cleanup_cache = cleanup_cache
        self._preview_processing = preview_processing
        
        self._setup_ui()
        self._load_current_config()
    
    def _setup_ui(self):
        """Create and arrange all UI elements with tabs."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Basic Settings Tab
        basic_tab = QWidget()
        self._setup_basic_tab(basic_tab)
        self.tab_widget.addTab(basic_tab, "Basic Settings")
        
        # Advanced Settings Tab
        advanced_tab = QWidget()
        self._setup_advanced_tab(advanced_tab)
        self.tab_widget.addTab(advanced_tab, "Advanced")
        
        # Processing Settings Tab
        processing_tab = QWidget()
        self._setup_processing_tab(processing_tab)
        self.tab_widget.addTab(processing_tab, "Processing")
        
        layout.addWidget(self.tab_widget)
        
        # Button section at bottom
        self._create_button_section(layout)
    
    def _setup_basic_tab(self, tab):
        """Setup basic configuration tab."""
        layout = QVBoxLayout(tab)
        
        # API Configuration Group
        api_group = QGroupBox("API Configuration")
        api_form = QFormLayout(api_group)
        
        # API Key input field
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your Gemini API key")
        api_form.addRow("API Key:", self.api_key_input)
        
        # Model selection dropdown
        self.model_combo = QComboBox()
        models = self._get_models()
        for model_key, model_info in models.items():
            self.model_combo.addItem(model_info["display_name"], model_key)
        api_form.addRow("Model:", self.model_combo)
        
        # Processing Mode selection
        self.processing_mode_combo = QComboBox()
        self.processing_mode_combo.addItem("Unified (Recommended)", "unified")
        self.processing_mode_combo.addItem("Traditional", "traditional") 
        self.processing_mode_combo.addItem("Hybrid", "hybrid")
        self.processing_mode_combo.addItem("Auto-Select", "auto")
        api_form.addRow("Processing Mode:", self.processing_mode_combo)
        
        layout.addWidget(api_group)
        
        # Voice Configuration Group
        voice_group = QGroupBox("Voice & Audio Settings")
        voice_form = QFormLayout(voice_group)
        
        # Voice selection dropdown
        self.voice_combo = QComboBox()
        voices = self._get_voices()
        self.voice_combo.addItems(voices)
        voice_form.addRow("Voice:", self.voice_combo)
        
        # Temperature setting
        self.temp_spinner = QDoubleSpinBox()
        self.temp_spinner.setRange(0.0, 2.0)
        self.temp_spinner.setSingleStep(0.1)
        self.temp_spinner.setDecimals(1)
        self.temp_spinner.setToolTip("0.0 = deterministic, 1.0 = balanced, 2.0 = creative")
        voice_form.addRow("Temperature:", self.temp_spinner)
        
        layout.addWidget(voice_group)
        
        # Information section
        self._create_info_section(layout)
        
        layout.addStretch()
    
    def _setup_advanced_tab(self, tab):
        """Setup advanced configuration tab."""
        layout = QVBoxLayout(tab)
        
        # Thinking Budget Group
        thinking_group = QGroupBox("AI Reasoning Control")
        thinking_layout = QVBoxLayout(thinking_group)
        
        # Thinking budget slider
        budget_layout = QHBoxLayout()
        budget_layout.addWidget(QLabel("Thinking Budget:"))
        
        self.thinking_budget_slider = QSlider()
        self.thinking_budget_slider.setOrientation(Qt.Orientation.Horizontal)
        self.thinking_budget_slider.setRange(0, 1024)
        self.thinking_budget_slider.setValue(0)
        self.thinking_budget_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.thinking_budget_slider.setTickInterval(256)
        
        self.thinking_budget_label = QLabel("0 tokens")
        self.thinking_budget_slider.valueChanged.connect(
            lambda v: self.thinking_budget_label.setText(f"{v} tokens")
        )
        
        budget_layout.addWidget(self.thinking_budget_slider)
        budget_layout.addWidget(self.thinking_budget_label)
        thinking_layout.addLayout(budget_layout)
        
        # Budget explanation
        budget_info = QLabel(
            "Thinking Budget controls how much the AI reasons before responding:\n"
            "• 0 tokens: Fast, cost-efficient (recommended for simple text)\n"
            "• 256-512: Better handling of complex lists and structure\n"
            "• 512+: Advanced reasoning for technical content"
        )
        budget_info.setWordWrap(True)
        budget_info.setStyleSheet("color: gray; font-size: 10px; padding: 5px;")
        thinking_layout.addWidget(budget_info)
        
        layout.addWidget(thinking_group)
        
        # Cache Configuration Group
        cache_group = QGroupBox("Cache Settings")
        cache_form = QFormLayout(cache_group)
        
        self.cache_enabled = QCheckBox("Enable caching")
        cache_form.addRow("Cache:", self.cache_enabled)
        
        self.cache_days = QSpinBox()
        self.cache_days.setRange(1, 365)
        self.cache_days.setSuffix(" days")
        cache_form.addRow("Keep cache for:", self.cache_days)
        
        layout.addWidget(cache_group)
        
        # Performance Group
        perf_group = QGroupBox("Performance Settings")
        perf_form = QFormLayout(perf_group)
        
        self.enable_fallback = QCheckBox("Enable fallback to traditional mode on errors")
        self.enable_fallback.setChecked(True)
        perf_form.addRow("Fallback:", self.enable_fallback)
        
        self.cache_preprocessing = QCheckBox("Cache preprocessing results")
        self.cache_preprocessing.setChecked(True)
        perf_form.addRow("Preprocessing Cache:", self.cache_preprocessing)
        
        layout.addWidget(perf_group)
        
        layout.addStretch()
    
    def _setup_processing_tab(self, tab):
        """Setup text processing configuration tab."""
        layout = QVBoxLayout(tab)
        
        # Preprocessing Style Group
        style_group = QGroupBox("Preprocessing Style")
        style_form = QFormLayout(style_group)
        
        self.preprocessing_style_combo = QComboBox()
        self.preprocessing_style_combo.addItem("Natural", "natural")
        self.preprocessing_style_combo.addItem("Professional", "professional")
        self.preprocessing_style_combo.addItem("Conversational", "conversational")
        self.preprocessing_style_combo.addItem("Technical", "technical")
        style_form.addRow("Style:", self.preprocessing_style_combo)
        
        self.enable_style_control = QCheckBox("Enable advanced style control")
        self.enable_style_control.setChecked(True)
        style_form.addRow("Style Control:", self.enable_style_control)
        
        layout.addWidget(style_group)
        
        # Content Detection Group
        detection_group = QGroupBox("Content Detection")
        detection_form = QFormLayout(detection_group)
        
        self.auto_detect_content = QCheckBox("Automatically detect content type")
        self.auto_detect_content.setChecked(True)
        detection_form.addRow("Auto-detect:", self.auto_detect_content)
        
        self.prefer_instructions = QCheckBox("Prefer instruction-style for numbered lists")
        self.prefer_instructions.setChecked(True)
        detection_form.addRow("Instructions:", self.prefer_instructions)
        
        layout.addWidget(detection_group)
        
        # Preview Area
        preview_group = QGroupBox("Processing Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        preview_input_layout = QHBoxLayout()
        preview_input_layout.addWidget(QLabel("Test text:"))
        
        self.preview_input = QLineEdit()
        self.preview_input.setPlaceholderText("• First item\n• Second item\n• Third item")
        preview_input_layout.addWidget(self.preview_input)
        
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self._preview_processing)
        preview_input_layout.addWidget(preview_btn)
        
        preview_layout.addLayout(preview_input_layout)
        
        self.preview_output = QTextEdit()
        self.preview_output.setMaximumHeight(100)
        self.preview_output.setPlaceholderText("Processed text will appear here...")
        preview_layout.addWidget(self.preview_output)
        
        layout.addWidget(preview_group)
        
        layout.addStretch()
    
    def _create_info_section(self, parent_layout):
        """Create information section with API key instructions."""
        info_label = QLabel(
            "<b>Getting Started:</b><br>"
            "1. Get API key from <a href='https://ai.google.dev/'>ai.google.dev</a><br>"
            "2. Click 'Get API key' → 'Create API key'<br>"
            "3. Copy and paste above<br>"
            "4. Select text in Anki editor and press Ctrl+G<br><br>"
            "<b>Unified Mode:</b> AI preprocesses text for natural speech (recommended)<br>"
            "<b>Traditional Mode:</b> Basic text cleanup only"
        )
        
        info_label.setOpenExternalLinks(True)
        info_label.setWordWrap(True)
        
        bg_color = "#3a3a3a" if theme_manager.night_mode else "#f0f0f0"
        
        info_label.setStyleSheet(
            f"QLabel {{ "
            f"background-color: {bg_color}; "
            f"padding: 10px; "
            f"border-radius: 5px; "
            f"margin: 5px; "
            f"}}"
        )
        
        parent_layout.addWidget(info_label)
    
    def _create_button_section(self, parent_layout):
        """Create action buttons section."""
        button_layout = QHBoxLayout()
        
        # Test button
        test_btn = QPushButton("Test API Key")
        test_btn.clicked.connect(self._test_api_key_action)
        button_layout.addWidget(test_btn)
        
        # Cache cleanup button
        cleanup_btn = QPushButton("Clean Cache")
        cleanup_btn.clicked.connect(self._cleanup_cache_action)
        button_layout.addWidget(cleanup_btn)
        
        # Preview unified mode button
        preview_unified_btn = QPushButton("Test Unified Mode")
        preview_unified_btn.clicked.connect(self._test_unified_mode_action)
        button_layout.addWidget(preview_unified_btn)
        
        button_layout.addStretch()
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_config_action)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        parent_layout.addLayout(button_layout)
    
    def _load_current_config(self):
        """Load current configuration values into form fields."""
        config = self._get_config()
        
        # Basic settings
        self.api_key_input.setText(config.get("api_key", ""))
        
        # Set model selection
        model_key = config.get("model", "flash_unified")
        model_index = self.model_combo.findData(model_key)
        if model_index >= 0:
            self.model_combo.setCurrentIndex(model_index)
        
        # Set processing mode
        processing_mode = config.get("processing_mode", "unified")
        mode_index = self.processing_mode_combo.findData(processing_mode)
        if mode_index >= 0:
            self.processing_mode_combo.setCurrentIndex(mode_index)
        
        # Set voice selection
        voice = config.get("voice", "Zephyr")
        voice_index = self.voice_combo.findText(voice)
        if voice_index >= 0:
            self.voice_combo.setCurrentIndex(voice_index)
        
        # Advanced settings
        self.temp_spinner.setValue(config.get("temperature", 0.0))
        self.thinking_budget_slider.setValue(config.get("thinking_budget", 0))
        self.thinking_budget_label.setText(f"{config.get('thinking_budget', 0)} tokens")
        
        # Cache settings
        self.cache_enabled.setChecked(config.get("enable_cache", True))
        self.cache_days.setValue(config.get("cache_days", 30))
        
        # Performance settings
        self.enable_fallback.setChecked(config.get("enable_fallback", True))
        self.cache_preprocessing.setChecked(config.get("cache_preprocessing", True))
        
        # Processing settings
        preprocessing_style = config.get("preprocessing_style", "natural")
        style_index = self.preprocessing_style_combo.findData(preprocessing_style)
        if style_index >= 0:
            self.preprocessing_style_combo.setCurrentIndex(style_index)
        
        self.enable_style_control.setChecked(config.get("enable_style_control", True))
        self.auto_detect_content.setChecked(config.get("auto_detect_content", True))
        self.prefer_instructions.setChecked(config.get("prefer_instructions", True))
    
    def _get_form_config(self) -> Dict[str, Any]:
        """Extract configuration from form fields."""
        return {
            # Basic settings
            "api_key": self.api_key_input.text().strip(),
            "model": self.model_combo.currentData(),
            "processing_mode": self.processing_mode_combo.currentData(),
            "voice": self.voice_combo.currentText(),
            "temperature": self.temp_spinner.value(),
            
            # Advanced settings
            "thinking_budget": self.thinking_budget_slider.value(),
            "enable_cache": self.cache_enabled.isChecked(),
            "cache_days": self.cache_days.value(),
            "enable_fallback": self.enable_fallback.isChecked(),
            "cache_preprocessing": self.cache_preprocessing.isChecked(),
            
            # Processing settings
            "preprocessing_style": self.preprocessing_style_combo.currentData(),
            "enable_style_control": self.enable_style_control.isChecked(),
            "auto_detect_content": self.auto_detect_content.isChecked(),
            "prefer_instructions": self.prefer_instructions.isChecked()
        }
    
    def _save_config_action(self):
        """Validate and save configuration settings."""
        config = self._get_form_config()
        
        if not config["api_key"]:
            QMessageBox.warning(self, "Error", "API key is required")
            return
        
        try:
            success = self._save_config(config)
            if success:
                QMessageBox.information(self, "Success", "Configuration saved successfully")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{e}")
    
    def _test_api_key_action(self):
        """Test the entered API key with current settings."""
        config = self._get_form_config()
        
        if not config["api_key"]:
            QMessageBox.warning(self, "Error", "Please enter an API key first")
            return
        
        try:
            success, message = self._test_api_key(config)
            
            if success:
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.critical(self, "Error", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"API test failed:\n{e}")
    
    def _test_unified_mode_action(self):
        """Test unified mode with sample structured text."""
        config = self._get_form_config()
        
        if not config["api_key"]:
            QMessageBox.warning(self, "Error", "Please enter an API key first")
            return
        
        try:
            success, message = self._test_unified_mode(config)
            
            if success:
                QMessageBox.information(self, "Unified Mode Test", message)
            else:
                QMessageBox.critical(self, "Error", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unified mode test failed:\n{e}")
    
    def _cleanup_cache_action(self):
        """Clean up expired cache files and show results."""
        try:
            cleaned = self._cleanup_cache()
            
            if cleaned > 0:
                QMessageBox.information(
                    self, "Cache Cleanup", 
                    f"Cleaned up {cleaned} expired cache files."
                )
            else:
                QMessageBox.information(
                    self, "Cache Cleanup", 
                    "No expired cache files found."
                )
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cache cleanup failed: {e}")
    
    def _preview_processing(self):
        """Preview text processing with current settings."""
        input_text = self.preview_input.text().strip()
        if not input_text:
            input_text = "• First item\n• Second item\n• Third item"
        
        try:
            config = self._get_form_config()
            result = self._preview_processing(input_text, config)
            self.preview_output.setText(result)
            
        except Exception as e:
            self.preview_output.setText(f"Preview error: {e}")


def show_config_dialog():
    """Factory function to create and show configuration dialog with service injection."""
    try:
        # Import container to get services (assumes services layer exists)
        from ..core.container import get_global_container
        
        container = get_global_container()
        config_service = container.get_config_service()
        audio_generator = container.get_audio_generator()
        cache_manager = container.get_cache_manager()
        content_analyzer = container.get_content_analyzer()
        
        # Create dialog with injected services
        dialog = ConfigDialog(
            get_config=config_service.get_config,
            save_config=config_service.save_config,
            get_models=audio_generator.get_available_models,
            get_voices=audio_generator.get_available_voices,
            test_api_key=config_service.test_api_key,
            test_unified_mode=config_service.test_unified_mode,
            cleanup_cache=cache_manager.cleanup_cache,
            preview_processing=content_analyzer.preview_processing
        )
        
        if hasattr(dialog, 'exec_'):
            dialog.exec_()
        else:
            dialog.exec()
        
    except Exception as e:
        from aqt.utils import showInfo
        showInfo(f"Configuration error: {e}")