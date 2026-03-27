"""
Audit logging system for privacy-aware RAG.
Logs all queries, retrievals, and access decisions for compliance and security.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal
from theme.constants import STATUS_ICONS

LogFormat = Literal["json", "csv"]

class AuditLogger:
    """Logs user queries and system responses for audit trail."""
    
    def __init__(
        self,
        log_dir: str = "version3/logs",
        log_format: LogFormat = "json",
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_format = log_format
        
        # Create log file path with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        if log_format == "json":
            self.log_file = self.log_dir / f"audit_{timestamp}.jsonl"
        else:
            self.log_file = self.log_dir / f"audit_{timestamp}.csv"
            self._init_csv()
    
    def _init_csv(self):
        """Initialize CSV file with headers if it doesn't exist."""
        if not self.log_file.exists():
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "user_role",
                    "query",
                    "retrieved_count",
                    "filtered_count",
                    "sensitivity_levels",
                    "response_preview",
                    "execution_time_ms",
                    "status",
                ])
    
    def log_query(
        self,
        user_role: str,
        query: str,
        retrieved_docs: list[dict],
        filtered_count: int,
        response: str,
        execution_time_ms: int,
        status: str = "success",
        additional_info: Optional[dict] = None,
        user_id: str = "anonymous",
    ):
        """
        Log a query and its results.
        
        Args:
            user_role: Role of the user making the query
            query: The user's query text
            retrieved_docs: List of retrieved document metadata
            filtered_count: Number of documents filtered by role
            response: Generated response (will be truncated for preview)
            execution_time_ms: Query execution time in milliseconds
            status: Query status (success/error/filtered)
            additional_info: Optional additional information
            user_id: Username of the user making the query
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Extract sensitivity levels from retrieved docs
        sensitivity_levels = list(set(
            doc.get("sensitivity_level", "unknown")
            for doc in retrieved_docs
        ))
        
        # Create response preview (first 200 chars)
        response_preview = response[:200] + "..." if len(response) > 200 else response
        
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "user_role": user_role,
            "query": query,
            "retrieved_count": len(retrieved_docs),
            "filtered_count": filtered_count,
            "sensitivity_levels": sensitivity_levels,
            "response_preview": response_preview,
            "execution_time_ms": execution_time_ms,
            "status": status,
        }
        
        if additional_info:
            log_entry["additional_info"] = additional_info
        
        # Write to log file
        if self.log_format == "json":
            self._write_json(log_entry)
        else:
            self._write_csv(log_entry)
    
    def _write_json(self, log_entry: dict):
        """Write log entry to JSONL file."""
        with open(self.log_file, 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')
    
    def _write_csv(self, log_entry: dict):
        """Write log entry to CSV file."""
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                log_entry["timestamp"],
                log_entry["user_role"],
                log_entry["query"],
                log_entry["retrieved_count"],
                log_entry["filtered_count"],
                ';'.join(log_entry["sensitivity_levels"]),
                log_entry["response_preview"],
                log_entry["execution_time_ms"],
                log_entry["status"],
            ])
    
    def log_access_denied(
        self,
        user_role: str,
        query: str,
        reason: str,
    ):
        """Log an access denied event."""
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "user_role": user_role,
            "query": query,
            "status": "access_denied",
            "reason": reason,
        }
        
        if self.log_format == "json":
            self._write_json(log_entry)
        else:
            # For CSV, write a special access denied entry
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    user_role,
                    query,
                    0,  # retrieved_count
                    0,  # filtered_count
                    "",  # sensitivity_levels
                    f"ACCESS DENIED: {reason}",
                    0,  # execution_time_ms
                    "access_denied",
                ])
    
    def get_recent_logs(self, limit: int = 10) -> list[dict]:
        """
        Get recent log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of log entries (most recent first)
        """
        if not self.log_file.exists():
            return []
        
        if self.log_format == "json":
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                entries = [json.loads(line) for line in lines[-limit:]]
                return list(reversed(entries))
        else:
            with open(self.log_file, 'r') as f:
                reader = csv.DictReader(f)
                entries = list(reader)
                return list(reversed(entries[-limit:]))
    
    def get_stats(self) -> dict:
        """Get audit statistics."""
        if not self.log_file.exists():
            return {
                "total_queries": 0,
                "by_role": {},
                "by_status": {},
            }
        
        stats = {
            "total_queries": 0,
            "by_role": {},
            "by_status": {},
        }
        
        if self.log_format == "json":
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    stats["total_queries"] += 1
                    
                    role = entry.get("user_role", "unknown")
                    stats["by_role"][role] = stats["by_role"].get(role, 0) + 1
                    
                    status = entry.get("status", "unknown")
                    stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        else:
            with open(self.log_file, 'r') as f:
                reader = csv.DictReader(f)
                for entry in reader:
                    stats["total_queries"] += 1
                    
                    role = entry.get("user_role", "unknown")
                    stats["by_role"][role] = stats["by_role"].get(role, 0) + 1
                    
                    status = entry.get("status", "unknown")
                    stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        return stats


if __name__ == "__main__":
    # Test the audit logger
    print(f"{STATUS_ICONS['info']} Testing Audit Logger\n")
    
    # Create test logger
    logger = AuditLogger(log_dir="version3/logs/test", log_format="json")
    
    # Log some test queries
    logger.log_query(
        user_role="employee",
        query="What is the company policy?",
        retrieved_docs=[
            {"sensitivity_level": "public", "filename": "policy.pdf"},
            {"sensitivity_level": "public", "filename": "handbook.pdf"},
        ],
        filtered_count=0,
        response="The company policy states...",
        execution_time_ms=1234,
    )
    
    logger.log_query(
        user_role="employee",
        query="What is the CEO's salary?",
        retrieved_docs=[],
        filtered_count=3,
        response="I don't have information about that in the available documents.",
        execution_time_ms=567,
        status="filtered",
    )
    
    logger.log_access_denied(
        user_role="employee",
        query="Show confidential documents",
        reason="Insufficient permissions",
    )
    
    print(f"{STATUS_ICONS['success']} Logged 3 test entries")
    print(f"Log file: {logger.log_file}")
    
    # Get stats
    stats = logger.get_stats()
    print(f"\n{STATUS_ICONS['complete']} Audit Statistics:")
    print(f"  Total queries: {stats['total_queries']}")
    print(f"  By role: {stats['by_role']}")
    print(f"  By status: {stats['by_status']}")
    
    # Get recent logs
    print(f"\n{STATUS_ICONS['info']} Recent logs:")
    for entry in logger.get_recent_logs(limit=3):
        print(f"  [{entry['timestamp']}] {entry['user_role']}: {entry['query'][:50]}... -> {entry['status']}")
