# -*- coding: utf-8 -*-
"""
Gemini TTS Add-on - Refactored Version
======================================

Professional Text-to-Speech integration using Google's Gemini API.
Refactored architecture with dependency injection, type safety, and structured logging.

Author: Jesus Heredia Ramirez
License: MIT
"""

import os
from anki.hooks import addHook
from aqt import mw, gui_hooks
from aqt.qt import QAction

# ============================================================================
# MODULE INFORMATION
# ============================================================================

__version__ = "2.0.0"
__author__ = "Jesus Heredia Ramirez"
__description__ = "Professional TTS for Anki using Google Gemini API with refactored architecture"

# ============================================================================
# GLOBAL STATE MANAGEMENT
# ============================================================================

# Profile-aware container storage
_profile_containers = {}

def get_container_for_profile(profile_name=None):
    """Get container instance for specific profile"""
    if profile_name is None:
        profile_name = getattr(mw.pm, 'name', 'default') if mw and mw.pm else 'default'
    
    return _profile_containers.get(profile_name)

def set_container_for_profile(container, profile_name=None):
    """Set container instance for specific profile"""
    if profile_name is None:
        profile_name = getattr(mw.pm, 'name', 'default') if mw and mw.pm else 'default'
    
    _profile_containers[profile_name] = container

def cleanup_profile_container(profile_name=None):
    """Clean up container for specific profile"""
    if profile_name is None:
        profile_name = getattr(mw.pm, 'name', 'default') if mw and mw.pm else 'default'
    
    if profile_name in _profile_containers:
        container = _profile_containers[profile_name]
        try:
            container.cleanup()
        except Exception as e:
            print(f"Gemini TTS: Container cleanup error - {e}")
        
        del _profile_containers[profile_name]
        print(f"Gemini TTS: Container cleaned up for profile '{profile_name}'")

# ============================================================================
# INITIALIZATION FUNCTIONS
# ============================================================================

def initialize_addon():
    """Initialize addon with dependency injection architecture"""
    profile_name = getattr(mw.pm, 'name', 'default') if mw and mw.pm else 'default'
    
    try:
        # Import core components
        from .core.container import TTSContainer
        from .core.logging_config import setup_logging
        from .core import check_dependencies
        
        # Set up logging first
        logger = setup_logging("INFO", "gemini_tts")
        logger.info("Initializing Gemini TTS", version=__version__, profile=profile_name)
        
        # Check dependencies
        deps = check_dependencies()
        missing_deps = [dep for dep, available in deps.items() if not available]
        if missing_deps:
            logger.warning("Missing dependencies", missing=missing_deps)
        
        # Create container for this profile
        container = TTSContainer(anki_main_window=mw)
        set_container_for_profile(container, profile_name)
        
        # Validate container health
        health = container.health_check()
        critical_issues = [service for service, healthy in health.items() 
                          if not healthy and service in ['anki_main_window', 'anki_collection']]
        
        if critical_issues:
            logger.error("Critical initialization issues", issues=critical_issues)
            return False
        
        logger.info("Gemini TTS initialized successfully", 
                   profile=profile_name, 
                   services_available=sum(1 for healthy in health.values() if healthy))
        
        return True
        
    except ImportError as e:
        print(f"Gemini TTS: Import error during initialization - {e}")
        return False
    except Exception as e:
        print(f"Gemini TTS: Initialization error for profile '{profile_name}' - {e}")
        return False

def cleanup_addon():
    """Clean up addon resources"""
    try:
        profile_name = getattr(mw.pm, 'name', 'default') if mw and mw.pm else 'default'
        cleanup_profile_container(profile_name)
    except Exception as e:
        print(f"Gemini TTS: Cleanup error - {e}")

def cleanup_all_containers():
    """Clean up all profile containers"""
    global _profile_containers
    
    try:
        for profile_name in list(_profile_containers.keys()):
            cleanup_profile_container(profile_name)
        
        _profile_containers.clear()
        print("Gemini TTS: All containers cleaned up")
        
    except Exception as e:
        print(f"Gemini TTS: Global cleanup error - {e}")

