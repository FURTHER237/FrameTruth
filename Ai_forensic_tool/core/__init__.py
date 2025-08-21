"""
FrameTruth AI Forensic Tool - Core Module
Main initialization and system setup module.
"""

import os
import sys
from pathlib import Path

# Add the core directory to Python path
core_dir = Path(__file__).parent
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

# Import core modules
from .config import config, get_config, validate_config
from .db import init_db, get_connection, get_db_info
from .auth import user_manager, create_user, authenticate_user, get_user_by_username
from .storage import storage_manager, get_user_root, store_file
from .acl import acl_manager, can_access, grant_permission
from .audit import audit_logger, log_access, log_security_event
from .file_manager import file_manager, upload_file, download_file, view_file

# Version information
__version__ = "1.0.0"
__author__ = "FrameTruth Team"
__description__ = "AI-powered forensic analysis tool with user management and audit logging"

# System status
_system_initialized = False


def initialize_system(force: bool = False) -> dict:
    """
    Initialize the core system components.
    
    Args:
        force: Force reinitialization even if already initialized
        
    Returns:
        Dictionary with initialization results
    """
    global _system_initialized
    
    if _system_initialized and not force:
        return {"status": "already_initialized", "message": "System already initialized"}
    
    try:
        results = {
            "status": "initializing",
            "components": {},
            "errors": [],
            "warnings": []
        }
        
        # 1. Validate configuration
        config_validation = validate_config()
        if not config_validation["valid"]:
            results["errors"].extend(config_validation["issues"])
        if config_validation["warnings"]:
            results["warnings"].extend(config_validation["warnings"])
        
        results["components"]["config"] = "validated"
        
        # 2. Create necessary directories
        try:
            config.create_directories()
            results["components"]["directories"] = "created"
        except Exception as e:
            results["errors"].append(f"Failed to create directories: {e}")
        
        # 3. Initialize database
        try:
            if init_db():
                results["components"]["database"] = "initialized"
            else:
                results["errors"].append("Failed to initialize database")
        except Exception as e:
            results["errors"].append(f"Database initialization error: {e}")
        
        # 4. Initialize audit logging
        try:
            # Test audit logging
            test_hash = log_system_event("SYSTEM_INITIALIZATION", {"version": __version__})
            if test_hash:
                results["components"]["audit"] = "initialized"
            else:
                results["warnings"].append("Audit logging may not be fully functional")
        except Exception as e:
            results["warnings"].append(f"Audit logging warning: {e}")
        
        # 5. Create default admin user if no users exist
        try:
            from .auth import list_users
            existing_users = list_users()
            if not existing_users:
                admin_user_id = create_user("admin", "admin123", "admin")
                if admin_user_id:
                    results["components"]["default_admin"] = "created"
                    results["warnings"].append("Default admin user created (username: admin, password: admin123)")
                else:
                    results["warnings"].append("Failed to create default admin user")
        except Exception as e:
            results["warnings"].append(f"Default user creation warning: {e}")
        
        # Determine overall status
        if results["errors"]:
            results["status"] = "failed"
            results["message"] = f"System initialization failed with {len(results['errors'])} errors"
        else:
            results["status"] = "success"
            results["message"] = "System initialized successfully"
            _system_initialized = True
        
        # Log system initialization
        try:
            if results["status"] == "success":
                log_system_event("SYSTEM_INITIALIZATION_SUCCESS", results)
            else:
                log_system_event("SYSTEM_INITIALIZATION_FAILED", results)
        except:
            pass  # Don't let logging errors affect initialization
        
        return results
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"System initialization error: {e}",
            "components": {},
            "errors": [str(e)],
            "warnings": []
        }
        
        try:
            log_system_event("SYSTEM_INITIALIZATION_ERROR", {"error": str(e)})
        except:
            pass
        
        return error_result


def get_system_status() -> dict:
    """
    Get the current system status and health information.
    
    Returns:
        Dictionary with system status information
    """
    try:
        status = {
            "initialized": _system_initialized,
            "version": __version__,
            "components": {}
        }
        
        # Check database status
        try:
            db_info = get_db_info()
            status["components"]["database"] = {
                "status": "healthy" if "error" not in db_info else "error",
                "info": db_info
            }
        except Exception as e:
            status["components"]["database"] = {"status": "error", "error": str(e)}
        
        # Check storage status
        try:
            storage_stats = storage_manager.get_storage_stats()
            status["components"]["storage"] = {
                "status": "healthy" if "error" not in storage_stats else "error",
                "info": storage_stats
            }
        except Exception as e:
            status["components"]["storage"] = {"status": "error", "error": str(e)}
        
        # Check audit logging status
        try:
            audit_integrity = audit_logger.verify_log_integrity()
            status["components"]["audit"] = {
                "status": "healthy" if audit_integrity.get("valid", False) else "warning",
                "info": audit_integrity
            }
        except Exception as e:
            status["components"]["audit"] = {"status": "error", "error": str(e)}
        
        # Check configuration status
        try:
            config_validation = validate_config()
            status["components"]["config"] = {
                "status": "healthy" if config_validation["valid"] else "warning",
                "issues": config_validation.get("issues", []),
                "warnings": config_validation.get("warnings", [])
            }
        except Exception as e:
            status["components"]["config"] = {"status": "error", "error": str(e)}
        
        # Determine overall health
        component_statuses = [comp.get("status", "unknown") for comp in status["components"].values()]
        if "error" in component_statuses:
            status["overall_health"] = "unhealthy"
        elif "warning" in component_statuses:
            status["overall_health"] = "degraded"
        else:
            status["overall_health"] = "healthy"
        
        return status
        
    except Exception as e:
        return {
            "initialized": _system_initialized,
            "version": __version__,
            "overall_health": "unknown",
            "error": str(e)
        }


