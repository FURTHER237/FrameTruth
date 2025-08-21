"""
File Manager module for FrameTruth AI Forensic Tool.
Integrates storage, ACL, and audit logging for unified file operations.
"""

import os
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from .db import get_connection
from .storage import store_file, get_file_info, list_user_files, delete_file, move_file, copy_file
from .acl import can_access, grant_permission, revoke_permission, get_file_permissions
from .audit import log_access, log_user_action


class FileManager:
    """Manages file operations with integrated access control and auditing."""
    
    def __init__(self):
        pass
    
    def upload_file(self, username: str, source_path: str, filename: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> Tuple[bool, str, Optional[int]]:
        """
        Upload a file to user storage and register it in the database.
        
        Args:
            username: Username of the file owner
            source_path: Path to the source file
            filename: Optional custom filename
            metadata: Optional additional metadata
            
        Returns:
            Tuple of (success, message, file_id)
        """
        try:
            # Store file in user storage
            success, message, file_info = store_file(username, source_path, filename)
            if not success:
                return False, message, None
            
            # Get user ID
            from .auth import get_user_by_username
            user = get_user_by_username(username)
            if not user:
                return False, "User not found", None
            
            # Register file in database
            file_id = self._register_file_in_db(user["id"], file_info, metadata)
            if not file_id:
                return False, "Failed to register file in database", None
            
            # Log the upload
            log_access(user["id"], file_id, "UPLOAD", metadata=metadata)
            log_user_action(user["id"], "FILE_UPLOAD", "file", file_id, file_info)
            
            return True, f"File uploaded successfully. File ID: {file_id}", file_id
            
        except Exception as e:
            return False, f"Error uploading file: {e}", None
    
    def download_file(self, username: str, file_id: int, target_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Download a file from user storage.
        
        Args:
            username: Username requesting the download
            file_id: ID of the file to download
            target_path: Optional target path for download
            
        Returns:
            Tuple of (success, message, file_path)
        """
        try:
            # Get user ID
            from .auth import get_user_by_username
            user = get_user_by_username(username)
            if not user:
                return False, "User not found", None
            
            # Check access permissions
            if not can_access(user["id"], file_id, "read"):
                return False, "Access denied", None
            
            # Get file information
            file_info = self._get_file_by_id(file_id)
            if not file_info:
                return False, "File not found", None
            
            # Determine target path
            if not target_path:
                target_path = os.path.join(os.getcwd(), file_info["filename"])
            
            # Copy file to target location
            import shutil
            shutil.copy2(file_info["storage_path"], target_path)
            
            # Log the download
            log_access(user["id"], file_id, "DOWNLOAD", metadata={"target_path": target_path})
            
            return True, f"File downloaded to {target_path}", target_path
            
        except Exception as e:
            return False, f"Error downloading file: {e}", None
    
    def view_file(self, username: str, file_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """
        View file information and metadata.
        
        Args:
            username: Username requesting to view the file
            file_id: ID of the file to view
            
        Returns:
            Tuple of (success, message, file_data)
        """
        try:
            # Get user ID
            from .auth import get_user_by_username
            user = get_user_by_username(username)
            if not user:
                return False, "User not found", None
            
            # Check access permissions
            if not can_access(user["id"], file_id, "read"):
                return False, "Access denied", None
            
            # Get file information
            file_info = self._get_file_by_id(file_id)
            if not file_info:
                return False, "File not found", None
            
            # Get detections for the file
            detections = self._get_file_detections(file_id)
            
            # Get file permissions
            permissions = get_file_permissions(file_id)
            
            # Prepare file data
            file_data = {
                "file_info": file_info,
                "detections": detections,
                "permissions": permissions,
                "access_time": time.time()
            }
            
            # Log the view
            log_access(user["id"], file_id, "VIEW", metadata={"view_type": "metadata"})
            
            return True, "File information retrieved successfully", file_data
            
        except Exception as e:
            return False, f"Error viewing file: {e}", None
    
    def share_file(self, owner_username: str, file_id: int, grantee_username: str,
                   permission: str = "read", expires_at: Optional[float] = None) -> Tuple[bool, str]:
        """
        Share a file with another user.
        
        Args:
            owner_username: Username of the file owner
            file_id: ID of the file to share
            grantee_username: Username to grant access to
            permission: Permission level (read, write, admin)
            expires_at: Optional expiration timestamp
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get user IDs
            from .auth import get_user_by_username
            owner = get_user_by_username(owner_username)
            grantee = get_user_by_username(grantee_username)
            
            if not owner:
                return False, "Owner not found"
            if not grantee:
                return False, "Grantee not found"
            
            # Grant permission
            success, message = grant_permission(owner["id"], file_id, grantee["id"], permission, expires_at)
            if not success:
                return False, message
            
            # Log the sharing action
            log_user_action(owner["id"], "FILE_SHARE", "file", file_id, {
                "grantee_username": grantee_username,
                "permission": permission,
                "expires_at": expires_at
            })
            
            return True, f"File shared successfully with {grantee_username}"
            
        except Exception as e:
            return False, f"Error sharing file: {e}"
    
    def revoke_access(self, owner_username: str, file_id: int, grantee_username: str,
                     permission: str = "read") -> Tuple[bool, str]:
        """
        Revoke access to a file from another user.
        
        Args:
            owner_username: Username of the file owner
            file_id: ID of the file
            grantee_username: Username to revoke access from
            permission: Permission level to revoke
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get user IDs
            from .auth import get_user_by_username
            owner = get_user_by_username(owner_username)
            grantee = get_user_by_username(grantee_username)
            
            if not owner:
                return False, "Owner not found"
            if not grantee:
                return False, "Grantee not found"
            
            # Revoke permission
            success, message = revoke_permission(owner["id"], file_id, grantee["id"], permission)
            if not success:
                return False, message
            
            # Log the revocation
            log_user_action(owner["id"], "FILE_REVOKE", "file", file_id, {
                "grantee_username": grantee_username,
                "permission": permission
            })
            
            return True, f"Access revoked successfully from {grantee_username}"
            
        except Exception as e:
            return False, f"Error revoking access: {e}"
    
    def delete_file(self, username: str, file_id: int) -> Tuple[bool, str]:
        """
        Delete a file from storage and database.
        
        Args:
            username: Username requesting deletion
            file_id: ID of the file to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get user ID
            from .auth import get_user_by_username
            user = get_user_by_username(username)
            if not user:
                return False, "User not found"
            
            # Check if user owns the file or has admin rights
            if not can_access(user["id"], file_id, "admin"):
                return False, "Insufficient permissions to delete file"
            
            # Get file information
            file_info = self._get_file_by_id(file_id)
            if not file_info:
                return False, "File not found"
            
            # Delete from storage
            success, message = delete_file(username, file_info["filename"])
            if not success:
                return False, f"Failed to delete from storage: {message}"
            
            # Delete from database
            if not self._delete_file_from_db(file_id):
                return False, "Failed to delete from database"
            
            # Log the deletion
            log_access(user["id"], file_id, "DELETE", metadata={"deletion_type": "permanent"})
            log_user_action(user["id"], "FILE_DELETE", "file", file_id, file_info)
            
            return True, "File deleted successfully"
            
        except Exception as e:
            return False, f"Error deleting file: {e}"
    
    def list_user_files(self, username: str, include_shared: bool = True) -> Tuple[bool, str, List[Dict]]:
        """
        List files owned by a user and optionally shared with them.
        
        Args:
            username: Username to list files for
            include_shared: Whether to include shared files
            
        Returns:
            Tuple of (success, message, files_list)
        """
        try:
            # Get user ID
            from .auth import get_user_by_username
            user = get_user_by_username(username)
            if not user:
                return False, "User not found", []
            
            files_list = []
            
            # Get owned files
            owned_files = list_user_files(username)
            for file_info in owned_files:
                file_data = {
                    **file_info,
                    "ownership": "owned",
                    "permissions": ["read", "write", "admin"]
                }
                files_list.append(file_data)
            
            # Get shared files if requested
            if include_shared:
                from .acl import get_shared_files
                shared_files = get_shared_files(user["id"])
                for file_info in shared_files:
                    file_data = {
                        **file_info,
                        "ownership": "shared",
                        "permissions": self._get_user_file_permissions(user["id"], file_info["id"])
                    }
                    files_list.append(file_data)
            
            # Sort by modification time (newest first)
            files_list.sort(key=lambda x: x.get("modified_at", 0), reverse=True)
            
            return True, f"Found {len(files_list)} files", files_list
            
        except Exception as e:
            return False, f"Error listing files: {e}", []
    
    def get_file_statistics(self, username: str) -> Tuple[bool, str, Dict]:
        """
        Get file statistics for a user.
        
        Args:
            username: Username to get statistics for
            
        Returns:
            Tuple of (success, message, statistics)
        """
        try:
            # Get user ID
            from .auth import get_user_by_username
            user = get_user_by_username(username)
            if not user:
                return False, "User not found", {}
            
            # Get file counts and sizes
            success, message, files_list = self.list_user_files(username, include_shared=True)
            if not success:
                return False, message, {}
            
            total_size = sum(f.get("size", 0) for f in files_list)
            owned_count = len([f for f in files_list if f.get("ownership") == "owned"])
            shared_count = len([f for f in files_list if f.get("ownership") == "shared"])
            
            # Get recent activity
            from .audit import get_access_logs
            recent_logs = get_access_logs(user_id=user["id"], limit=10)
            
            statistics = {
                "total_files": len(files_list),
                "owned_files": owned_count,
                "shared_files": shared_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "recent_activity": recent_logs
            }
            
            return True, "Statistics retrieved successfully", statistics
            
        except Exception as e:
            return False, f"Error getting statistics: {e}", {}
    
    def _register_file_in_db(self, owner_id: int, file_info: Dict, metadata: Optional[Dict] = None) -> Optional[int]:
        """Register a file in the database."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO files (owner_id, filename, original_path, storage_path, file_size, mime_type, sha256, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    owner_id,
                    file_info["filename"],
                    file_info.get("original_path", ""),
                    file_info["path"],
                    file_info["size"],
                    file_info["mime_type"],
                    file_info["sha256"],
                    time.time()
                ))
                
                file_id = cursor.lastrowid
                conn.commit()
                return file_id
                
        except Exception as e:
            print(f"Error registering file in database: {e}")
            return None
    
    def _get_file_by_id(self, file_id: int) -> Optional[Dict]:
        """Get file information by ID from database."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                file_record = cursor.execute("""
                    SELECT f.*, u.username as owner_username
                    FROM files f
                    JOIN users u ON f.owner_id = u.id
                    WHERE f.id = ?
                """, (file_id,)).fetchone()
                
                return dict(file_record) if file_record else None
                
        except Exception as e:
            print(f"Error getting file by ID: {e}")
            return None
    
    def _get_file_detections(self, file_id: int) -> List[Dict]:
        """Get detections for a specific file."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                detections = cursor.execute("""
                    SELECT * FROM detections WHERE file_id = ? ORDER BY created_at DESC
                """, (file_id,)).fetchall()
                
                return [dict(detection) for detection in detections]
                
        except Exception as e:
            print(f"Error getting file detections: {e}")
            return []
    
    def _delete_file_from_db(self, file_id: int) -> bool:
        """Delete a file record from the database."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete related records first
                cursor.execute("DELETE FROM detections WHERE file_id = ?", (file_id,))
                cursor.execute("DELETE FROM acl WHERE file_id = ?", (file_id,))
                cursor.execute("DELETE FROM access_log WHERE file_id = ?", (file_id,))
                
                # Delete file record
                cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error deleting file from database: {e}")
            return False
    
    def _get_user_file_permissions(self, user_id: int, file_id: int) -> List[str]:
        """Get permissions a user has for a specific file."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                permissions = cursor.execute("""
                    SELECT permission FROM acl 
                    WHERE file_id = ? AND grantee_user_id = ? AND (expires_at IS NULL OR expires_at > ?)
                """, (file_id, user_id, time.time())).fetchall()
                
                return [perm["permission"] for perm in permissions]
                
        except Exception as e:
            print(f"Error getting user file permissions: {e}")
            return []


# Global file manager instance
file_manager = FileManager()


# Convenience functions
def upload_file(username: str, source_path: str, filename: Optional[str] = None,
                metadata: Optional[Dict] = None) -> Tuple[bool, str, Optional[int]]:
    """Upload a file to user storage and register it in the database."""
    return file_manager.upload_file(username, source_path, filename, metadata)


def download_file(username: str, file_id: int, target_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """Download a file from user storage."""
    return file_manager.download_file(username, file_id, target_path)


def view_file(username: str, file_id: int) -> Tuple[bool, str, Optional[Dict]]:
    """View file information and metadata."""
    return file_manager.view_file(username, file_id)


def share_file(owner_username: str, file_id: int, grantee_username: str,
               permission: str = "read", expires_at: Optional[float] = None) -> Tuple[bool, str]:
    """Share a file with another user."""
    return file_manager.share_file(owner_username, file_id, grantee_username, permission, expires_at)


def revoke_access(owner_username: str, file_id: int, grantee_username: str,
                 permission: str = "read") -> Tuple[bool, str]:
    """Revoke access to a file from another user."""
    return file_manager.revoke_access(owner_username, file_id, grantee_username, permission)


def delete_file(username: str, file_id: int) -> Tuple[bool, str]:
    """Delete a file from storage and database."""
    return file_manager.delete_file(username, file_id)


def list_user_files(username: str, include_shared: bool = True) -> Tuple[bool, str, List[Dict]]:
    """List files owned by a user and optionally shared with them."""
    return file_manager.list_user_files(username, include_shared)


def get_file_statistics(username: str) -> Tuple[bool, str, Dict]:
    """Get file statistics for a user."""
    return file_manager.get_file_statistics(username)


if __name__ == "__main__":
    # Test file manager functionality
    print("Testing file manager functionality...")
    
    # Note: This requires a database with users and proper setup
    # The actual testing would be done in integration tests
    print("File manager module loaded successfully")
    print("Use the convenience functions to manage files with integrated access control and auditing")