# ============================================================================
# UI INTEGRATION FUNCTIONS
# ============================================================================

def setup_editor_button(buttons, editor):
    """Add TTS button to editor toolbar with service injection"""
    try:
        container = get_container_for_profile()
        if not container:
            print("Gemini TTS: No container available for editor integration")
            return buttons
        
        # Import UI integration
        from .ui.editor_integration import setup_editor_button as ui_setup
        return ui_setup(buttons, editor)
        
    except ImportError as e:
        print(f"Gemini TTS: UI integration import error - {e}")
        return buttons
    except Exception as e:
        print(f"Gemini TTS: Editor button setup error - {e}")
        return buttons

def show_config():
    """Show configuration dialog with service injection"""
    try:
        container = get_container_for_profile()
        if not container:
            from aqt.utils import showInfo
            showInfo("Gemini TTS not properly initialized. Try restarting Anki.")
            return
        
        # Import and show config dialog
        from .ui.config_dialog import show_config_dialog
        show_config_dialog()
        
    except ImportError as e:
        from aqt.utils import showInfo
        showInfo(f"Configuration error: Import failed - {e}")
    except Exception as e:
        from aqt.utils import showInfo
        showInfo(f"Configuration error: {e}")

def show_test_dialog():
    """Show testing dialog"""
    try:
        container = get_container_for_profile()
        if not container:
            from aqt.utils import showInfo
            showInfo("Gemini TTS not properly initialized.")
            return
        
        from .ui.dialogs.test_dialog import show_test_dialog as ui_show_test
        ui_show_test()
        
    except ImportError as e:
        from aqt.utils import showInfo
        showInfo(f"Test dialog error: Import failed - {e}")
    except Exception as e:
        from aqt.utils import showInfo
        showInfo(f"Test dialog error: {e}")

# ============================================================================
# MIGRATION SUPPORT
# ============================================================================

def migrate_legacy_config():
    """Migrate from monolithic configuration"""
    try:
        # Check for legacy config format
        if mw and mw.col:
            try:
                legacy_config = mw.col.get_config("gemini_tts", {})
            except AttributeError:
                legacy_config = mw.col.conf.get("gemini_tts", {})
            
            if legacy_config and "model" not in legacy_config:
                # Looks like legacy format, migrate
                from .core.models import TTSConfig
                from .services.config_service import ConfigurationService
                
                container = get_container_for_profile()
                if container and container.get_config_service():
                    config_service = container.get_config_service()
                    migrated = config_service.migrate_legacy_config(legacy_config)
                    
                    # Save migrated config
                    container.update_config(migrated)
                    print("Gemini TTS: Configuration migrated to new format")
                    
    except Exception as e:
        print(f"Gemini TTS: Config migration error - {e}")

# ============================================================================
# SERVICE ACCESS HELPERS
# ============================================================================

def get_audio_generator():
    """Get audio generator service for current profile"""
    container = get_container_for_profile()
    return container.get_audio_generator() if container else None

def get_config_service():
    """Get configuration service for current profile"""
    container = get_container_for_profile()
    return container.get_config_service() if container else None

def get_cache_manager():
    """Get cache manager service for current profile"""
    container = get_container_for_profile()
    return container.get_cache_manager() if container else None

# ============================================================================
# ANKI HOOKS REGISTRATION
# ============================================================================

def register_hooks():
    """Register all Anki hooks"""
    try:
        # Profile initialization
        try:
            gui_hooks.profile_did_open.append(initialize_addon)
            gui_hooks.profile_did_open.append(migrate_legacy_config)
        except AttributeError:
            # Fallback for older Anki versions
            addHook("profileLoaded", initialize_addon)
            addHook("profileLoaded", migrate_legacy_config)
        
        # Profile cleanup
        addHook("unloadProfile", cleanup_addon)
        
        # Application shutdown
        try:
            gui_hooks.main_window_will_close.append(cleanup_all_containers)
        except AttributeError:
            addHook("atexit", cleanup_all_containers)
        
        # Editor integration
        addHook("setupEditorButtons", setup_editor_button)
        
        print("Gemini TTS: Hooks registered successfully")
        
    except Exception as e:
        print(f"Gemini TTS: Hook registration error - {e}")

