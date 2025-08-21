#!/usr/bin/env python3
"""
Simple login test script for FrameTruth AI Forensic Tool.
Usage: python test_login.py [username] [password]
"""

import sys
from core import *

def test_login(username, password):
    """Test login with given credentials."""
    print(f"🔐 Testing login for user: {username}")
    
    # Try to authenticate
    user = authenticate_user(username, password)
    
    if user:
        print(f"✅ Login successful!")
        print(f"   User ID: {user['id']}")
        print(f"   Username: {user['username']}")
        print(f"   Role: {user['role']}")
        print(f"   Created: {user['created_at']}")
        
        # Create session
        session_token = user_manager.create_session(user['id'])
        print(f"   Session Token: {session_token}")
        
        # Validate session
        session_info = user_manager.validate_session(session_token)
        if session_info:
            print(f"   Session Valid: Yes")
        else:
            print(f"   Session Valid: No")
            
        return True
    else:
        print(f"❌ Login failed for user: {username}")
        return False

def show_all_users():
    """List all users in the system."""
    print("\n👥 All users in system:")
    users = user_manager.list_users()
    
    if users:
        for user in users:
            print(f"   - {user['username']} (Role: {user['role']})")
    else:
        print("   No users found")

def main():
    """Main function."""
    print("🚀 FrameTruth AI Forensic Tool - Login Test")
    print("=" * 50)
    
    # Check if username and password provided
    if len(sys.argv) == 3:
        username = sys.argv[1]
        password = sys.argv[2]
        test_login(username, password)
    elif len(sys.argv) == 1:
        # No arguments - show available users and test default
        print("No credentials provided. Testing with default admin account...")
        print()
        
        # List all users
        show_all_users()
        
        print("\n" + "=" * 50)
        print("Testing default admin login...")
        test_login("admin", "admin123")
        
        print("\n" + "=" * 50)
        print("Testing test analyst login...")
        test_login("testanalyst", "analystpass123")
        
    else:
        print("Usage: python test_login.py [username] [password]")
        print("   or: python test_login.py (to test default accounts)")
        print()
        print("Examples:")
        print("   python test_login.py admin admin123")
        print("   python test_login.py testanalyst analystpass123")
        print("   python test_login.py testuser userpass123")

if __name__ == "__main__":
    main()
