"""
Access Control List (ACL) module for FrameTruth AI Forensic Tool.
Handles file permissions and sharing between users.
"""

import time
from typing import List, Dict, Optional, Tuple
from .db import get_connection


class ACLManager:
    """Manages access control lists for files."""
    
    def __init__(self):
        pass
    
    def grant_permission(self, granter_id: int, file_id: int, grantee_user_id: int, 
                        permission: str = "read", expires_at: Optional[float] = None) -> Tuple[bool, str]:
        """
        Grant a permission to a user for a specific file.
        
        Args:
            granter_id: ID of user granting permission
            file_id: ID of the file
            grantee_user_id: ID of user receiving permission
            permission: Permission type (read, write, admin)
            expires_at: Optional expiration timestamp
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate permission
            if permission not in ["read", "write", "admin"]:
                return False, "Invalid permission type"
            
            # Check if granter owns the file or has admin rights
            if not self._can_grant_permission(granter_id, file_id):
                return False, "Insufficient permissions to grant access"
            
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if permission already exists
                existing = cursor.execute("""
                    SELECT id FROM acl 
                    WHERE file_id = ? AND grantee_user_id = ? AND permission = ?
                """, (file_id, grantee_user_id, permission)).fetchone()
                
                if existing:
                    # Update existing permission
                    cursor.execute("""
                        UPDATE acl 
                        SET granted_by = ?, created_at = ?, expires_at = ?
                        WHERE file_id = ? AND grantee_user_id = ? AND permission = ?
                    """, (granter_id, time.time(), expires_at, file_id, grantee_user_id, permission))
                else:
                    # Create new permission
                    cursor.execute("""
                        INSERT INTO acl (file_id, grantee_user_id, permission, granted_by, created_at, expires_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (file_id, grantee_user_id, permission, granter_id, time.time(), expires_at))
                
                conn.commit()
                return True, f"Permission '{permission}' granted successfully"
                
        except Exception as e:
            return False, f"Error granting permission: {e}"
    
    def revoke_permission(self, revoker_id: int, file_id: int, grantee_user_id: int, 
                         permission: str = "read") -> Tuple[bool, str]:
        """
        Revoke a permission from a user for a specific file.
        
        Args:
            revoker_id: ID of user revoking permission
            file_id: ID of the file
            grantee_user_id: ID of user losing permission
            permission: Permission type to revoke
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if revoker can revoke this permission
            if not self._can_revoke_permission(revoker_id, file_id, grantee_user_id):
                return False, "Insufficient permissions to revoke access"
            
            with get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM acl 
                    WHERE file_id = ? AND grantee_user_id = ? AND permission = ?
                """, (file_id, grantee_user_id, permission))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    return True, f"Permission '{permission}' revoked successfully"
                else:
                    return False, "Permission not found"
                
        except Exception as e:
            return False, f"Error revoking permission: {e}"
    
    def revoke_all_permissions(self, revoker_id: int, file_id: int, grantee_user_id: int) -> Tuple[bool, str]:
        """
        Revoke all permissions from a user for a specific file.
        
        Args:
            revoker_id: ID of user revoking permissions
            file_id: ID of the file
            grantee_user_id: ID of user losing permissions
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if revoker can revoke permissions
            if not self._can_revoke_permission(revoker_id, file_id, grantee_user_id):
                return False, "Insufficient permissions to revoke access"
            
            with get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM acl 
                    WHERE file_id = ? AND grantee_user_id = ?
                """, (file_id, grantee_user_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    return True, f"All permissions revoked successfully ({cursor.rowcount} permissions)"
                else:
                    return False, "No permissions found"
                
        except Exception as e:
            return False, f"Error revoking permissions: {e}"
    
    def can_access(self, user_id: int, file_id: int, permission: str = "read") -> bool:
        """
        Check if a user can access a file with the specified permission.
        
        Args:
            user_id: ID of the user
            file_id: ID of the file
            permission: Required permission level
            
        Returns:
            True if user has access, False otherwise
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user owns the file
                owner = cursor.execute("""
                    SELECT owner_id FROM files WHERE id = ?
                """, (file_id,)).fetchone()
                
                if not owner:
                    return False
                
                if owner["owner_id"] == user_id:
                    return True
                
                # Check ACL permissions
                acl = cursor.execute("""
                    SELECT permission, expires_at FROM acl 
                    WHERE file_id = ? AND grantee_user_id = ? AND expires_at IS NULL OR expires_at > ?
                """, (file_id, user_id, time.time())).fetchall()
                
                if not acl:
                    return False
                
                # Check permission hierarchy
                permission_levels = {"read": 1, "write": 2, "admin": 3}
                required_level = permission_levels.get(permission, 0)
                
                for perm in acl:
                    granted_level = permission_levels.get(perm["permission"], 0)
                    if granted_level >= required_level:
                        return True
                
                return False
                
        except Exception as e:
            print(f"Error checking access: {e}")
            return False
    
    def get_file_permissions(self, file_id: int) -> List[Dict]:
        """
        Get all permissions for a specific file.
        
        Args:
            file_id: ID of the file
            
        Returns:
            List of permission dictionaries
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                permissions = cursor.execute("""
                    SELECT a.*, u.username as grantee_username, g.username as granter_username
                    FROM acl a
                    JOIN users u ON a.grantee_user_id = u.id
                    JOIN users g ON a.granted_by = g.id
                    WHERE a.file_id = ?
                    ORDER BY a.created_at DESC
                """, (file_id,)).fetchall()
                
                return [dict(perm) for perm in permissions]
                
        except Exception as e:
            print(f"Error getting file permissions: {e}")
            return []
    
    def get_user_permissions(self, user_id: int) -> List[Dict]:
        """
        Get all permissions granted to a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of permission dictionaries
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                permissions = cursor.execute("""
                    SELECT a.*, f.filename, f.original_path, u.username as granter_username
                    FROM acl a
                    JOIN files f ON a.file_id = f.id
                    JOIN users u ON a.granted_by = u.id
                    WHERE a.grantee_user_id = ? AND (a.expires_at IS NULL OR a.expires_at > ?)
                    ORDER BY a.created_at DESC
                """, (user_id, time.time())).fetchall()
                
                return [dict(perm) for perm in permissions]
                
        except Exception as e:
            print(f"Error getting user permissions: {e}")
            return []
    
    def get_shared_files(self, user_id: int) -> List[Dict]:
        """
        Get all files shared with a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of shared file dictionaries
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                shared_files = cursor.execute("""
                    SELECT DISTINCT f.*, u.username as owner_username
                    FROM files f
                    JOIN acl a ON a.file_id = f.id
                    JOIN users u ON f.owner_id = u.id
                    WHERE a.grantee_user_id = ? AND (a.expires_at IS NULL OR a.expires_at > ?)
                    ORDER BY f.created_at DESC
                """, (user_id, time.time())).fetchall()
                
                return [dict(file) for file in shared_files]
                
        except Exception as e:
            print(f"Error getting shared files: {e}")
            return []
    
    def get_file_owners(self, file_id: int) -> List[Dict]:
        """
        Get all users who have ownership or admin rights to a file.
        
        Args:
            file_id: ID of the file
            
        Returns:
            List of owner dictionaries
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Get file owner
                owner = cursor.execute("""
                    SELECT u.id, u.username, 'owner' as role
                    FROM files f
                    JOIN users u ON f.owner_id = u.id
                    WHERE f.id = ?
                """, (file_id,)).fetchone()
                
                # Get admin users
                admins = cursor.execute("""
                    SELECT u.id, u.username, 'admin' as role
                    FROM acl a
                    JOIN users u ON a.grantee_user_id = u.id
                    WHERE a.file_id = ? AND a.permission = 'admin'
                """, (file_id,)).fetchall()
                
                owners = [dict(owner)] if owner else []
                owners.extend([dict(admin) for admin in admins])
                
                return owners
                
        except Exception as e:
            print(f"Error getting file owners: {e}")
            return []
    
    def cleanup_expired_permissions(self) -> int:
        """
        Clean up expired permissions from the ACL table.
        
        Returns:
            Number of expired permissions removed
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM acl WHERE expires_at IS NOT NULL AND expires_at < ?
                """, (time.time(),))
                
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            print(f"Error cleaning up expired permissions: {e}")
            return 0
    
    def _can_grant_permission(self, user_id: int, file_id: int) -> bool:
        """Check if a user can grant permissions for a file."""
        return self.can_access(user_id, file_id, "admin")
    
    def _can_revoke_permission(self, user_id: int, file_id: int, grantee_user_id: int) -> bool:
        """Check if a user can revoke permissions for a file."""
        # File owner can revoke any permission
        with get_connection() as conn:
            cursor = conn.cursor()
            owner = cursor.execute("""
                SELECT owner_id FROM files WHERE id = ?
            """, (file_id,)).fetchone()
            
            if owner and owner["owner_id"] == user_id:
                return True
        
        # Admin users can revoke permissions
        return self.can_access(user_id, file_id, "admin")


# Global ACL manager instance
acl_manager = ACLManager()


# Convenience functions
def grant_permission(granter_id: int, file_id: int, grantee_user_id: int, 
                    permission: str = "read", expires_at: Optional[float] = None) -> Tuple[bool, str]:
    """Grant a permission to a user for a specific file."""
    return acl_manager.grant_permission(granter_id, file_id, grantee_user_id, permission, expires_at)


def revoke_permission(revoker_id: int, file_id: int, grantee_user_id: int, 
                     permission: str = "read") -> Tuple[bool, str]:
    """Revoke a permission from a user for a specific file."""
    return acl_manager.revoke_permission(revoker_id, file_id, grantee_user_id, permission)


def revoke_all_permissions(revoker_id: int, file_id: int, grantee_user_id: int) -> Tuple[bool, str]:
    """Revoke all permissions from a user for a specific file."""
    return acl_manager.revoke_all_permissions(revoker_id, file_id, grantee_user_id)


def can_access(user_id: int, file_id: int, permission: str = "read") -> bool:
    """Check if a user can access a file with the specified permission."""
    return acl_manager.can_access(user_id, file_id, permission)


def get_file_permissions(file_id: int) -> List[Dict]:
    """Get all permissions for a specific file."""
    return acl_manager.get_file_permissions(file_id)


def get_user_permissions(user_id: int) -> List[Dict]:
    """Get all permissions granted to a specific user."""
    return acl_manager.get_user_permissions(user_id)


def get_shared_files(user_id: int) -> List[Dict]:
    """Get all files shared with a specific user."""
    return acl_manager.get_shared_files(user_id)


def get_file_owners(file_id: int) -> List[Dict]:
    """Get all users who have ownership or admin rights to a file."""
    return acl_manager.get_file_owners(file_id)


def cleanup_expired_permissions() -> int:
    """Clean up expired permissions from the ACL table."""
    return acl_manager.cleanup_expired_permissions()


if __name__ == "__main__":
    # Test ACL functionality
    print("Testing ACL functionality...")
    
    # Note: This requires a database with users and files
    # The actual testing would be done in integration tests
    print("ACL module loaded successfully")
    print("Use the convenience functions to manage access control")