def shutdown_system() -> dict:
    """
    Gracefully shutdown the system.
    
    Returns:
        Dictionary with shutdown results
    """
    global _system_initialized
    
    try:
        results = {
            "status": "shutting_down",
            "components": {},
            "message": "System shutdown initiated"
        }
        
        # Log system shutdown
        try:
            log_system_event("SYSTEM_SHUTDOWN", {"shutdown_type": "graceful"})
        except:
            pass
        
        # Cleanup operations
        try:
            # Cleanup expired sessions
            from .auth import user_manager
            expired_sessions = user_manager.cleanup_expired_sessions()
            results["components"]["sessions"] = f"cleaned {expired_sessions} expired sessions"
        except Exception as e:
            results["components"]["sessions"] = f"cleanup error: {e}"
        
        try:
            # Cleanup expired permissions
            from .acl import cleanup_expired_permissions
            expired_permissions = cleanup_expired_permissions()
            results["components"]["permissions"] = f"cleaned {expired_permissions} expired permissions"
        except Exception as e:
            results["components"]["permissions"] = f"cleanup error: {e}"
        
        try:
            # Cleanup old logs
            from .audit import cleanup_old_logs
            old_logs = cleanup_old_logs()
            results["components"]["logs"] = f"cleaned {old_logs} old log entries"
        except Exception as e:
            results["components"]["logs"] = f"cleanup error: {e}"
        
        # Mark system as not initialized
        _system_initialized = False
        
        results["status"] = "shutdown_complete"
        results["message"] = "System shutdown completed successfully"
        
        return results
        
    except Exception as e:
        return {
            "status": "shutdown_error",
            "message": f"System shutdown error: {e}",
            "error": str(e)
        }


def reset_system() -> dict:
    """
    Reset the system to initial state (WARNING: This will delete all data).
    
    Returns:
        Dictionary with reset results
    """
    try:
        results = {
            "status": "resetting",
            "message": "System reset initiated",
            "components": {}
        }
        
        # Log system reset
        try:
            log_system_event("SYSTEM_RESET", {"reset_type": "full_system_reset"})
        except:
            pass
        
        # Reset database
        try:
            from .db import reset_db
            if reset_db():
                results["components"]["database"] = "reset"
            else:
                results["components"]["database"] = "reset_failed"
        except Exception as e:
            results["components"]["database"] = f"reset_error: {e}"
        
        # Clear storage
        try:
            import shutil
            evidence_store = config.evidence_store
            if evidence_store.exists():
                shutil.rmtree(evidence_store)
                evidence_store.mkdir(exist_ok=True)
            results["components"]["storage"] = "cleared"
        except Exception as e:
            results["components"]["storage"] = f"clear_error: {e}"
        
        # Clear logs
        try:
            logs_dir = config.logs_dir
            if logs_dir.exists():
                for log_file in logs_dir.glob("*.jsonl"):
                    log_file.unlink()
            results["components"]["logs"] = "cleared"
        except Exception as e:
            results["components"]["logs"] = f"clear_error: {e}"
        
        # Mark system as not initialized
        global _system_initialized
        _system_initialized = False
        
        results["status"] = "reset_complete"
        results["message"] = "System reset completed successfully"
        
        return results
        
    except Exception as e:
        return {
            "status": "reset_error",
            "message": f"System reset error: {e}",
            "error": str(e)
        }


# Auto-initialize system when module is imported
if os.environ.get("AIFT_AUTO_INIT", "true").lower() == "true":
    try:
        init_result = initialize_system()
        if init_result["status"] == "success":
            print(f"FrameTruth AI Forensic Tool v{__version__} initialized successfully")
        else:
            print(f"FrameTruth AI Forensic Tool v{__version__} initialization warnings: {init_result.get('warnings', [])}")
    except Exception as e:
        print(f"FrameTruth AI Forensic Tool v{__version__} initialization failed: {e}")

# Export main functions and classes
__all__ = [
    # Core functions
    "initialize_system",
    "get_system_status", 
    "shutdown_system",
    "reset_system",
    
    # Configuration
    "config",
    "get_config",
    "validate_config",
    
    # Database
    "init_db",
    "get_connection",
    "get_db_info",
    
    # Authentication
    "user_manager",
    "create_user",
    "authenticate_user",
    "get_user_by_username",
    
    # Storage
    "storage_manager",
    "get_user_root",
    "store_file",
    
    # Access Control
    "acl_manager",
    "can_access",
    "grant_permission",
    
    # Audit Logging
    "audit_logger",
    "log_access",
    "log_security_event",
    
    # File Management
    "file_manager",
    "upload_file",
    "download_file",
    "view_file",
    
    # Version info
    "__version__",
    "__author__",
    "__description__"
]
