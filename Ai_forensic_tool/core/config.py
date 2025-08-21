"""
Configuration module for FrameTruth AI Forensic Tool.
Centralizes all configuration settings and environment variables.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Central configuration management for the application."""
    
    def __init__(self):
        # Base paths
        self.base_dir = Path(__file__).parent.parent
        self.core_dir = self.base_dir / "core"
        self.logs_dir = self.base_dir / "logs"
        self.evidence_store = self.base_dir / "evidence_store"
        
        # Database configuration
        self.db_path = os.environ.get("AIFT_DB", str(self.base_dir / "aift.db"))
        self.db_backup_dir = self.base_dir / "backups"
        
        # Security configuration
        self.session_timeout_hours = int(os.environ.get("AIFT_SESSION_TIMEOUT", "24"))
        self.password_min_length = int(os.environ.get("AIFT_PASSWORD_MIN_LENGTH", "8"))
        self.max_login_attempts = int(os.environ.get("AIFT_MAX_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration_minutes = int(os.environ.get("AIFT_LOCKOUT_DURATION", "30"))
        
        # File storage configuration
        self.max_file_size_mb = int(os.environ.get("AIFT_MAX_FILE_SIZE_MB", "100"))
        self.allowed_file_types = os.environ.get("AIFT_ALLOWED_FILE_TYPES", 
            "jpg,jpeg,png,gif,bmp,tiff,pdf,doc,docx,xls,xlsx,ppt,pptx,txt,csv,zip,rar,7z").split(",")
        self.storage_quota_mb = int(os.environ.get("AIFT_STORAGE_QUOTA_MB", "1000"))
        
        # Audit logging configuration
        self.audit_log_retention_days = int(os.environ.get("AIFT_AUDIT_RETENTION_DAYS", "90"))
        self.security_log_retention_days = int(os.environ.get("AIFT_SECURITY_RETENTION_DAYS", "365"))
        self.log_rotation_size_mb = int(os.environ.get("AIFT_LOG_ROTATION_SIZE_MB", "10"))
        
        # Detection configuration
        self.detection_timeout_seconds = int(os.environ.get("AIFT_DETECTION_TIMEOUT", "300"))
        self.max_concurrent_detections = int(os.environ.get("AIFT_MAX_CONCURRENT_DETECTIONS", "5"))
        self.detection_cache_size = int(os.environ.get("AIFT_DETECTION_CACHE_SIZE", "1000"))
        
        # UI configuration
        self.ui_theme = os.environ.get("AIFT_UI_THEME", "light")
        self.ui_language = os.environ.get("AIFT_UI_LANGUAGE", "en")
        self.max_display_files = int(os.environ.get("AIFT_MAX_DISPLAY_FILES", "100"))
        
        # Performance configuration
        self.worker_threads = int(os.environ.get("AIFT_WORKER_THREADS", "4"))
        self.cache_enabled = os.environ.get("AIFT_CACHE_ENABLED", "true").lower() == "true"
        self.compression_enabled = os.environ.get("AIFT_COMPRESSION_ENABLED", "true").lower() == "true"
        
        # Network configuration
        self.bind_host = os.environ.get("AIFT_BIND_HOST", "127.0.0.1")
        self.bind_port = int(os.environ.get("AIFT_BIND_PORT", "8501"))
        self.max_connections = int(os.environ.get("AIFT_MAX_CONNECTIONS", "100"))
        
        # Backup configuration
        self.backup_enabled = os.environ.get("AIFT_BACKUP_ENABLED", "true").lower() == "true"
        self.backup_interval_hours = int(os.environ.get("AIFT_BACKUP_INTERVAL_HOURS", "24"))
        self.backup_retention_days = int(os.environ.get("AIFT_BACKUP_RETENTION_DAYS", "30"))
        
        # Development configuration
        self.debug_mode = os.environ.get("AIFT_DEBUG_MODE", "false").lower() == "true"
        self.test_mode = os.environ.get("AIFT_TEST_MODE", "false").lower() == "true"
        self.log_level = os.environ.get("AIFT_LOG_LEVEL", "INFO")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "db_path": self.db_path,
            "backup_dir": self.db_backup_dir,
            "journal_mode": "WAL",
            "foreign_keys": True,
            "timeout": 30.0,
            "check_same_thread": False
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "session_timeout_hours": self.session_timeout_hours,
            "password_min_length": self.password_min_length,
            "max_login_attempts": self.max_login_attempts,
            "lockout_duration_minutes": self.lockout_duration_minutes,
            "password_policy": {
                "require_uppercase": True,
                "require_lowercase": True,
                "require_digits": True,
                "require_special": False,
                "max_age_days": 90
            }
        }
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        return {
            "max_file_size_mb": self.max_file_size_mb,
            "allowed_file_types": self.allowed_file_types,
            "storage_quota_mb": self.storage_quota_mb,
            "compression_enabled": self.compression_enabled,
            "encryption_enabled": False,  # Future feature
            "deduplication_enabled": True
        }
    
    def get_audit_config(self) -> Dict[str, Any]:
        """Get audit logging configuration."""
        return {
            "audit_log_retention_days": self.audit_log_retention_days,
            "security_log_retention_days": self.security_log_retention_days,
            "log_rotation_size_mb": self.log_rotation_size_mb,
            "hash_chaining_enabled": True,
            "tamper_detection_enabled": True,
            "export_formats": ["jsonl", "csv", "xml"]
        }
    
    def get_detection_config(self) -> Dict[str, Any]:
        """Get detection configuration."""
        return {
            "timeout_seconds": self.detection_timeout_seconds,
            "max_concurrent": self.max_concurrent_detections,
            "cache_size": self.detection_cache_size,
            "enabled_detectors": [
                "image_manipulation",
                "metadata_analysis",
                "hash_verification",
                "format_validation"
            ],
            "confidence_threshold": 0.7
        }
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration."""
        return {
            "theme": self.ui_theme,
            "language": self.ui_language,
            "max_display_files": self.max_display_files,
            "auto_refresh_seconds": 30,
            "enable_notifications": True,
            "enable_animations": True
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return {
            "worker_threads": self.worker_threads,
            "cache_enabled": self.cache_enabled,
            "compression_enabled": self.compression_enabled,
            "connection_pool_size": 10,
            "query_timeout_seconds": 30,
            "max_memory_usage_mb": 512
        }
    
    def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration."""
        return {
            "bind_host": self.bind_host,
            "bind_port": self.bind_port,
            "max_connections": self.max_connections,
            "ssl_enabled": False,  # Future feature
            "cors_enabled": True,
            "rate_limiting_enabled": True
        }
    
    def get_backup_config(self) -> Dict[str, Any]:
        """Get backup configuration."""
        return {
            "enabled": self.backup_enabled,
            "interval_hours": self.backup_interval_hours,
            "retention_days": self.backup_retention_days,
            "include_files": True,
            "include_database": True,
            "include_logs": True,
            "compression": True
        }
    
    def get_development_config(self) -> Dict[str, Any]:
        """Get development configuration."""
        return {
            "debug_mode": self.debug_mode,
            "test_mode": self.test_mode,
            "log_level": self.log_level,
            "auto_reload": self.debug_mode,
            "profiling_enabled": self.debug_mode,
            "mock_external_services": self.test_mode
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return {
            "database": self.get_database_config(),
            "security": self.get_security_config(),
            "storage": self.get_storage_config(),
            "audit": self.get_audit_config(),
            "detection": self.get_detection_config(),
            "ui": self.get_ui_config(),
            "performance": self.get_performance_config(),
            "network": self.get_network_config(),
            "backup": self.get_backup_config(),
            "development": self.get_development_config()
        }
    
    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.logs_dir,
            self.evidence_store,
            self.db_backup_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return any issues."""
        issues = []
        warnings = []
        
        # Check directory permissions
        try:
            self.create_directories()
        except Exception as e:
            issues.append(f"Cannot create directories: {e}")
        
        # Check database path
        db_dir = Path(self.db_path).parent
        if not db_dir.exists():
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create database directory: {e}")
        
        # Validate numeric values
        if self.max_file_size_mb <= 0:
            issues.append("max_file_size_mb must be positive")
        
        if self.storage_quota_mb <= 0:
            issues.append("storage_quota_mb must be positive")
        
        if self.session_timeout_hours <= 0:
            issues.append("session_timeout_hours must be positive")
        
        # Check for potential security issues
        if self.bind_host == "0.0.0.0" and not self.debug_mode:
            warnings.append("Binding to 0.0.0.0 in production may be a security risk")
        
        if self.password_min_length < 8:
            warnings.append("Password minimum length is recommended to be at least 8 characters")
        
        # Check for performance issues
        if self.worker_threads > 16:
            warnings.append("High number of worker threads may impact performance")
        
        if self.max_concurrent_detections > 10:
            warnings.append("High number of concurrent detections may impact system stability")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    def export_config(self, output_path: Optional[str] = None) -> str:
        """Export configuration to a file."""
        if output_path is None:
            output_path = self.base_dir / "config_export.json"
        
        import json
        config_data = self.get_all_config()
        
        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        return str(output_path)
    
    def load_from_file(self, config_file: str) -> bool:
        """Load configuration from a file."""
        try:
            import json
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update configuration attributes
            for section, values in config_data.items():
                if hasattr(self, section):
                    section_obj = getattr(self, section)
                    if isinstance(section_obj, dict):
                        section_obj.update(values)
                    else:
                        setattr(self, section, values)
            
            return True
        except Exception as e:
            print(f"Error loading configuration from file: {e}")
            return False


# Global configuration instance
config = Config()


# Convenience functions
def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def get_database_config() -> Dict[str, Any]:
    """Get database configuration."""
    return config.get_database_config()


def get_security_config() -> Dict[str, Any]:
    """Get security configuration."""
    return config.get_security_config()


def get_storage_config() -> Dict[str, Any]:
    """Get storage configuration."""
    return config.get_storage_config()


def get_audit_config() -> Dict[str, Any]:
    """Get audit logging configuration."""
    return config.get_audit_config()


def get_detection_config() -> Dict[str, Any]:
    """Get detection configuration."""
    return config.get_detection_config()


def get_ui_config() -> Dict[str, Any]:
    """Get UI configuration."""
    return config.get_ui_config()


def get_performance_config() -> Dict[str, Any]:
    """Get performance configuration."""
    return config.get_performance_config()


def get_network_config() -> Dict[str, Any]:
    """Get network configuration."""
    return config.get_network_config()


def get_backup_config() -> Dict[str, Any]:
    """Get backup configuration."""
    return config.get_backup_config()


def get_development_config() -> Dict[str, Any]:
    """Get development configuration."""
    return config.get_development_config()


def validate_config() -> Dict[str, Any]:
    """Validate configuration and return any issues."""
    return config.validate_config()


def export_config(output_path: Optional[str] = None) -> str:
    """Export configuration to a file."""
    return config.export_config(output_path)


def load_config_from_file(config_file: str) -> bool:
    """Load configuration from a file."""
    return config.load_from_file(config_file)


if __name__ == "__main__":
    # Test configuration functionality
    print("Testing configuration functionality...")
    
    # Create directories
    config.create_directories()
    print("Directories created")
    
    # Validate configuration
    validation = validate_config()
    print(f"Configuration validation: {validation}")
    
    # Export configuration
    export_path = export_config()
    print(f"Configuration exported to: {export_path}")
    
    # Display some configuration values
    print(f"Database path: {config.db_path}")
    print(f"Max file size: {config.max_file_size_mb}MB")
    print(f"Session timeout: {config.session_timeout_hours} hours")
    print(f"Debug mode: {config.debug_mode}")
    
    print("Configuration test completed")
