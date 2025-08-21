"""
Authentication module for FrameTruth AI Forensic Tool.
Handles user creation, authentication, and session management.
"""

import time
import hashlib
import secrets
from typing import Optional, Dict, List
from .db import get_connection


class UserManager:
    """Manages user authentication and authorization."""
    
    def __init__(self):
        self.session_tokens = {}  # In-memory session storage
    
    def create_user(self, username: str, password: str, role: str = "user") -> Optional[int]:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            password: Plain text password
            role: User role (user, admin, analyst)
            
        Returns:
            User ID if successful, None otherwise
        """
        try:
            # Validate input
            if not username or not password:
                return None
            
            if len(username) < 3 or len(username) > 50:
                return None
            
            if len(password) < 8:
                return None
            
            # Hash password with salt
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if username already exists
                existing = cursor.execute(
                    "SELECT id FROM users WHERE username = ?", 
                    (username,)
                ).fetchone()
                
                if existing:
                    return None
                
                # Create user
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, created_at)
                    VALUES (?, ?, ?, ?)
                """, (username, password_hash, role, time.time()))
                
                user_id = cursor.lastrowid
                conn.commit()
                return user_id
                
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User dictionary if successful, None otherwise
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                user = cursor.execute("""
                    SELECT id, username, password_hash, role, created_at
                    FROM users WHERE username = ?
                """, (username,)).fetchone()
                
                if not user:
                    return None
                
                # Verify password
                if self._verify_password(password, user["password_hash"]):
                    # Update last login
                    cursor.execute("""
                        UPDATE users SET last_login = ? WHERE id = ?
                    """, (time.time(), user["id"]))
                    conn.commit()
                    
                    return dict(user)
                
                return None
                
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def create_session(self, user_id: int) -> str:
        """
        Create a new session token for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Session token
        """
        token = secrets.token_urlsafe(32)
        self.session_tokens[token] = {
            "user_id": user_id,
            "created_at": time.time(),
            "expires_at": time.time() + (24 * 60 * 60)  # 24 hours
        }
        return token
    
    def validate_session(self, token: str) -> Optional[Dict]:
        """
        Validate a session token and return user info.
        
        Args:
            token: Session token
            
        Returns:
            User dictionary if valid, None otherwise
        """
        if token not in self.session_tokens:
            return None
        
        session = self.session_tokens[token]
        if time.time() > session["expires_at"]:
            del self.session_tokens[token]
            return None
        
        user = self.get_user_by_id(session["user_id"])
        if user:
            # Extend session
            session["expires_at"] = time.time() + (24 * 60 * 60)
            return user
        
        return None
    
    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a session token.
        
        Args:
            token: Session token
            
        Returns:
            True if successful, False otherwise
        """
        if token in self.session_tokens:
            del self.session_tokens[token]
            return True
        return False
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Get user information by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User dictionary if found, None otherwise
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                user = cursor.execute("""
                    SELECT id, username, role, created_at, last_login
                    FROM users WHERE id = ?
                """, (user_id,)).fetchone()
                
                return dict(user) if user else None
                
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Get user information by username.
        
        Args:
            username: Username
            
        Returns:
            User dictionary if found, None otherwise
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                user = cursor.execute("""
                    SELECT id, username, role, created_at, last_login
                    FROM users WHERE username = ?
                """, (username,)).fetchone()
                
                return dict(user) if user else None
                
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
    
    def list_users(self, include_passwords: bool = False) -> List[Dict]:
        """
        List all users in the system.
        
        Args:
            include_passwords: Whether to include password hashes
            
        Returns:
            List of user dictionaries
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                if include_passwords:
                    users = cursor.execute("""
                        SELECT id, username, password_hash, role, created_at, last_login
                        FROM users ORDER BY username
                    """).fetchall()
                else:
                    users = cursor.execute("""
                        SELECT id, username, role, created_at, last_login
                        FROM users ORDER BY username
                    """).fetchall()
                
                return [dict(user) for user in users]
                
        except Exception as e:
            print(f"Error listing users: {e}")
            return []
    
    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """
        Update a user's role.
        
        Args:
            user_id: User ID
            new_role: New role
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users SET role = ? WHERE id = ?
                """, (new_role, user_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user account.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user has files
                file_count = cursor.execute("""
                    SELECT COUNT(*) FROM files WHERE owner_id = ?
                """, (user_id,)).fetchone()[0]
                
                if file_count > 0:
                    print(f"Cannot delete user {user_id}: has {file_count} files")
                    return False
                
                # Delete user
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash a password with salt."""
        return hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        ).hex() + ":" + salt
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against stored hash."""
        try:
            hash_part, salt = stored_hash.rsplit(':', 1)
            computed_hash = hashlib.pbkdf2_hmac(
                'sha256', 
                password.encode('utf-8'), 
                salt.encode('utf-8'), 
                100000
            ).hex()
            return computed_hash == hash_part
        except:
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired session tokens.
        
        Returns:
            Number of expired sessions removed
        """
        current_time = time.time()
        expired_tokens = [
            token for token, session in self.session_tokens.items()
            if current_time > session["expires_at"]
        ]
        
        for token in expired_tokens:
            del self.session_tokens[token]
        
        return len(expired_tokens)


# Global user manager instance
user_manager = UserManager()


# Convenience functions
def create_user(username: str, password: str, role: str = "user") -> Optional[int]:
    """Create a new user account."""
    return user_manager.create_user(username, password, role)


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate a user with username and password."""
    return user_manager.authenticate_user(username, password)


def create_session(user_id: int) -> str:
    """Create a new session token for a user."""
    return user_manager.create_session(user_id)


def validate_session(token: str) -> Optional[Dict]:
    """Validate a session token and return user info."""
    return user_manager.validate_session(token)


def invalidate_session(token: str) -> bool:
    """Invalidate a session token."""
    return user_manager.invalidate_session(token)


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user information by ID."""
    return user_manager.get_user_by_id(user_id)


def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user information by username."""
    return user_manager.get_user_by_username(username)


def list_users(include_passwords: bool = False) -> List[Dict]:
    """List all users in the system."""
    return user_manager.list_users(include_passwords)


def update_user_role(user_id: int, new_role: str) -> bool:
    """Update a user's role."""
    return user_manager.update_user_role(user_id, new_role)


def delete_user(user_id: int) -> bool:
    """Delete a user account."""
    return user_manager.delete_user(user_id)


if __name__ == "__main__":
    # Test user management
    print("Testing user management...")
    
    # Create test user
    user_id = create_user("testuser", "testpass123", "user")
    if user_id:
        print(f"Created test user with ID: {user_id}")
        
        # Authenticate
        user = authenticate_user("testuser", "testpass123")
        if user:
            print(f"Authentication successful: {user}")
            
            # Create session
            token = create_session(user_id)
            print(f"Session token: {token}")
            
            # Validate session
            session_user = validate_session(token)
            if session_user:
                print(f"Session valid: {session_user}")
            else:
                print("Session validation failed")
        else:
            print("Authentication failed")
    else:
        print("User creation failed")
