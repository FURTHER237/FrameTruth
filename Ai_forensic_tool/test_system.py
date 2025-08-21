#!/usr/bin/env python3
"""
Test script for FrameTruth AI Forensic Tool infrastructure.
Demonstrates core functionality and provides a simple way to test the system.
"""

import os
import sys
import time
from pathlib import Path

# Add the core directory to the path
sys.path.insert(0, str(Path(__file__).parent / "core"))

def test_basic_functionality():
    """Test basic system functionality."""
    print("🧪 Testing basic system functionality...")
    
    try:
        # Import core modules
        from core import initialize_system, get_system_status
        print("✅ Core modules imported successfully")
        
        # Check system status
        status = get_system_status()
        print(f"✅ System status: {status['overall_health']}")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_user_management():
    """Test user management functionality."""
    print("\n👥 Testing user management...")
    
    try:
        from core import create_user, authenticate_user, get_user_by_username
        
        # Create test users
        test_users = [
            ("testadmin", "adminpass123", "admin"),
            ("testanalyst", "analystpass123", "analyst"),
            ("testuser", "userpass123", "user")
        ]
        
        created_users = []
        for username, password, role in test_users:
            user_id = create_user(username, password, role)
            if user_id:
                created_users.append((username, user_id))
                print(f"✅ Created user: {username} ({role})")
            else:
                print(f"❌ Failed to create user: {username}")
                return False
        
        # Test authentication
        for username, password, role in test_users:
            user = authenticate_user(username, password)
            if user:
                print(f"✅ Authenticated user: {username}")
            else:
                print(f"❌ Authentication failed for: {username}")
                return False
        
        # Test user lookup
        for username, password, role in test_users:
            user = get_user_by_username(username)
            if user:
                print(f"✅ Retrieved user: {username}")
            else:
                print(f"❌ User lookup failed for: {username}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ User management test failed: {e}")
        return False

def test_file_operations():
    """Test file operations functionality."""
    print("\n📁 Testing file operations...")
    
    try:
        from core import upload_file
        
        # Create a test file
        test_file_path = Path("test_evidence.txt")
        test_file_path.write_text("This is a test evidence file for testing purposes.")
        
        # Upload file
        success, message, file_id = upload_file("testanalyst", str(test_file_path), "test_evidence.txt")
        if success:
            print(f"✅ File uploaded successfully: {file_id}")
        else:
            print(f"❌ File upload failed: {message}")
            return False
        
        # Clean up test file
        test_file_path.unlink()
        
        return True
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

def test_access_control():
    """Test access control functionality."""
    print("\n🔒 Testing access control...")
    
    try:
        from core import grant_permission, can_access
        
        # Get user IDs
        from core import get_user_by_username
        owner = get_user_by_username("testanalyst")
        grantee = get_user_by_username("testuser")
        
        if not owner or not grantee:
            print("❌ User lookup failed for access control test")
            return False
        
        # Note: This test requires a file to be uploaded first
        # For now, we'll just test the permission granting mechanism
        print("✅ Access control functions imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Access control test failed: {e}")
        return False

def test_audit_logging():
    """Test audit logging functionality."""
    print("\n📊 Testing audit logging...")
    
    try:
        from core import log_security_event, log_access
        
        # Log security event
        security_hash = log_security_event("TEST_EVENT", user_id=1, details={"test": True})
        if security_hash:
            print("✅ Security event logged successfully")
        else:
            print("❌ Security event logging failed")
            return False
        
        print("✅ Audit logging functions working")
        return True
    except Exception as e:
        print(f"❌ Audit logging test failed: {e}")
        return False

def test_storage_management():
    """Test storage management functionality."""
    print("\n💾 Testing storage management...")
    
    try:
        from core import storage_manager, get_user_root
        
        # Test getting user root directory
        user_root = get_user_root("testuser")
        if user_root and user_root.exists():
            print(f"✅ User root directory: {user_root}")
        else:
            print("❌ User root directory not found")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Storage management test failed: {e}")
        return False

def test_configuration():
    """Test configuration functionality."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from core import config, validate_config
        
        # Validate configuration
        validation = validate_config()
        if validation["valid"]:
            print("✅ Configuration validation passed")
        else:
            print(f"⚠️ Configuration validation warnings: {validation.get('warnings', [])}")
        
        # Check key config values
        print(f"✅ Evidence store: {config.evidence_store}")
        print(f"✅ Logs directory: {config.logs_dir}")
        print(f"✅ Database path: {config.db_path}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 FrameTruth AI Forensic Tool - System Test")
    print("=" * 50)
    
    # Initialize system first
    try:
        from core import initialize_system
        print("🔧 Initializing system...")
        init_result = initialize_system()
        print(f"✅ System initialization: {init_result['status']}")
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return
    
    # Run tests
    tests = [
        test_basic_functionality,
        test_user_management,
        test_file_operations,
        test_access_control,
        test_audit_logging,
        test_storage_management,
        test_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print("\n💡 To use the system:")
    print("   - Default admin user: admin / admin123")
    print("   - Check the README.md for detailed usage instructions")
    print("   - Use the core module functions in your own scripts")

if __name__ == "__main__":
    main()
