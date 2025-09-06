import os
import uuid
import shutil
from typing import Optional, Union, BinaryIO, Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager
import mimetypes
import asyncio
import logging
from enum import Enum

from fs import open_fs
from fs.base import FS
from fs.osfs import OSFS
from fs.memoryfs import MemoryFS
from fs.errors import FSError
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class StorageBackend(Enum):
    LOCAL = "local"
    MEMORY = "memory"


class StorageType(Enum):
    PUBLIC = "public"
    TEMP = "temp"
    TEMPLATES = "templates"


class StorageEngine:
    """
    Unified storage engine using PyFilesystem2 for all file operations.
    Provides a consistent interface for storing, reading, and managing files.
    """
    
    def __init__(
        self,
        base_path: str = "storage",
        backend: StorageBackend = StorageBackend.LOCAL,
        temp_cleanup_hours: int = 24,
        max_temp_size_mb: int = 100
    ):
        """Initialize the storage engine.
        
        Args:
            base_path: Base directory for storage
            backend: Storage backend type
            temp_cleanup_hours: Hours after which temp files are deleted
            max_temp_size_mb: Maximum temp directory size in MB
        """
        self.base_path = Path(base_path)
        self.backend = backend
        self.temp_cleanup_hours = temp_cleanup_hours
        self.max_temp_size_mb = max_temp_size_mb
        
        # Initialize filesystem backends
        self._fs_backends: Dict[StorageType, FS] = {}
        self._initialize_backends()
        
        # URL mappings for public files
        self.url_mappings = {
            "charts": "/storage/charts",
            "images": "/storage/images", 
            "documents": "/storage/documents",
            "pdfs": "/storage/pdfs"
        }
        
    def _initialize_backends(self):
        """Initialize filesystem backends for different storage types."""
        if self.backend == StorageBackend.LOCAL:
            # Ensure base directory exists
            self.base_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize local filesystems
            for storage_type in StorageType:
                storage_path = self.base_path / storage_type.value
                storage_path.mkdir(parents=True, exist_ok=True)
                self._fs_backends[storage_type] = OSFS(str(storage_path))
        
        elif self.backend == StorageBackend.MEMORY:
            # Initialize in-memory filesystems (useful for testing)
            for storage_type in StorageType:
                self._fs_backends[storage_type] = MemoryFS()
        
        # Create subdirectories in public storage
        public_fs = self._fs_backends[StorageType.PUBLIC]
        for subdir in ["charts", "images", "documents", "pdfs"]:
            public_fs.makedirs(subdir, recreate=True)
            
        # Create subdirectories in temp storage  
        temp_fs = self._fs_backends[StorageType.TEMP]
        for subdir in ["uploads", "processing", "cache"]:
            temp_fs.makedirs(subdir, recreate=True)

    def get_fs(self, storage_type: StorageType) -> FS:
        """Get filesystem for a specific storage type."""
        return self._fs_backends[storage_type]
    
    @contextmanager
    def temp_file(self, suffix: str = "", prefix: str = "temp_"):
        """Context manager for temporary files with automatic cleanup."""
        filename = f"{prefix}{uuid.uuid4().hex}{suffix}"
        temp_path = f"processing/{filename}"
        temp_fs = self.get_fs(StorageType.TEMP)
        
        try:
            yield temp_path, temp_fs
        finally:
            # Cleanup temp file
            try:
                if temp_fs.exists(temp_path):
                    temp_fs.remove(temp_path)
            except FSError as e:
                logger.warning(f"Failed to cleanup temp file {temp_path}: {e}")
    
    def store_upload(
        self, 
        file: UploadFile, 
        category: str, 
        custom_filename: Optional[str] = None,
        storage_type: StorageType = StorageType.PUBLIC
    ) -> Dict[str, Any]:
        """Store an uploaded file.
        
        Args:
            file: FastAPI UploadFile object
            category: Storage category (charts, images, etc.)
            custom_filename: Optional custom filename
            storage_type: Type of storage (public/temp)
            
        Returns:
            Dict with file info including URL
        """
        try:
            # Generate filename
            if custom_filename:
                filename = custom_filename
            else:
                ext = self._get_file_extension(file.filename, file.content_type)
                filename = f"{uuid.uuid4().hex}{ext}"
            
            # Determine storage path
            file_path = f"{category}/{filename}"
            
            # Store the file
            fs = self.get_fs(storage_type)
            with fs.open(file_path, 'wb') as f:
                content = file.file.read()
                f.write(content)
                file_size = len(content)
            
            # Generate URL for public files
            url = None
            if storage_type == StorageType.PUBLIC and category in self.url_mappings:
                url = f"{self.url_mappings[category]}/{filename}"
            
            return {
                "filename": filename,
                "path": file_path,
                "url": url,
                "size": file_size,
                "content_type": file.content_type,
                "stored_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error storing upload: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store file: {str(e)}")
    
    def store_bytes(
        self,
        data: bytes,
        category: str,
        filename: str,
        content_type: Optional[str] = None,
        storage_type: StorageType = StorageType.PUBLIC
    ) -> Dict[str, Any]:
        """Store binary data as a file.
        
        Args:
            data: Binary data to store
            category: Storage category
            filename: Filename to use
            content_type: MIME type
            storage_type: Type of storage
            
        Returns:
            Dict with file info including URL
        """
        try:
            file_path = f"{category}/{filename}"
            fs = self.get_fs(storage_type)
            
            with fs.open(file_path, 'wb') as f:
                f.write(data)
            
            # Generate URL for public files
            url = None
            if storage_type == StorageType.PUBLIC and category in self.url_mappings:
                url = f"{self.url_mappings[category]}/{filename}"
            
            # Detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
            
            return {
                "filename": filename,
                "path": file_path, 
                "url": url,
                "size": len(data),
                "content_type": content_type,
                "stored_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error storing bytes: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store data: {str(e)}")
    
    def read_file(self, path: str, storage_type: StorageType = StorageType.PUBLIC) -> bytes:
        """Read file contents as bytes."""
        try:
            fs = self.get_fs(storage_type)
            with fs.open(path, 'rb') as f:
                return f.read()
        except FSError as e:
            logger.error(f"Error reading file {path}: {e}")
            raise HTTPException(status_code=404, detail="File not found")
    
    def read_text(self, path: str, storage_type: StorageType = StorageType.TEMPLATES, encoding: str = 'utf-8') -> str:
        """Read file contents as text."""
        try:
            fs = self.get_fs(storage_type)
            with fs.open(path, 'r', encoding=encoding) as f:
                return f.read()
        except FSError as e:
            logger.error(f"Error reading text file {path}: {e}")
            raise HTTPException(status_code=404, detail="File not found")
    
    def exists(self, path: str, storage_type: StorageType = StorageType.PUBLIC) -> bool:
        """Check if a file exists."""
        fs = self.get_fs(storage_type)
        return fs.exists(path)
    
    def delete_file(self, path: str, storage_type: StorageType = StorageType.PUBLIC) -> bool:
        """Delete a file."""
        try:
            fs = self.get_fs(storage_type)
            if fs.exists(path):
                fs.remove(path)
                return True
            return False
        except FSError as e:
            logger.error(f"Error deleting file {path}: {e}")
            return False
    
    def list_files(
        self, 
        category: str, 
        storage_type: StorageType = StorageType.PUBLIC
    ) -> List[Dict[str, Any]]:
        """List files in a category."""
        try:
            fs = self.get_fs(storage_type)
            files = []
            
            if fs.exists(category):
                for file_info in fs.scandir(category):
                    if file_info.is_file:
                        # Get file details safely
                        details = fs.getinfo(f"{category}/{file_info.name}", namespaces=['details'])
                        files.append({
                            "name": file_info.name,
                            "path": f"{category}/{file_info.name}",
                            "size": details.size,
                            "modified": details.modified.isoformat() if details.modified else None
                        })
            
            return files
        except FSError as e:
            logger.error(f"Error listing files in {category}: {e}")
            return []
    
    def cleanup_temp_files(self) -> Dict[str, int]:
        """Clean up old temporary files."""
        try:
            temp_fs = self.get_fs(StorageType.TEMP)
            # Use timezone-aware cutoff matched to each file's modified tzinfo to avoid naive/aware comparisons
            base_cutoff = timedelta(hours=self.temp_cleanup_hours)
            
            deleted_count = 0
            total_size_freed = 0
            
            for subdir in ["uploads", "processing", "cache"]:
                if temp_fs.exists(subdir):
                    for file_info in temp_fs.scandir(subdir):
                        if file_info.is_file:
                            file_path = f"{subdir}/{file_info.name}"
                            try:
                                # Get file details safely  
                                details = temp_fs.getinfo(file_path, namespaces=['details'])
                                modified = details.modified
                                if modified:
                                    try:
                                        # Align cutoff tzinfo with modified timestamp tzinfo
                                        cutoff_time = datetime.now(tz=modified.tzinfo) - base_cutoff
                                        if modified < cutoff_time:
                                            total_size_freed += details.size
                                            temp_fs.remove(file_path)
                                            deleted_count += 1
                                    except Exception as tz_err:
                                        # Fallback: attempt naive comparison by dropping tzinfo
                                        try:
                                            naive_modified = modified.replace(tzinfo=None)
                                            naive_cutoff = datetime.now() - base_cutoff
                                            if naive_modified < naive_cutoff:
                                                total_size_freed += details.size
                                                temp_fs.remove(file_path)
                                                deleted_count += 1
                                        except Exception as e2:
                                            logger.warning(f"Failed to compare modified time for {file_path}: {e2}")
                            except FSError as e:
                                logger.warning(f"Failed to delete temp file {file_path}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} temp files, freed {total_size_freed} bytes")
            
            return {
                "deleted_files": deleted_count,
                "bytes_freed": total_size_freed
            }
            
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")
            return {"deleted_files": 0, "bytes_freed": 0}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        stats = {}
        
        for storage_type in StorageType:
            fs = self.get_fs(storage_type)
            type_stats = {"total_files": 0, "total_size": 0, "categories": {}}
            
            try:
                if storage_type == StorageType.PUBLIC:
                    categories = ["charts", "images", "documents", "pdfs"]
                elif storage_type == StorageType.TEMP:
                    categories = ["uploads", "processing", "cache"]
                else:
                    categories = ["prompts"] if fs.exists("prompts") else []
                
                for category in categories:
                    if fs.exists(category):
                        cat_files = 0
                        cat_size = 0
                        for file_info in fs.scandir(category):
                            if file_info.is_file:
                                try:
                                    details = fs.getinfo(f"{category}/{file_info.name}", namespaces=['details'])
                                    cat_files += 1
                                    cat_size += details.size
                                except FSError:
                                    # Skip files we can't read
                                    continue
                        
                        type_stats["categories"][category] = {
                            "files": cat_files,
                            "size": cat_size
                        }
                        type_stats["total_files"] += cat_files
                        type_stats["total_size"] += cat_size
                
            except FSError as e:
                logger.warning(f"Error getting stats for {storage_type.value}: {e}")
            
            stats[storage_type.value] = type_stats
        
        return stats
    
    def _get_file_extension(self, filename: Optional[str], content_type: Optional[str]) -> str:
        """Get appropriate file extension."""
        if filename and '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        
        if content_type:
            extension = mimetypes.guess_extension(content_type)
            if extension:
                return extension
        
        return ''
    
    async def async_cleanup_temp_files(self) -> Dict[str, int]:
        """Async version of temp file cleanup for background tasks."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.cleanup_temp_files)


# Global storage engine instance
storage_engine: Optional[StorageEngine] = None


def get_storage_engine() -> StorageEngine:
    """Get the global storage engine instance."""
    global storage_engine
    if storage_engine is None:
        from app.core.config import settings
        storage_engine = StorageEngine(
            base_path=settings.STORAGE_BASE_PATH,
            temp_cleanup_hours=settings.TEMP_FILE_CLEANUP_HOURS,
            max_temp_size_mb=settings.MAX_TEMP_FILE_SIZE_MB
        )
    return storage_engine


def init_storage_engine(config_settings) -> StorageEngine:
    """Initialize storage engine with configuration."""
    global storage_engine
    storage_engine = StorageEngine(
        base_path=config_settings.STORAGE_BASE_PATH,
        temp_cleanup_hours=config_settings.TEMP_FILE_CLEANUP_HOURS, 
        max_temp_size_mb=config_settings.MAX_TEMP_FILE_SIZE_MB
    )
    return storage_engine