# ============================================================================
# MENU INTEGRATION
# ============================================================================

def setup_menu():
    """Setup Tools menu integration"""
    try:
        if not mw:
            return
        
        # Configuration menu item
        config_action = QAction("Gemini TTS Configuration", mw)
        config_action.triggered.connect(show_config)
        mw.form.menuTools.addAction(config_action)
        
        # Test dialog menu item
        test_action = QAction("Gemini TTS Test", mw)
        test_action.triggered.connect(show_test_dialog)
        mw.form.menuTools.addAction(test_action)
        
        print("Gemini TTS: Menu items added")
        
    except Exception as e:
        print(f"Gemini TTS: Menu setup error - {e}")

# ============================================================================
# DIAGNOSTIC FUNCTIONS
# ============================================================================

def get_addon_status():
    """Get comprehensive addon status for debugging"""
    try:
        profile_name = getattr(mw.pm, 'name', 'default') if mw and mw.pm else 'default'
        container = get_container_for_profile()
        
        status = {
            "version": __version__,
            "profile": profile_name,
            "container_available": container is not None,
            "profile_containers": list(_profile_containers.keys())
        }
        
        if container:
            status["health"] = container.health_check()
            status["services"] = container.get_service_info()
        
        # Check core dependencies
        try:
            from .core import check_dependencies
            status["dependencies"] = check_dependencies()
        except ImportError:
            status["dependencies"] = {"error": "Core module not available"}
        
        return status
        
    except Exception as e:
        return {"error": str(e)}

def run_diagnostics():
    """Run comprehensive diagnostics"""
    status = get_addon_status()
    
    print("=== Gemini TTS Diagnostic Report ===")
    print(f"Version: {status.get('version', 'Unknown')}")
    print(f"Profile: {status.get('profile', 'Unknown')}")
    print(f"Container Available: {status.get('container_available', False)}")
    
    if "health" in status:
        print("\nService Health:")
        for service, healthy in status["health"].items():
            print(f"  {service}: {'✓' if healthy else '✗'}")
    
    if "dependencies" in status:
        print("\nDependencies:")
        deps = status["dependencies"]
        if isinstance(deps, dict) and "error" not in deps:
            for dep, available in deps.items():
                print(f"  {dep}: {'✓' if available else '✗'}")
        else:
            print(f"  Error: {deps}")
    
    print("=== End Diagnostic Report ===")

# ============================================================================
# ADDON ENTRY POINT
# ============================================================================

def main():
    """Main addon entry point"""
    try:
        print(f"Gemini TTS v{__version__} loading...")
        
        # Register hooks
        register_hooks()
        
        # Setup menu (will run when Anki is ready)
        if mw:
            setup_menu()
        else:
            # Defer menu setup until Anki is ready
            try:
                gui_hooks.main_window_did_init.append(setup_menu)
            except AttributeError:
                addHook("atexit", lambda: None)  # Placeholder for older versions
        
        print(f"Gemini TTS v{__version__} loaded successfully")
        
    except Exception as e:
        print(f"Gemini TTS: Main initialization error - {e}")

# ============================================================================
# AUTO-INITIALIZATION
# ============================================================================

# Initialize when module is imported
main()

# ============================================================================
# PUBLIC API FOR BACKWARD COMPATIBILITY
# ============================================================================

def get_tts_instance():
    """Legacy API: Get TTS instance for current profile"""
    audio_gen = get_audio_generator()
    return audio_gen if audio_gen else None

def get_current_config():
    """Legacy API: Get current configuration"""
    container = get_container_for_profile()
    return container.get_config() if container else None

# Export public interface
__all__ = [
    '__version__',
    '__author__',
    '__description__',
    'get_audio_generator',
    'get_config_service', 
    'get_cache_manager',
    'get_addon_status',
    'run_diagnostics',
    'get_tts_instance',  # Legacy
    'get_current_config'  # Legacy
]