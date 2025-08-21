"""
Storage module for FrameTruth AI Forensic Tool.
Handles file storage, organization, and metadata management.
"""

import os
import shutil
import hashlib
import mimetypes
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from .db import get_connection


class StorageManager:
    """Manages file storage and organization for users."""
    
    def __init__(self, base_path: str = "evidence_store"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def get_user_root(self, username: str) -> Path:
        """
        Get the storage root directory for a specific user.
        
        Args:
            username: Username
            
        Returns:
            Path to user's storage directory
        """
        user_path = self.base_path / username
        user_path.mkdir(exist_ok=True)
        return user_path
    
    def get_file_path(self, username: str, filename: str) -> Path:
        """
        Get the full path for a file in a user's storage.
        
        Args:
            username: Username
            filename: Filename
            
        Returns:
            Full path to the file
        """
        return self.get_user_root(username) / filename
    
    def store_file(self, username: str, source_path: str, filename: Optional[str] = None) -> Tuple[bool, str, Dict]:
        """
        Store a file in a user's storage directory.
        
        Args:
            username: Username
            source_path: Path to source file
            filename: Optional custom filename
            
        Returns:
            Tuple of (success, message, file_info)
        """
        try:
            source_path = Path(source_path)
            if not source_path.exists():
                return False, "Source file does not exist", {}
            
            # Use original filename if not specified
            if not filename:
                filename = source_path.name
            
            # Ensure filename is safe
            filename = self._sanitize_filename(filename)
            
            # Get user storage path
            user_root = self.get_user_root(username)
            dest_path = user_root / filename
            
            # Handle filename conflicts
            counter = 1
            original_filename = filename
            while dest_path.exists():
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                dest_path = user_root / filename
                counter += 1
            
            # Copy file to storage
            shutil.copy2(source_path, dest_path)
            
            # Calculate file properties
            file_info = self._get_file_info(dest_path)
            
            return True, f"File stored successfully as {filename}", file_info
            
        except Exception as e:
            return False, f"Error storing file: {e}", {}
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        Get comprehensive information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        return self._get_file_info(Path(file_path))
    
    def _get_file_info(self, file_path: Path) -> Dict:
        """Internal method to get file information."""
        try:
            stat = file_path.stat()
            
            # Calculate SHA256 hash
            sha256_hash = self._calculate_sha256(file_path)
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            return {
                "filename": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "mime_type": mime_type or "application/octet-stream",
                "sha256": sha256_hash,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ""
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def list_user_files(self, username: str, include_hidden: bool = False) -> List[Dict]:
        """
        List all files in a user's storage directory.
        
        Args:
            username: Username
            include_hidden: Whether to include hidden files
            
        Returns:
            List of file information dictionaries
        """
        try:
            user_root = self.get_user_root(username)
            files = []
            
            for item in user_root.iterdir():
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                file_info = self._get_file_info(item)
                files.append(file_info)
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x.get('modified_at', 0), reverse=True)
            return files
            
        except Exception as e:
            print(f"Error listing user files: {e}")
            return []
    
    def delete_file(self, username: str, filename: str) -> Tuple[bool, str]:
        """
        Delete a file from a user's storage.
        
        Args:
            username: Username
            filename: Filename to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            file_path = self.get_file_path(username, filename)
            
            if not file_path.exists():
                return False, "File does not exist"
            
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                return False, "Path is neither file nor directory"
            
            return True, f"File {filename} deleted successfully"
            
        except Exception as e:
            return False, f"Error deleting file: {e}"
    
    def move_file(self, username: str, old_filename: str, new_filename: str) -> Tuple[bool, str]:
        """
        Move/rename a file within a user's storage.
        
        Args:
            username: Username
            old_filename: Current filename
            new_filename: New filename
            
        Returns:
            Tuple of (success, message)
        """
        try:
            old_path = self.get_file_path(username, old_filename)
            new_path = self.get_file_path(username, new_filename)
            
            if not old_path.exists():
                return False, "Source file does not exist"
            
            if new_path.exists():
                return False, "Destination file already exists"
            
            # Sanitize new filename
            new_filename = self._sanitize_filename(new_filename)
            new_path = self.get_file_path(username, new_filename)
            
            old_path.rename(new_path)
            return True, f"File moved from {old_filename} to {new_filename}"
            
        except Exception as e:
            return False, f"Error moving file: {e}"
    
    def copy_file(self, username: str, filename: str, new_filename: str) -> Tuple[bool, str]:
        """
        Copy a file within a user's storage.
        
        Args:
            username: Username
            filename: Source filename
            new_filename: New filename
            
        Returns:
            Tuple of (success, message)
        """
        try:
            source_path = self.get_file_path(username, filename)
            dest_path = self.get_file_path(username, new_filename)
            
            if not source_path.exists():
                return False, "Source file does not exist"
            
            if dest_path.exists():
                return False, "Destination file already exists"
            
            # Sanitize new filename
            new_filename = self._sanitize_filename(new_filename)
            dest_path = self.get_file_path(username, new_filename)
            
            shutil.copy2(source_path, dest_path)
            return True, f"File copied from {filename} to {new_filename}"
            
        except Exception as e:
            return False, f"Error copying file: {e}"
    
    def get_storage_stats(self, username: Optional[str] = None) -> Dict:
        """
        Get storage statistics.
        
        Args:
            username: Optional username to get stats for specific user
            
        Returns:
            Dictionary with storage statistics
        """
        try:
            if username:
                user_root = self.get_user_root(username)
                total_size = sum(
                    f.stat().st_size for f in user_root.rglob('*') if f.is_file()
                )
                file_count = sum(1 for f in user_root.rglob('*') if f.is_file())
                
                return {
                    "username": username,
                    "total_size": total_size,
                    "total_size_mb": total_size / (1024 * 1024),
                    "file_count": file_count,
                    "storage_path": str(user_root)
                }
            else:
                # Overall stats
                total_size = 0
                total_files = 0
                user_stats = {}
                
                for user_dir in self.base_path.iterdir():
                    if user_dir.is_dir():
                        user_size = sum(
                            f.stat().st_size for f in user_dir.rglob('*') if f.is_file()
                        )
                        user_files = sum(1 for f in user_dir.rglob('*') if f.is_file())
                        
                        total_size += user_size
                        total_files += user_files
                        
                        user_stats[user_dir.name] = {
                            "size": user_size,
                            "size_mb": user_size / (1024 * 1024),
                            "files": user_files
                        }
                
                return {
                    "total_size": total_size,
                    "total_size_mb": total_size / (1024 * 1024),
                    "total_files": total_files,
                    "users": user_stats,
                    "base_path": str(self.base_path)
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def cleanup_orphaned_files(self, username: str) -> Tuple[int, List[str]]:
        """
        Clean up files that exist in storage but not in database.
        
        Args:
            username: Username
            
        Returns:
            Tuple of (count, list of cleaned files)
        """
        try:
            from .db import get_connection
            
            # Get files from database
            with get_connection() as conn:
                cursor = conn.cursor()
                db_files = cursor.execute("""
                    SELECT storage_path FROM files 
                    WHERE owner_id = (SELECT id FROM users WHERE username = ?)
                """, (username,)).fetchall()
            
            db_paths = {row["storage_path"] for row in db_files}
            
            # Get files from storage
            user_root = self.get_user_root(username)
            storage_files = [str(f) for f in user_root.rglob('*') if f.is_file()]
            
            # Find orphaned files
            orphaned = [f for f in storage_files if f not in db_paths]
            
            # Clean up orphaned files
            cleaned = []
            for orphaned_file in orphaned:
                try:
                    os.remove(orphaned_file)
                    cleaned.append(orphaned_file)
                except Exception as e:
                    print(f"Error removing orphaned file {orphaned_file}: {e}")
            
            return len(cleaned), cleaned
            
        except Exception as e:
            print(f"Error cleaning up orphaned files: {e}")
            return 0, []


# Global storage manager instance
storage_manager = StorageManager()


# Convenience functions
def get_user_root(username: str) -> Path:
    """Get the storage root directory for a specific user."""
    return storage_manager.get_user_root(username)


def store_file(username: str, source_path: str, filename: Optional[str] = None) -> Tuple[bool, str, Dict]:
    """Store a file in a user's storage directory."""
    return storage_manager.store_file(username, source_path, filename)


def get_file_info(file_path: str) -> Dict:
    """Get comprehensive information about a file."""
    return storage_manager.get_file_info(file_path)


def list_user_files(username: str, include_hidden: bool = False) -> List[Dict]:
    """List all files in a user's storage directory."""
    return storage_manager.list_user_files(username, include_hidden)


def delete_file(username: str, filename: str) -> Tuple[bool, str]:
    """Delete a file from a user's storage."""
    return storage_manager.delete_file(username, filename)


def move_file(username: str, old_filename: str, new_filename: str) -> Tuple[bool, str]:
    """Move/rename a file within a user's storage."""
    return storage_manager.move_file(username, old_filename, new_filename)


def copy_file(username: str, filename: str, new_filename: str) -> Tuple[bool, str]:
    """Copy a file within a user's storage."""
    return storage_manager.copy_file(username, filename, new_filename)


def get_storage_stats(username: Optional[str] = None) -> Dict:
    """Get storage statistics."""
    return storage_manager.get_storage_stats(username)


def cleanup_orphaned_files(username: str) -> Tuple[int, List[str]]:
    """Clean up files that exist in storage but not in database."""
    return storage_manager.cleanup_orphaned_files(username)


if __name__ == "__main__":
    # Test storage functionality
    print("Testing storage functionality...")
    
    # Test user root creation
    user_root = get_user_root("testuser")
    print(f"User root: {user_root}")
    
    # Test file storage (create a test file first)
    test_file = Path("test_file.txt")
    test_file.write_text("This is a test file for storage testing.")
    
    success, message, file_info = store_file("testuser", str(test_file))
    print(f"Storage test: {success}, {message}")
    if success:
        print(f"File info: {file_info}")
    
    # Test listing files
    files = list_user_files("testuser")
    print(f"User files: {len(files)}")
    
    # Test storage stats
    stats = get_storage_stats("testuser")
    print(f"Storage stats: {stats}")
    
    # Cleanup test file
    test_file.unlink()
    print("Storage test completed")
