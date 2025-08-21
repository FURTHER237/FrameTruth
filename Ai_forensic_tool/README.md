# FrameTruth AI Forensic Tool - Infrastructure

A comprehensive, modular infrastructure for AI-powered forensic analysis with user management, file storage, access control, and audit logging.

## 🏗️ Architecture Overview

The infrastructure is built with modularity and extensibility as core principles:

```
Ai_forensic_tool/
├── core/                    # Core system modules
│   ├── __init__.py         # Main initialization and system setup
│   ├── config.py           # Configuration management
│   ├── db.py              # Database management (SQLite)
│   ├── auth.py            # User authentication and session management
│   ├── storage.py         # File storage and organization
│   ├── acl.py             # Access Control Lists (ACL)
│   ├── audit.py           # Comprehensive audit logging
│   └── file_manager.py    # Unified file operations
├── evidence_store/         # User file storage (auto-created)
├── logs/                  # Audit and security logs (auto-created)
├── backups/               # Database backups (auto-created)
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd FrameTruth/Ai_forensic_tool

# Install dependencies (only external packages)
pip install -r requirements.txt

# The system will auto-initialize on first import
```

### 2. Basic Usage

```python
# Import the core system
from core import *

# Check system status
status = get_system_status()
print(f"System health: {status['overall_health']}")

# Create a user
user_id = create_user("analyst1", "securepass123", "analyst")

# Upload a file
success, message, file_id = upload_file("analyst1", "/path/to/evidence.jpg")
if success:
    print(f"File uploaded: {file_id}")

# Share file with another user
share_file("analyst1", file_id, "analyst2", "read")

# View file information
success, message, file_data = view_file("analyst2", file_id)
```

## 🔐 User Management

### User Roles
- **admin**: Full system access, user management
- **analyst**: File analysis, sharing, limited admin
- **user**: Basic file operations, viewing shared files

### Authentication Features
- Secure password hashing with PBKDF2
- Session management with configurable timeouts
- Account lockout protection
- Password policy enforcement

```python
# Create users
create_user("admin", "admin123", "admin")
create_user("analyst1", "pass123", "analyst")
create_user("viewer1", "view123", "user")

# Authenticate
user = authenticate_user("analyst1", "pass123")
if user:
    token = create_session(user["id"])
    print(f"Logged in: {user['username']}")
```

## 📁 File Storage System

### Per-User Storage
Each user gets their own storage directory:
```
evidence_store/
├── admin/
├── analyst1/
├── analyst2/
└── viewer1/
```

### File Operations
```python
# Upload with metadata
metadata = {"case_id": "CASE-001", "priority": "high"}
success, message, file_id = upload_file("analyst1", "evidence.jpg", metadata=metadata)

# Download file
success, message, path = download_file("analyst2", file_id, "/downloads/")

# List user files
success, message, files = list_user_files("analyst1", include_shared=True)

# Get file statistics
success, message, stats = get_file_statistics("analyst1")
```

## 🔒 Access Control (ACL)

### Permission Levels
- **read**: View file metadata and download
- **write**: Modify file permissions and metadata
- **admin**: Full control including deletion

### Sharing and Permissions
```python
# Grant read access
grant_permission(owner_id, file_id, grantee_id, "read")

# Share with expiration (24 hours)
import time
expires = time.time() + (24 * 60 * 60)
share_file("owner", file_id, "grantee", "read", expires)

# Check access
if can_access(user_id, file_id, "read"):
    print("User can access file")

# Revoke access
revoke_access("owner", file_id, "grantee", "read")
```

## 📊 Audit Logging

### Comprehensive Logging
- File access (view, download, upload, delete)
- User actions (login, logout, permission changes)
- System events (initialization, shutdown)
- Security events (failed logins, access violations)

### Tamper Detection
- Hash-chained JSONL logs
- Integrity verification
- Immutable audit trail

```python
# Log custom events
log_security_event("SUSPICIOUS_ACTIVITY", user_id=123, ip_address="192.168.1.100")
log_user_action(456, "FILE_ANALYSIS", "file", 789, {"analysis_type": "deep_scan"})

# Verify log integrity
integrity = verify_log_integrity()
print(f"Log integrity: {integrity['valid']}")

# Export logs
export_path = export_logs()
print(f"Logs exported to: {export_path}")
```

## ⚙️ Configuration

### Environment Variables
```bash
# Database
export AIFT_DB="/path/to/custom.db"

# Security
export AIFT_SESSION_TIMEOUT="48"
export AIFT_PASSWORD_MIN_LENGTH="12"
export AIFT_MAX_LOGIN_ATTEMPTS="3"

# Storage
export AIFT_MAX_FILE_SIZE_MB="500"
export AIFT_STORAGE_QUOTA_MB="5000"

# Network
export AIFT_BIND_HOST="0.0.0.0"
export AIFT_BIND_PORT="8501"

# Development
export AIFT_DEBUG_MODE="true"
export AIFT_AUTO_INIT="false"
```

