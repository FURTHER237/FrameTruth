"""
Audit logging module for FrameTruth AI Forensic Tool.
Handles comprehensive logging of user actions and file access with tamper detection.
"""

import json
import os
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from .db import get_connection


class AuditLogger:
    """Manages comprehensive audit logging with tamper detection."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Main audit log file
        self.audit_log_path = self.log_dir / "access_audit.jsonl"
        self.security_log_path = self.log_dir / "security_events.jsonl"
        
        # Initialize log files if they don't exist
        self._init_log_files()
    
    def _init_log_files(self):
        """Initialize log files with proper headers."""
        if not self.audit_log_path.exists():
            self._write_initial_record(self.audit_log_path, "AUDIT_LOG_INIT")
        
        if not self.security_log_path.exists():
            self._write_initial_record(self.security_log_path, "SECURITY_LOG_INIT")
    
    def _write_initial_record(self, log_path: Path, record_type: str):
        """Write initial record to establish hash chain."""
        initial_record = {
            "timestamp": time.time(),
            "iso_timestamp": datetime.utcnow().isoformat(),
            "record_type": record_type,
            "message": "Log file initialized",
            "prev_hash": None,
            "record_hash": None
        }
        
        # Calculate hash for initial record
        initial_record["record_hash"] = self._calculate_record_hash(initial_record)
        
        with open(log_path, 'w') as f:
            f.write(json.dumps(initial_record) + '\n')
    
    def log_access(self, actor_user_id: int, file_id: int, action: str, 
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> str:
        """
        Log a file access event.
        
        Args:
            actor_user_id: ID of the user performing the action
            file_id: ID of the file being accessed
            action: Action type (VIEW, DOWNLOAD, UPLOAD, DELETE, SHARE, REVOKE)
            ip_address: Optional IP address of the actor
            user_agent: Optional user agent string
            metadata: Optional additional metadata
            
        Returns:
            Record hash for the logged event
        """
        try:
            # Log to database
            self._log_to_database(actor_user_id, file_id, action, ip_address, user_agent, metadata)
            
            # Log to JSONL file with hash chaining
            record_hash = self._log_to_file(self.audit_log_path, {
                "event_type": "FILE_ACCESS",
                "actor_user_id": actor_user_id,
                "file_id": file_id,
                "action": action,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "metadata": metadata or {}
            })
            
            return record_hash
            
        except Exception as e:
            print(f"Error logging access event: {e}")
            return ""
    
    def log_security_event(self, event_type: str, user_id: Optional[int] = None,
                          ip_address: Optional[str] = None, details: Optional[Dict] = None) -> str:
        """
        Log a security-related event.
        
        Args:
            event_type: Type of security event
            user_id: Optional user ID involved
            ip_address: Optional IP address
            details: Optional additional details
            
        Returns:
            Record hash for the logged event
        """
        try:
            record_hash = self._log_to_file(self.security_log_path, {
                "event_type": event_type,
                "user_id": user_id,
                "ip_address": ip_address,
                "details": details or {}
            })
            
            return record_hash
            
        except Exception as e:
            print(f"Error logging security event: {e}")
            return ""
    
    def log_user_action(self, user_id: int, action: str, target_type: Optional[str] = None,
                       target_id: Optional[int] = None, details: Optional[Dict] = None) -> str:
        """
        Log a user action event.
        
        Args:
            user_id: ID of the user performing the action
            action: Action being performed
            target_type: Type of target (user, file, permission, etc.)
            target_id: ID of the target
            details: Optional additional details
            
        Returns:
            Record hash for the logged event
        """
        try:
            record_hash = self._log_to_file(self.audit_log_path, {
                "event_type": "USER_ACTION",
                "user_id": user_id,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "details": details or {}
            })
            
            return record_hash
            
        except Exception as e:
            print(f"Error logging user action: {e}")
            return ""
    
    def log_system_event(self, event_type: str, details: Optional[Dict] = None) -> str:
        """
        Log a system-level event.
        
        Args:
            event_type: Type of system event
            details: Optional additional details
            
        Returns:
            Record hash for the logged event
        """
        try:
            record_hash = self._log_to_file(self.audit_log_path, {
                "event_type": "SYSTEM_EVENT",
                "event_type": event_type,
                "details": details or {}
            })
            
            return record_hash
            
        except Exception as e:
            print(f"Error logging system event: {e}")
            return ""
    
    def _log_to_database(self, actor_user_id: int, file_id: int, action: str,
                         ip_address: Optional[str], user_agent: Optional[str],
                         metadata: Optional[Dict]):
        """Log access event to database."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO access_log (actor_user_id, file_id, action, ip_address, user_agent, ts, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    actor_user_id, file_id, action, ip_address, user_agent, 
                    time.time(), json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error logging to database: {e}")
    
    def _log_to_file(self, log_path: Path, payload: Dict) -> str:
        """Log event to JSONL file with hash chaining."""
        try:
            # Prepare record
            record = {
                "timestamp": time.time(),
                "iso_timestamp": datetime.utcnow().isoformat(),
                **payload
            }
            
            # Get previous hash
            prev_hash = self._get_last_hash(log_path)
            record["prev_hash"] = prev_hash
            
            # Calculate current record hash
            record_hash = self._calculate_record_hash(record)
            record["record_hash"] = record_hash
            
            # Write to file
            with open(log_path, 'a') as f:
                f.write(json.dumps(record) + '\n')
            
            return record_hash
            
        except Exception as e:
            print(f"Error logging to file: {e}")
            return ""
    
    def _get_last_hash(self, log_path: Path) -> Optional[str]:
        """Get the hash of the last record in the log file."""
        try:
            if not log_path.exists():
                return None
            
            with open(log_path, 'r') as f:
                lines = f.readlines()
                if not lines:
                    return None
                
                last_line = lines[-1].strip()
                if not last_line:
                    return None
                
                last_record = json.loads(last_line)
                return last_record.get("record_hash")
                
        except Exception as e:
            print(f"Error getting last hash: {e}")
            return None
    
    def _calculate_record_hash(self, record: Dict) -> str:
        """Calculate hash for a record."""
        # Create a copy without the hash fields for consistent hashing
        record_copy = record.copy()
        record_copy.pop("prev_hash", None)
        record_copy.pop("record_hash", None)
        
        # Sort keys for consistent hashing
        sorted_record = json.dumps(record_copy, sort_keys=True, separators=(',', ':'))
        
        return hashlib.sha256(sorted_record.encode('utf-8')).hexdigest()
    
    def verify_log_integrity(self, log_path: Optional[Path] = None) -> Dict:
        """
        Verify the integrity of the audit log by checking hash chains.
        
        Args:
            log_path: Optional specific log file to verify
            
        Returns:
            Dictionary with verification results
        """
        try:
            if log_path is None:
                log_path = self.audit_log_path
            
            if not log_path.exists():
                return {"valid": False, "error": "Log file does not exist"}
            
            with open(log_path, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                return {"valid": True, "message": "Empty log file"}
            
            errors = []
            prev_hash = None
            
            for i, line in enumerate(lines, 1):
                try:
                    record = json.loads(line.strip())
                    
                    # Skip initial records
                    if record.get("record_type") in ["AUDIT_LOG_INIT", "SECURITY_LOG_INIT"]:
                        prev_hash = record.get("record_hash")
                        continue
                    
                    # Verify previous hash
                    if prev_hash != record.get("prev_hash"):
                        errors.append(f"Line {i}: Previous hash mismatch")
                    
                    # Verify current hash
                    expected_hash = self._calculate_record_hash(record)
                    actual_hash = record.get("record_hash")
                    
                    if expected_hash != actual_hash:
                        errors.append(f"Line {i}: Hash mismatch")
                    
                    prev_hash = actual_hash
                    
                except json.JSONDecodeError as e:
                    errors.append(f"Line {i}: Invalid JSON - {e}")
                except Exception as e:
                    errors.append(f"Line {i}: Error processing - {e}")
            
            return {
                "valid": len(errors) == 0,
                "total_records": len(lines),
                "errors": errors,
                "message": "Log integrity verified" if len(errors) == 0 else f"Found {len(errors)} errors"
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def get_access_logs(self, user_id: Optional[int] = None, file_id: Optional[int] = None,
                        action: Optional[str] = None, start_time: Optional[float] = None,
                        end_time: Optional[float] = None, limit: int = 100) -> List[Dict]:
        """
        Get access logs from database with optional filtering.
        
        Args:
            user_id: Filter by specific user
            file_id: Filter by specific file
            action: Filter by specific action
            start_time: Filter by start time (timestamp)
            end_time: Filter by end time (timestamp)
            limit: Maximum number of records to return
            
        Returns:
            List of access log records
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT al.*, u.username as actor_username, f.filename
                    FROM access_log al
                    JOIN users u ON al.actor_user_id = u.id
                    JOIN files f ON al.file_id = f.id
                    WHERE 1=1
                """
                params = []
                
                if user_id is not None:
                    query += " AND al.actor_user_id = ?"
                    params.append(user_id)
                
                if file_id is not None:
                    query += " AND al.file_id = ?"
                    params.append(file_id)
                
                if action is not None:
                    query += " AND al.action = ?"
                    params.append(action)
                
                if start_time is not None:
                    query += " AND al.ts >= ?"
                    params.append(start_time)
                
                if end_time is not None:
                    query += " AND al.ts <= ?"
                    params.append(end_time)
                
                query += " ORDER BY al.ts DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                records = cursor.fetchall()
                
                return [dict(record) for record in records]
                
        except Exception as e:
            print(f"Error getting access logs: {e}")
            return []
    
    def export_logs(self, log_path: Optional[Path] = None, output_path: Optional[str] = None) -> str:
        """
        Export logs to a file with integrity verification.
        
        Args:
            log_path: Optional specific log file to export
            output_path: Optional output file path
            
        Returns:
            Path to exported file
        """
        try:
            if log_path is None:
                log_path = self.audit_log_path
            
            if not log_path.exists():
                return ""
            
            # Verify integrity before export
            integrity_check = self.verify_log_integrity(log_path)
            if not integrity_check["valid"]:
                print(f"Warning: Log integrity check failed: {integrity_check['errors']}")
            
            # Generate output path
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"exported_logs_{timestamp}.jsonl"
            
            # Copy log file
            import shutil
            shutil.copy2(log_path, output_path)
            
            # Add integrity information
            with open(output_path, 'a') as f:
                f.write(json.dumps({
                    "export_timestamp": time.time(),
                    "export_iso_timestamp": datetime.utcnow().isoformat(),
                    "integrity_check": integrity_check,
                    "export_type": "AUDIT_LOG_EXPORT"
                }) + '\n')
            
            return output_path
            
        except Exception as e:
            print(f"Error exporting logs: {e}")
            return ""
    
    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Clean up old log entries from database.
        
        Args:
            days_to_keep: Number of days of logs to keep
            
        Returns:
            Number of records cleaned up
        """
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            
            with get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM access_log WHERE ts < ?
                """, (cutoff_time,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                return deleted_count
                
        except Exception as e:
            print(f"Error cleaning up old logs: {e}")
            return 0


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions
def log_access(actor_user_id: int, file_id: int, action: str, 
               ip_address: Optional[str] = None, user_agent: Optional[str] = None,
               metadata: Optional[Dict] = None) -> str:
    """Log a file access event."""
    return audit_logger.log_access(actor_user_id, file_id, action, ip_address, user_agent, metadata)


def log_security_event(event_type: str, user_id: Optional[int] = None,
                      ip_address: Optional[str] = None, details: Optional[Dict] = None) -> str:
    """Log a security-related event."""
    return audit_logger.log_security_event(event_type, user_id, ip_address, details)


def log_user_action(user_id: int, action: str, target_type: Optional[str] = None,
                   target_id: Optional[int] = None, details: Optional[Dict] = None) -> str:
    """Log a user action event."""
    return audit_logger.log_user_action(user_id, action, target_type, target_id, details)


def log_system_event(event_type: str, details: Optional[Dict] = None) -> str:
    """Log a system-level event."""
    return audit_logger.log_system_event(event_type, details)


def verify_log_integrity(log_path: Optional[Path] = None) -> Dict:
    """Verify the integrity of the audit log by checking hash chains."""
    return audit_logger.verify_log_integrity(log_path)


def get_access_logs(user_id: Optional[int] = None, file_id: Optional[int] = None,
                    action: Optional[str] = None, start_time: Optional[float] = None,
                    end_time: Optional[float] = None, limit: int = 100) -> List[Dict]:
    """Get access logs from database with optional filtering."""
    return audit_logger.get_access_logs(user_id, file_id, action, start_time, end_time, limit)


def export_logs(log_path: Optional[Path] = None, output_path: Optional[str] = None) -> str:
    """Export logs to a file with integrity verification."""
    return audit_logger.export_logs(log_path, output_path)


def cleanup_old_logs(days_to_keep: int = 90) -> int:
    """Clean up old log entries from database."""
    return audit_logger.cleanup_old_logs(days_to_keep)


if __name__ == "__main__":
    # Test audit logging functionality
    print("Testing audit logging functionality...")
    
    # Test security event logging
    security_hash = log_security_event("LOGIN_ATTEMPT", user_id=1, ip_address="192.168.1.1")
    print(f"Security event logged with hash: {security_hash}")
    
    # Test user action logging
    action_hash = log_user_action(1, "FILE_UPLOAD", "file", 123, {"size": 1024})
    print(f"User action logged with hash: {action_hash}")
    
    # Test system event logging
    system_hash = log_system_event("DATABASE_BACKUP", {"backup_size": "50MB"})
    print(f"System event logged with hash: {system_hash}")
    
    # Verify log integrity
    integrity = verify_log_integrity()
    print(f"Log integrity: {integrity}")
    
    print("Audit logging test completed")
