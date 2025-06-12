# -*- coding: utf-8 -*-
"""
Anki Editor Integration - Pure UI Implementation
===============================================

Handles editor buttons, menus, and text processing integration.
Separated from business logic with dependency injection.
"""

import os
from typing import Dict, Any, Callable, Optional
from functools import partial

from aqt import mw
from aqt.qt import QTimer, QMenu, QCursor
from aqt.utils import tooltip


class EditorIntegration:
    """Pure UI editor integration with service injection."""
    
    def __init__(self,
                 get_config: Callable[[], Dict[str, Any]],
                 save_config: Callable[[Dict[str, Any]], bool],
                 get_models: Callable[[], Dict[str, Dict[str, Any]]],
                 get_voices: Callable[[], list],
                 generate_audio: Callable[[str], str],
                 normalize_text: Callable[[str], str],
                 should_use_unified: Callable[[str], bool]):
        """
        Initialize with injected service functions.
        
        Args:
            get_config: Function to retrieve current configuration
            save_config: Function to save configuration
            get_models: Function to get available models
            get_voices: Function to get available voices  
            generate_audio: Function to generate audio (returns filename)
            normalize_text: Function to normalize text for traditional mode
            should_use_unified: Function to determine if unified mode should be used
        """
        self._get_config = get_config
        self._save_config = save_config
        self._get_models = get_models
        self._get_voices = get_voices
        self._generate_audio = generate_audio
        self._normalize_text = normalize_text
        self._should_use_unified = should_use_unified
    
    def setup_editor_button(self, buttons, editor):
        """Add enhanced TTS buttons to editor toolbar."""
        try:
            # Try to load custom icon
            addon_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            icon_path = os.path.join(addon_dir, "icons", "gemini.png")
            use_icon = icon_path if os.path.exists(icon_path) else None
            
            # Get current settings for tooltip
            config = self._get_config()
            models = self._get_models()
            model_key = config.get("model", "flash_unified")
            model_info = models.get(model_key, {})
            processing_mode = config.get("processing_mode", "unified")
            current_voice = config.get("voice", "Zephyr")
            
            tip = (f"Generate Gemini TTS (Ctrl+G)\n"
                   f"Model: {model_info.get('display_name', model_key)}\n"
                   f"Mode: {processing_mode.title()}\n"
                   f"Voice: {current_voice}")
            
            # Main TTS button
            button = editor.addButton(
                icon=use_icon,
                cmd="gemini_tts",
                tip=tip,
                func=lambda ed: self.on_button_click(ed),
                keys="Ctrl+G"
            )
            
            # Mode selection button
            mode_button = editor.addButton(
                None,
                cmd="gemini_mode",
                tip=f"Processing Mode: {processing_mode.title()}\nClick to change",
                func=lambda ed: self.show_mode_menu(ed),
                label=f"Mode: {processing_mode[:3].title()}"
            )
            
            # Model selection button
            model_button = editor.addButton(
                None,
                cmd="gemini_model",
                tip=f"Model: {model_info.get('display_name', model_key)}\nClick to change",
                func=lambda ed: self.show_model_menu(ed),
                label="Model"
            )
            
            # Voice selection button  
            voice_button = editor.addButton(
                None,
                cmd="gemini_voice", 
                tip=f"Voice: {current_voice}\nClick to change",
                func=lambda ed: self.show_voice_menu(ed),
                label="Voice"
            )
            
            buttons.extend([button, mode_button, model_button, voice_button])
            
        except Exception as e:
            print(f"Gemini TTS: Button setup error - {e}")
        
        return buttons
    
    def on_button_click(self, editor):
        """Handle TTS button click in editor."""
        js_code = """
        (function() {
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                const container = document.createElement('div');
                container.appendChild(range.cloneContents());
                return {
                    plainText: selection.toString(),
                    htmlContent: container.innerHTML,
                    hasContent: selection.toString().length > 0
                };
            }
            return {
                plainText: '',
                htmlContent: '',
                hasContent: false
            };
        })();
        """
        
        editor.web.evalWithCallback(js_code, partial(self.process_selection_result, editor))
    
    def process_selection_result(self, editor, result):
        """Process the selection result from JavaScript."""
        if not result.get('hasContent', False):
            tooltip("Please select some text first")
            return
        
        raw_text = result.get('plainText', '') or result.get('htmlContent', '')
        
        if not raw_text.strip():
            tooltip("No readable text found in selection")
            return
        
        # Check if we should preprocess the text or use it as-is
        if self._should_use_unified(raw_text):
            # Unified mode will handle preprocessing
            final_text = raw_text
        else:
            # Traditional mode - apply normalization
            final_text = self._normalize_text(raw_text)
        
        if not final_text.strip():
            tooltip("Selected text cannot be converted to speech")
            return
        
        self.process_selected_text(editor, final_text)
    
    def process_selected_text(self, editor, selected_text):
        """Process selected text for TTS generation."""
        config = self._get_config()
        
        if not config.get("api_key", "").strip():
            tooltip("Please configure API key first")
            return
        
        # Show processing indicator based on mode
        processing_mode = config.get("processing_mode", "unified")
        if processing_mode == "unified":
            tooltip("Generating TTS with AI preprocessing...")
        else:
            tooltip("Generating TTS...")
        
        QTimer.singleShot(100, lambda: self.generate_and_add_audio(editor, selected_text))
    
    def generate_and_add_audio(self, editor, text):
        """Generate audio and add to note (non-blocking operation)."""
        try:
            filename = self._generate_audio(text)
            
            if self.add_audio_to_note(editor, filename):
                config = self._get_config()
                models = self._get_models()
                model_key = config.get("model", "flash_unified")
                model_info = models.get(model_key, {})
                current_voice = config.get("voice", "Zephyr")
                processing_mode = config.get("processing_mode", "unified")
                
                tooltip(f"Audio generated: {model_info.get('display_name', model_key)} ({processing_mode}) - {current_voice}")
            else:
                tooltip("Failed to add audio to note")
                
        except Exception as e:
            error_msg = str(e)
            
            if "API key" in error_msg:
                tooltip("Invalid API key - check configuration")
            elif "Rate limited" in error_msg:
                tooltip("Rate limited - wait and try again")
            elif "Network error" in error_msg:
                tooltip("Network error - check connection")
            elif "too long" in error_msg:
                tooltip("Text too long - select shorter text")
            else:
                tooltip(f"Error: {error_msg[:50]}...")
    
    def add_audio_to_note(self, editor, filename: str) -> bool:
        """Add generated audio to the detected source field in Anki note."""
        target_field = self.detect_source_field(editor)
        
        if target_field not in editor.note:
            tooltip(f"Field '{target_field}' not found")
            return False
        
        sound_tag = f"[sound:{filename}]"
        current_content = editor.note[target_field]
        
        if sound_tag not in current_content:
            if current_content.strip():
                editor.note[target_field] = f"{current_content} {sound_tag}"
            else:
                editor.note[target_field] = sound_tag
        
        editor.loadNote()
        QTimer.singleShot(100, lambda: self.focus_editor(editor))
        return True
    
    def detect_source_field(self, editor) -> str:
        """Detect which field the user is currently working in."""
        if not (editor and hasattr(editor, 'note') and editor.note):
            return "Front"
        
        if hasattr(editor, 'currentField') and editor.currentField is not None:
            field_names = list(editor.note.keys())
            if 0 <= editor.currentField < len(field_names):
                return field_names[editor.currentField]
        
        field_names = list(editor.note.keys())
        return field_names[0] if field_names else "Front"
    
    def focus_editor(self, editor):
        """Restore focus to editor web view."""
        try:
            if hasattr(editor, 'web') and hasattr(editor.web, 'setFocus'):
                editor.web.setFocus()
        except:
            pass
    
    def show_mode_menu(self, editor):
        """Show processing mode selection menu."""
        menu = QMenu(editor.widget)
        config = self._get_config()
        current_mode = config.get("processing_mode", "unified")
        
        modes = [
            ("unified", "Unified (AI + TTS)"),
            ("traditional", "Traditional (TTS Only)"),
            ("hybrid", "Hybrid (Auto-Select)"),
            ("auto", "Auto-Detect")
        ]
        
        for mode_key, mode_name in modes:
            action = menu.addAction(mode_name)
            action.setCheckable(True)
            action.setChecked(mode_key == current_mode)
            action.triggered.connect(lambda checked, mk=mode_key: self.change_processing_mode(mk))
        
        menu.exec(QCursor.pos())
    
    def show_model_menu(self, editor):
        """Show model selection menu."""
        menu = QMenu(editor.widget)
        config = self._get_config()
        models = self._get_models()
        current_model = config.get("model", "flash_unified")
        
        for model_key, model_info in models.items():
            action = menu.addAction(model_info["display_name"])
            action.setCheckable(True)
            action.setChecked(model_key == current_model)
            action.triggered.connect(lambda checked, mk=model_key: self.change_model(mk))
        
        menu.exec(QCursor.pos())
    
    def show_voice_menu(self, editor):
        """Show voice selection menu."""
        menu = QMenu(editor.widget)
        config = self._get_config()
        voices = self._get_voices()
        current_voice = config.get("voice", "Zephyr")
        
        for voice in voices:
            action = menu.addAction(voice)
            action.setCheckable(True)
            action.setChecked(voice == current_voice)
            action.triggered.connect(lambda checked, v=voice: self.change_voice(v))
        
        menu.exec(QCursor.pos())
    
    def change_processing_mode(self, mode_key):
        """Change processing mode and update configuration."""
        config = self._get_config()
        config["processing_mode"] = mode_key
        self._save_config(config)
        
        mode_names = {
            "unified": "Unified (AI + TTS)",
            "traditional": "Traditional",
            "hybrid": "Hybrid",
            "auto": "Auto-Detect"
        }
        tooltip(f"Processing mode: {mode_names.get(mode_key, mode_key)}")
    
    def change_model(self, model_key):
        """Change model and update configuration."""
        config = self._get_config()
        config["model"] = model_key
        self._save_config(config)
        
        models = self._get_models()
        model_info = models.get(model_key, {})
        tooltip(f"Model: {model_info.get('display_name', model_key)}")
    
    def change_voice(self, voice):
        """Change voice and update configuration."""
        config = self._get_config()
        config["voice"] = voice
        self._save_config(config)
        tooltip(f"Voice: {voice}")


def setup_editor_button(buttons, editor):
    """Factory function to create editor integration with service injection."""
    try:
        # Import container to get services (assumes services layer exists)
        from ..core.container import get_global_container
        
        container = get_global_container()
        config_service = container.get_configuration_service()
        audio_generator = container.get_audio_generator()
        text_processor = container.get_text_processor()
        
        # Create editor integration with injected services
        integration = EditorIntegration(
            get_config=config_service.get_config,
            save_config=config_service.save_config,
            get_models=audio_generator.get_available_models,
            get_voices=audio_generator.get_available_voices,
            generate_audio=audio_generator.generate_audio,
            normalize_text=text_processor.normalize_text,
            should_use_unified=text_processor.should_use_unified_mode
        )
        
        return integration.setup_editor_button(buttons, editor)
        
    except Exception as e:
        print(f"Gemini TTS: Cannot add button - service error: {e}")
        return buttons