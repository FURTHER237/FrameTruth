#!/usr/bin/env python3
"""
Interactive CLI test script for FrameTruth AI Forensic Tool.
Provides a simple menu system for testing various functions.
"""

import sys
from core import *

def show_menu():
    """Display the main menu."""
    print("\n" + "=" * 50)
    print("🔧 FrameTruth AI Forensic Tool - Test CLI")
    print("=" * 50)
    print("1. Login")
    print("2. List Users")
    print("3. Test File Upload")
    print("4. Test File Operations")
    print("5. Test Access Control")
    print("6. View System Status")
    print("7. Exit")
    print("=" * 50)

def login_menu():
    """Handle login functionality."""
    print("\n🔐 Login Menu")
    print("-" * 20)
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    if not username or not password:
        print("❌ Username and password required")
        return None
    
    user = authenticate_user(username, password)
    if user:
        print(f"✅ Login successful! Welcome {user['username']} ({user['role']})")
        
        # Create session
        session_token = create_session(user['id'])
        print(f"Session created: {session_token[:20]}...")
        
        return user
    else:
        print("❌ Login failed. Invalid credentials.")
        return None

def test_file_upload(user):
    """Test file upload functionality."""
    print(f"\n📁 File Upload Test for {user['username']}")
    print("-" * 40)
    
    # Create a test file
    test_content = f"This is a test file created by {user['username']} at {time.time()}"
    test_filename = f"test_file_{user['username']}.txt"
    
    with open(test_filename, 'w') as f:
        f.write(test_content)
    
    print(f"Created test file: {test_filename}")
    
    # Upload the file
    success, message, file_id = upload_file(user['username'], test_filename)
    
    if success:
        print(f"✅ File uploaded successfully!")
        print(f"   File ID: {file_id}")
        print(f"   Message: {message}")
    else:
        print(f"❌ File upload failed: {message}")
    
    # Clean up test file
    import os
    if os.path.exists(test_filename):
        os.remove(test_filename)
        print(f"Cleaned up test file: {test_filename}")

def test_file_operations(user):
    """Test basic file operations."""
    print(f"\n📋 File Operations Test for {user['username']}")
    print("-" * 40)
    
    # List user files
    success, message, files = list_user_files(user['username'])
    
    if success and files:
        print(f"✅ Found {len(files)} files:")
        for i, file_info in enumerate(files[:5]):  # Show first 5 files
            print(f"   {i+1}. {file_info.get('filename', 'Unknown')} ({file_info.get('size', 0)} bytes)")
    else:
        print(f"❌ No files found or error: {message}")

def test_access_control(user):
    """Test access control functionality."""
    print(f"\n🔒 Access Control Test for {user['username']}")
    print("-" * 40)
    
    # Get user's files
    success, message, files = list_user_files(user['username'])
    
    if success and files:
        file_id = files[0].get('id')
        if file_id:
            print(f"Testing access control for file ID: {file_id}")
            
            # Test if user can access their own file
            can_read = can_access(user['id'], file_id, "read")
            can_write = can_access(user['id'], file_id, "write")
            can_admin = can_access(user['id'], file_id, "admin")
            
            print(f"   Read access: {'✅' if can_read else '❌'}")
            print(f"   Write access: {'✅' if can_write else '❌'}")
            print(f"   Admin access: {'✅' if can_admin else '❌'}")
        else:
            print("❌ No file ID found for testing")
    else:
        print("❌ No files available for access control testing")

def main():
    """Main CLI loop."""
    print("🚀 Starting FrameTruth AI Forensic Tool Test CLI...")
    
    current_user = None
    
    while True:
        show_menu()
        
        try:
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == "1":
                current_user = login_menu()
                
            elif choice == "2":
                print("\n👥 Listing all users...")
                users = list_users()
                if users:
                    for user in users:
                        print(f"   - {user['username']} (Role: {user['role']})")
                else:
                    print("   No users found")
                    
            elif choice == "3":
                if current_user:
                    test_file_upload(current_user)
                else:
                    print("❌ Please login first (option 1)")
                    
            elif choice == "4":
                if current_user:
                    test_file_operations(current_user)
                else:
                    print("❌ Please login first (option 1)")
                    
            elif choice == "5":
                if current_user:
                    test_access_control(current_user)
                else:
                    print("❌ Please login first (option 1)")
                    
            elif choice == "6":
                print("\n📊 System Status:")
                status = get_system_status()
                print(f"   Overall Health: {status['overall_health']}")
                print(f"   Database: {status['components'].get('database', 'Unknown')}")
                print(f"   Storage: {status['components'].get('storage', 'Unknown')}")
                print(f"   Audit: {status['components'].get('audit', 'Unknown')}")
                
            elif choice == "7":
                print("\n👋 Goodbye! Exiting...")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-7.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or contact support.")

if __name__ == "__main__":
    main()
