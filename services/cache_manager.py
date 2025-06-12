# -*- coding: utf-8 -*-
"""
Cache Management Service
=======================

Handles audio file caching, metadata, and cleanup operations.
"""

import os
import json
import time
import tempfile
import hashlib
from typing import Optional, List, Dict, Any

from ..core.models import TTSConfig, CacheMetadata, CacheFileInfo, Result
from ..core.constants import CacheConstants, FileConstants, AudioConstants
from ..core.exceptions import *
from ..core.logging_config import TTSLogger, LoggedOperation

class CacheManager:
    """Service for managing audio cache operations"""
    
    def __init__(self, cache_dir: str, config: TTSConfig, logger: Optional[TTSLogger] = None):
        self.cache_dir = cache_dir
        self.config = config
        self.logger = logger or TTSLogger("cache_manager")
        
        self._metadata: Optional[CacheMetadata] = None
        self._ensure_cache_directory()
    
    def _ensure_cache_directory(self):
        """Ensure cache directory exists and is secure"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Verify directory is within expected bounds
            real_cache_dir = os.path.realpath(self.cache_dir)
            if not real_cache_dir.startswith(os.path.realpath(os.path.dirname(self.cache_dir))):
                raise PathSecurityException("Cache directory outside allowed path", real_cache_dir)
                
        except OSError as e:
            raise CacheException(f"Cannot create cache directory: {e}", critical=True)
    
    @property
    def metadata_file(self) -> str:
        """Get metadata file path"""
        return os.path.join(self.cache_dir, CacheConstants.METADATA_FILENAME)
    
    def get_metadata(self) -> CacheMetadata:
        """Load or create cache metadata"""
        if self._metadata is None:
            self._metadata = self._load_metadata()
        return self._metadata
    
    def _load_metadata(self) -> CacheMetadata:
        """Load metadata from file"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    
                # Convert to structured metadata
                metadata = CacheMetadata(version=data.get("version", "1.0"))
                
                for filename, file_data in data.get("files", {}).items():
                    metadata.files[filename] = CacheFileInfo(
                        created=file_data.get("created", time.time()),
                        accessed=file_data.get("accessed", time.time()),
                        version=file_data.get("version", "1.0"),
                        cache_key=file_data.get("cache_key", ""),
                        file_size=file_data.get("file_size", 0)
                    )
                
                self.logger.debug("Metadata loaded", file_count=len(metadata.files))
                return metadata
            else:
                self.logger.debug("Creating new metadata")
                return CacheMetadata()
                
        except Exception as e:
            self.logger.warning("Metadata load failed, creating new", exception=e)
            return CacheMetadata()
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            metadata = self.get_metadata()
            
            # Convert to serializable format
            data = {
                "version": metadata.version,
                "files": {}
            }
            
            for filename, file_info in metadata.files.items():
                data["files"][filename] = {
                    "created": file_info.created,
                    "accessed": file_info.accessed,
                    "version": file_info.version,
                    "cache_key": file_info.cache_key,
                    "file_size": file_info.file_size
                }
            
            # Atomic write using temp file
            temp_file = f"{self.metadata_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            os.replace(temp_file, self.metadata_file)
            self.logger.debug("Metadata saved", file_count=len(metadata.files))
            
        except Exception as e:
            self.logger.error("Metadata save failed", exception=e)
            raise CacheWriteException(f"Cannot save metadata: {e}")
    
    def get_cached_file(self, cache_key: str) -> Optional[str]:
        """Get cached audio file by key"""
        
        with LoggedOperation(self.logger, "cache_lookup", cache_key=cache_key[:8]):
            
            try:
                metadata = self.get_metadata()
                
                # Search for file with matching cache key
                for filename, file_info in metadata.files.items():
                    if file_info.cache_key == cache_key:
                        file_path = os.path.join(self.cache_dir, filename)
                        
                        # Verify file exists
                        if os.path.exists(file_path):
                            # Update access time
                            metadata.update_access(filename)
                            self._save_metadata()
                            
                            self.logger.log_cache_operation("hit", cache_key=cache_key)
                            return filename
                        else:
                            # File missing, remove from metadata
                            del metadata.files[filename]
                            self._save_metadata()
                            self.logger.warning("Cache file missing", filename=filename)
                
                self.logger.log_cache_operation("miss", cache_key=cache_key)
                return None
                
            except Exception as e:
                self.logger.error("Cache lookup failed", exception=e, cache_key=cache_key)
                return None
    
    def save_audio(self, cache_key: str, audio_data: bytes) -> str:
        """Save audio data to cache"""
        
        with LoggedOperation(self.logger, "cache_save", 
                           cache_key=cache_key[:8], 
                           data_size=len(audio_data)):
            
            # Generate unique filename
            timestamp = int(time.time())
            filename = f"gemini_tts_{cache_key[:8]}_{timestamp}.wav"
            file_path = os.path.join(self.cache_dir, filename)
            
            # Validate filename security
            self._validate_filename(filename)
            
            try:
                # Write audio data atomically
                temp_file = os.path.join(self.cache_dir, f".tmp_{filename}")
                
                with open(temp_file, 'wb') as f:
                    f.write(audio_data)
                
                # Atomic move
                os.replace(temp_file, file_path)
                
                # Update metadata
                metadata = self.get_metadata()
                metadata.add_file(filename, cache_key, len(audio_data))
                self._save_metadata()
                
                self.logger.log_cache_operation("save", cache_key=cache_key, 
                                              filename=filename, file_size=len(audio_data))
                
                return filename
                
            except Exception as e:
                # Cleanup temp file if it exists
                temp_file = os.path.join(self.cache_dir, f".tmp_{filename}")
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except OSError:
                        pass
                
                self.logger.error("Cache save failed", exception=e, cache_key=cache_key)
                raise CacheWriteException(f"Cannot save audio file: {e}")
    
    def _validate_filename(self, filename: str):
        """Validate filename security"""
        if len(filename) > FileConstants.MAX_FILENAME_LENGTH:
            raise SecurityException(f"Filename too long: {len(filename)}")
        
        for char in FileConstants.FORBIDDEN_CHARS:
            if char in filename:
                raise SecurityException(f"Forbidden character in filename: {char}")
        
        if filename.startswith('.') and not filename.startswith('.cache_tmp_'):
            raise SecurityException(f"Invalid filename pattern: {filename}")
    
    def cleanup_expired_files(self) -> int:
        """Remove expired cache files"""
        
        with LoggedOperation(self.logger, "cache_cleanup", max_age=self.config.cache_days):
            
            try:
                metadata = self.get_metadata()
                expired_files = metadata.get_expired_files(self.config.cache_days)
                
                removed_count = 0
                for filename in expired_files:
                    try:
                        file_path = os.path.join(self.cache_dir, filename)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        
                        # Remove from metadata
                        del metadata.files[filename]
                        removed_count += 1
                        
                        self.logger.debug("Expired file removed", filename=filename)
                        
                    except Exception as e:
                        self.logger.warning("Failed to remove expired file", 
                                          filename=filename, exception=e)
                
                # Save updated metadata
                if removed_count > 0:
                    self._save_metadata()
                
                self.logger.info("Cache cleanup completed", removed_count=removed_count)
                return removed_count
                
            except Exception as e:
                self.logger.error("Cache cleanup failed", exception=e)
                return 0
    
    def cleanup_temp_files(self) -> int:
        """Remove abandoned temporary files"""
        
        with LoggedOperation(self.logger, "temp_cleanup"):
            
            try:
                removed_count = 0
                current_time = time.time()
                cleanup_age = CacheConstants.TEMP_FILE_CLEANUP_HOURS * 3600
                
                for filename in os.listdir(self.cache_dir):
                    if filename.startswith(CacheConstants.TEMP_FILE_PREFIX):
                        file_path = os.path.join(self.cache_dir, filename)
                        
                        try:
                            file_age = current_time - os.path.getctime(file_path)
                            if file_age > cleanup_age:
                                os.remove(file_path)
                                removed_count += 1
                                self.logger.debug("Temp file removed", filename=filename)
                        except Exception as e:
                            self.logger.warning("Failed to remove temp file", 
                                              filename=filename, exception=e)
                
                self.logger.info("Temp cleanup completed", removed_count=removed_count)
                return removed_count
                
            except Exception as e:
                self.logger.error("Temp cleanup failed", exception=e)
                return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        
        try:
            metadata = self.get_metadata()
            total_size = 0
            oldest_file = None
            newest_file = None
            
            for filename, file_info in metadata.files.items():
                total_size += file_info.file_size
                
                if oldest_file is None or file_info.created < oldest_file:
                    oldest_file = file_info.created
                
                if newest_file is None or file_info.created > newest_file:
                    newest_file = file_info.created
            
            return {
                "file_count": len(metadata.files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "oldest_file_age_days": round((time.time() - oldest_file) / (24 * 3600), 1) if oldest_file else 0,
                "newest_file_age_days": round((time.time() - newest_file) / (24 * 3600), 1) if newest_file else 0,
                "cache_dir": self.cache_dir,
                "metadata_version": metadata.version
            }
            
        except Exception as e:
            self.logger.error("Cache stats failed", exception=e)
            return {"error": str(e)}
    
    def clear_cache(self) -> Result:
        """Clear all cache files"""
        
        with LoggedOperation(self.logger, "cache_clear"):
            
            try:
                removed_count = 0
                
                # Remove all cached files
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith(CacheConstants.CACHE_AUDIO_EXT):
                        file_path = os.path.join(self.cache_dir, filename)
                        try:
                            os.remove(file_path)
                            removed_count += 1
                        except Exception as e:
                            self.logger.warning("Failed to remove cache file", 
                                              filename=filename, exception=e)
                
                # Reset metadata
                self._metadata = CacheMetadata()
                self._save_metadata()
                
                self.logger.info("Cache cleared", removed_count=removed_count)
                return Result.success_result(f"Cleared {removed_count} files")
                
            except Exception as e:
                self.logger.error("Cache clear failed", exception=e)
                return Result.error_result(f"Cache clear failed: {e}")
    
    def validate_cache_integrity(self) -> Result:
        """Validate cache file integrity"""
        
        with LoggedOperation(self.logger, "cache_validation"):
            
            try:
                metadata = self.get_metadata()
                issues = []
                
                # Check metadata consistency
                for filename, file_info in metadata.files.items():
                    file_path = os.path.join(self.cache_dir, filename)
                    
                    if not os.path.exists(file_path):
                        issues.append(f"Missing file: {filename}")
                        continue
                    
                    # Check file size
                    actual_size = os.path.getsize(file_path)
                    if file_info.file_size > 0 and actual_size != file_info.file_size:
                        issues.append(f"Size mismatch: {filename} ({actual_size} vs {file_info.file_size})")
                    
                    # Basic audio validation
                    if actual_size < AudioConstants.MIN_AUDIO_SIZE:
                        issues.append(f"Audio too small: {filename} ({actual_size} bytes)")
                
                # Check for orphaned files
                for filename in os.listdir(self.cache_dir):
                    if (filename.endswith(CacheConstants.CACHE_AUDIO_EXT) and 
                        not filename.startswith('.') and
                        filename not in metadata.files):
                        issues.append(f"Orphaned file: {filename}")
                
                if issues:
                    self.logger.warning("Cache integrity issues found", issue_count=len(issues))
                    return Result.success_result({"issues": issues, "status": "issues_found"})
                else:
                    self.logger.info("Cache integrity validated", file_count=len(metadata.files))
                    return Result.success_result({"status": "valid", "file_count": len(metadata.files)})
                
            except Exception as e:
                self.logger.error("Cache validation failed", exception=e)
                return Result.error_result(f"Validation failed: {e}")
    
    def repair_cache(self) -> Result:
        """Repair cache inconsistencies"""
        
        with LoggedOperation(self.logger, "cache_repair"):
            
            try:
                validation_result = self.validate_cache_integrity()
                if not validation_result.success:
                    return validation_result
                
                if validation_result.data.get("status") == "valid":
                    return Result.success_result("No repairs needed")
                
                issues = validation_result.data.get("issues", [])
                repairs = []
                
                metadata = self.get_metadata()
                
                # Fix missing files
                files_to_remove = []
                for issue in issues:
                    if issue.startswith("Missing file:"):
                        filename = issue.split(": ")[1]
                        files_to_remove.append(filename)
                        repairs.append(f"Removed metadata for missing file: {filename}")
                
                for filename in files_to_remove:
                    if filename in metadata.files:
                        del metadata.files[filename]
                
                # Save repaired metadata
                if repairs:
                    self._save_metadata()
                
                self.logger.info("Cache repair completed", repair_count=len(repairs))
                return Result.success_result({"repairs": repairs, "repair_count": len(repairs)})
                
            except Exception as e:
                self.logger.error("Cache repair failed", exception=e)
                return Result.error_result(f"Repair failed: {e}")
    
    def get_file_path(self, filename: str) -> str:
        """Get full path for cache filename"""
        return os.path.join(self.cache_dir, filename)