### Configuration Management
```python
# Get specific configuration
db_config = get_database_config()
security_config = get_security_config()
storage_config = get_storage_config()

# Export all configuration
config_path = export_config("my_config.json")

# Load from file
load_config_from_file("custom_config.json")
```

## 🧪 Testing and Development

### System Status
```python
# Check system health
status = get_system_status()
print(f"Overall health: {status['overall_health']}")

# Component status
for component, info in status['components'].items():
    print(f"{component}: {info['status']}")
```

### Development Mode
```bash
# Enable debug mode
export AIFT_DEBUG_MODE="true"
export AIFT_TEST_MODE="true"

# Disable auto-initialization
export AIFT_AUTO_INIT="false"
```

### Manual Initialization
```python
# Force system initialization
init_result = initialize_system(force=True)
print(f"Initialization: {init_result['status']}")

# System shutdown
shutdown_result = shutdown_system()
print(f"Shutdown: {shutdown_result['status']}")

# System reset (WARNING: deletes all data)
reset_result = reset_system()
print(f"Reset: {reset_result['status']}")
```

## 🔧 Database Schema

### Core Tables
- **users**: User accounts and roles
- **files**: File metadata and storage information
- **detections**: AI detection results and analysis
- **acl**: Access control permissions
- **access_log**: Comprehensive audit trail

### Database Operations
```python
# Get database info
db_info = get_db_info()
print(f"Database size: {db_info['size_mb']:.2f} MB")

# Get connection
with get_connection() as conn:
    cursor = conn.cursor()
    # Execute queries...
```

## 📈 Performance and Scalability

### Optimization Features
- SQLite with WAL mode for concurrent access
- Connection pooling and query optimization
- Configurable worker threads
- Memory usage monitoring
- Automatic cleanup of expired data

### Monitoring
```python
# Storage statistics
stats = get_storage_stats()
print(f"Total storage: {stats['total_size_mb']:.2f} MB")

# User statistics
user_stats = get_file_statistics("analyst1")
print(f"Files owned: {user_stats['owned_files']}")
```

## 🚨 Security Features

### Built-in Security
- Password hashing with salt
- Session token management
- Access control enforcement
- Comprehensive audit logging
- Tamper detection
- Input validation and sanitization

### Security Best Practices
- Principle of least privilege
- Secure by default configuration
- Regular security audits
- Immutable audit trails
- Access revocation capabilities

## 🔄 Integration Points

### Future Extensions
- Web UI (Streamlit/Flask/FastAPI)
- REST API endpoints
- Plugin system for detectors
- External authentication providers
- Cloud storage integration
- Real-time notifications

### Current Integration
```python
# Import specific components
from core.auth import UserManager
from core.storage import StorageManager
from core.acl import ACLManager
from core.audit import AuditLogger

# Use managers directly
user_mgr = UserManager()
storage_mgr = StorageManager()
acl_mgr = ACLManager()
audit_mgr = AuditLogger()
```

## 📚 API Reference

### Core Functions
- `initialize_system()`: Initialize the system
- `get_system_status()`: Get system health
- `shutdown_system()`: Graceful shutdown
- `reset_system()`: Reset to initial state

### User Management
- `create_user(username, password, role)`
- `authenticate_user(username, password)`
- `create_session(user_id)`
- `validate_session(token)`

### File Operations
- `upload_file(username, source_path, filename, metadata)`
- `download_file(username, file_id, target_path)`
- `view_file(username, file_id)`
- `share_file(owner, file_id, grantee, permission)`

### Access Control
- `grant_permission(granter_id, file_id, grantee_id, permission)`
- `revoke_permission(revoker_id, file_id, grantee_id, permission)`
- `can_access(user_id, file_id, permission)`

### Audit Logging
- `log_access(actor_id, file_id, action, metadata)`
- `log_security_event(event_type, user_id, details)`
- `verify_log_integrity()`
- `export_logs()`

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check file permissions
   - Verify database path
   - Ensure SQLite is available

2. **Storage Permission Errors**
   - Check directory permissions
   - Verify user has write access
   - Check disk space

3. **Authentication Issues**
   - Verify user exists
   - Check password requirements
   - Clear expired sessions

### Debug Mode
```bash
export AIFT_DEBUG_MODE="true"
export AIFT_LOG_LEVEL="DEBUG"
```

### Log Analysis
```python
# Check recent access logs
logs = get_access_logs(limit=50)
for log in logs:
    print(f"{log['action']}: {log['actor_username']} -> {log['filename']}")

# Verify log integrity
integrity = verify_log_integrity()
if not integrity['valid']:
    print("Log integrity issues detected!")
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Follow the coding standards
4. Add tests for new functionality
5. Submit a pull request

### Code Standards
- Use type hints
- Follow PEP 8
- Add comprehensive docstrings
- Include error handling
- Write unit tests

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting section
- Contact the development team

---

**FrameTruth AI Forensic Tool** - Building trust through transparent analysis.
