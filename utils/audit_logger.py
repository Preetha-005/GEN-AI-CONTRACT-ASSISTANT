"""
Audit Logger Module
Maintains audit trails for contract analysis
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import logging

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditLogger:
    """Logs all contract analysis activities for audit purposes"""
    
    def __init__(self):
        """Initialize audit logger"""
        self.audit_dir = config.AUDIT_LOG_DIR
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.enabled = config.ENABLE_AUDIT_TRAIL
    
    def log_analysis(self, 
                    document_info: Dict, 
                    analysis_results: Dict,
                    user_info: Optional[Dict] = None) -> str:
        """
        Log a complete contract analysis session
        
        Args:
            document_info: Information about the analyzed document
            analysis_results: Results of the analysis
            user_info: Optional user information
            
        Returns:
            Audit log ID
        """
        if not self.enabled:
            return "audit_disabled"
        
        # Generate unique audit ID
        timestamp = datetime.now().isoformat()
        audit_id = self._generate_audit_id(document_info, timestamp)
        
        # Create audit record
        audit_record = {
            'audit_id': audit_id,
            'timestamp': timestamp,
            'document_info': {
                'filename': document_info.get('filename', 'unknown'),
                'file_hash': self._hash_file(document_info.get('file_path')),
                'file_size': document_info.get('file_size', 0),
                'file_type': document_info.get('file_type', 'unknown')
            },
            'analysis_summary': {
                'risk_level': analysis_results.get('risk_assessment', {}).get('overall_risk_level'),
                'risk_score': analysis_results.get('risk_assessment', {}).get('overall_risk_score'),
                'high_risk_clauses': len(analysis_results.get('risk_assessment', {}).get('high_risk_clauses', [])),
                'flags_raised': len(analysis_results.get('risk_assessment', {}).get('risk_flags', []))
            },
            'user_info': user_info or {'user': 'anonymous'},
            'metadata': {
                'version': '1.0',
                'system': 'GenAI Legal Assistant'
            }
        }
        
        # Save audit log
        log_file = self.audit_dir / f"audit_{audit_id}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(audit_record, f, indent=2)
        
        logger.info(f"Audit log created: {audit_id}")
        return audit_id
    
    def log_action(self, action: str, details: Dict):
        """
        Log a specific action
        
        Args:
            action: Action name
            details: Action details
        """
        if not self.enabled:
            return
        
        timestamp = datetime.now().isoformat()
        action_record = {
            'timestamp': timestamp,
            'action': action,
            'details': details
        }
        
        # Append to daily log file
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = self.audit_dir / f"actions_{date_str}.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(action_record) + '\n')
    
    def get_audit_log(self, audit_id: str) -> Optional[Dict]:
        """
        Retrieve an audit log by ID
        
        Args:
            audit_id: Audit log identifier
            
        Returns:
            Audit log dictionary or None
        """
        log_file = self.audit_dir / f"audit_{audit_id}.json"
        
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def list_audit_logs(self, limit: int = 10) -> list:
        """
        List recent audit logs
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of audit log summaries
        """
        log_files = sorted(
            self.audit_dir.glob('audit_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        summaries = []
        for log_file in log_files[:limit]:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    summaries.append({
                        'audit_id': log_data['audit_id'],
                        'timestamp': log_data['timestamp'],
                        'filename': log_data['document_info']['filename'],
                        'risk_level': log_data['analysis_summary']['risk_level']
                    })
            except Exception as e:
                logger.error(f"Error reading audit log {log_file}: {e}")
        
        return summaries
    
    def cleanup_old_logs(self, days: int = None):
        """
        Remove audit logs older than specified days
        
        Args:
            days: Number of days to retain (uses config if None)
        """
        if days is None:
            days = config.AUDIT_LOG_RETENTION_DAYS
        
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        removed_count = 0
        for log_file in self.audit_dir.glob('*.json*'):
            if log_file.stat().st_mtime < cutoff_date:
                log_file.unlink()
                removed_count += 1
        
        logger.info(f"Cleaned up {removed_count} old audit logs")
        return removed_count
    
    def _generate_audit_id(self, document_info: Dict, timestamp: str) -> str:
        """Generate unique audit ID"""
        content = f"{document_info.get('filename', '')}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _hash_file(self, file_path: Optional[str]) -> str:
        """Generate hash of file for integrity checking"""
        if not file_path or not Path(file_path).exists():
            return "no_hash"
        
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()[:32]
        except Exception as e:
            logger.error(f"Error hashing file: {e}")
            return "hash_error"
    
    def export_audit_trail(self, output_file: str, start_date: Optional[str] = None):
        """
        Export complete audit trail to a file
        
        Args:
            output_file: Output file path
            start_date: Optional start date filter (YYYY-MM-DD)
        """
        all_logs = []
        
        for log_file in self.audit_dir.glob('audit_*.json'):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    
                    # Filter by date if specified
                    if start_date:
                        log_date = log_data['timestamp'][:10]
                        if log_date < start_date:
                            continue
                    
                    all_logs.append(log_data)
            except Exception as e:
                logger.error(f"Error reading {log_file}: {e}")
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Export
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_logs, f, indent=2)
        
        logger.info(f"Exported {len(all_logs)} audit logs to {output_file}")
        return len(all_logs)


if __name__ == "__main__":
    # Test audit logger
    logger_instance = AuditLogger()
    print(f"Audit logging enabled: {logger_instance.enabled}")
    print(f"Audit directory: {logger_instance.audit_dir}")
