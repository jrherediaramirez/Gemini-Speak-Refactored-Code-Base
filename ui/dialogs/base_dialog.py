# -*- coding: utf-8 -*-
"""
Base Dialog - Common Dialog Functionality
=========================================

Provides common dialog patterns, theming, and utilities.
"""

from typing import Optional, Dict, Any
from aqt import mw
from aqt.theme import theme_manager
from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                    QMessageBox, QLabel, QFrame, Qt)


class BaseDialog(QDialog):
    """Base dialog with common functionality and theming."""
    
    def __init__(self, parent=None, title: str = "Dialog", 
                 width: int = 400, height: int = 300):
        """
        Initialize base dialog.
        
        Args:
            parent: Parent widget
            title: Dialog window title
            width: Dialog width in pixels
            height: Dialog height in pixels
        """
        super().__init__(parent or mw)
        
        self.setWindowTitle(title)
        self.setMinimumWidth(width)
        self.setMinimumHeight(height)
        
        # Apply theme-aware styling
        self._apply_theme()
        
    def _apply_theme(self):
        """Apply theme-aware styling to dialog."""
        if theme_manager.night_mode:
            bg_color = "#2b2b2b"
            text_color = "#ffffff"
            border_color = "#555555"
        else:
            bg_color = "#ffffff"
            text_color = "#000000"
            border_color = "#cccccc"
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {border_color};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 5px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
    
    def create_button_box(self, buttons: Dict[str, callable] = None) -> QHBoxLayout:
        """
        Create standardized button box layout.
        
        Args:
            buttons: Dict of button_text: callback_function
            
        Returns:
            QHBoxLayout with buttons
        """
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if buttons:
            for text, callback in buttons.items():
                btn = QPushButton(text)
                btn.clicked.connect(callback)
                
                # Style primary buttons
                if text.lower() in ['ok', 'save', 'apply']:
                    btn.setDefault(True)
                    
                button_layout.addWidget(btn)
        
        return button_layout
    
    def create_separator(self) -> QFrame:
        """Create horizontal separator line."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line
    
    def create_info_label(self, text: str, info_type: str = "info") -> QLabel:
        """
        Create styled information label.
        
        Args:
            text: Information text
            info_type: Type of info ('info', 'warning', 'error', 'success')
            
        Returns:
            Styled QLabel
        """
        label = QLabel(text)
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        
        # Color scheme based on type
        colors = {
            "info": ("#e3f2fd", "#1976d2"),
            "warning": ("#fff3e0", "#f57c00"), 
            "error": ("#ffebee", "#d32f2f"),
            "success": ("#e8f5e8", "#388e3c")
        }
        
        if theme_manager.night_mode:
            bg_colors = {
                "info": "#1a237e",
                "warning": "#e65100",
                "error": "#b71c1c", 
                "success": "#1b5e20"
            }
            bg_color = bg_colors.get(info_type, "#3a3a3a")
            text_color = "#ffffff"
        else:
            bg_color, text_color = colors.get(info_type, ("#f0f0f0", "#000000"))
        
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: 10px;
                border-radius: 5px;
                margin: 5px;
            }}
        """)
        
        return label
    
    def show_error(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """Show warning message dialog."""
        QMessageBox.warning(self, title, message)
    
    def show_info(self, title: str, message: str):
        """Show information message dialog.""" 
        QMessageBox.information(self, title, message)
    
    def confirm(self, title: str, message: str) -> bool:
        """
        Show confirmation dialog.
        
        Returns:
            True if user confirmed, False otherwise
        """
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def validate_required_fields(self, fields: Dict[str, Any]) -> Optional[str]:
        """
        Validate required form fields.
        
        Args:
            fields: Dict of field_name: field_value
            
        Returns:
            Error message if validation fails, None if all valid
        """
        empty_fields = []
        
        for field_name, value in fields.items():
            if not value or (isinstance(value, str) and not value.strip()):
                empty_fields.append(field_name)
        
        if empty_fields:
            return f"Required fields are empty: {', '.join(empty_fields)}"
        
        return None
    
    def safe_close(self):
        """Safe dialog close with cleanup."""
        try:
            self.accept()
        except Exception as e:
            print(f"Dialog close error: {e}")
    
    def center_on_parent(self):
        """Center dialog on parent widget."""
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        # Handle Escape key
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
    
    def showEvent(self, event):
        """Handle dialog show event."""
        super().showEvent(event)
        self.center_on_parent()