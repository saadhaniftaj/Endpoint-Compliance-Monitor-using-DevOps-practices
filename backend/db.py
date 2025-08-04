import sqlite3
import logging
from typing import List, Dict, Any
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "reports.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get a database connection with proper timeout handling"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create compliance_reports table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compliance_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        hostname TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        disk_encryption_status TEXT,
                        os_updates_status TEXT,
                        running_processes TEXT,
                        compliance_score REAL,
                        is_compliant BOOLEAN,
                        details TEXT
                    )
                ''')
                
                # Create devices table for tracking unique devices
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT UNIQUE NOT NULL,
                        hostname TEXT NOT NULL,
                        first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                        total_reports INTEGER DEFAULT 0
                    )
                ''')
                # Create imposed_certificates table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS imposed_certificates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cert_id TEXT UNIQUE NOT NULL,
                        imposed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def insert_compliance_report(self, report_data: Dict[str, Any]) -> bool:
        """Insert a new compliance report"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert or update device record
                cursor.execute('''
                    INSERT OR REPLACE INTO devices (device_id, hostname, last_seen, total_reports)
                    VALUES (?, ?, ?, COALESCE(
                        (SELECT total_reports FROM devices WHERE device_id = ?) + 1, 1
                    ))
                ''', (
                    report_data['device_id'],
                    report_data['hostname'],
                    datetime.now().isoformat(),
                    report_data['device_id']
                ))
                
                # Insert compliance report
                cursor.execute('''
                    INSERT INTO compliance_reports 
                    (device_id, hostname, disk_encryption_status, os_updates_status, 
                     running_processes, compliance_score, is_compliant, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report_data['device_id'],
                    report_data['hostname'],
                    report_data.get('disk_encryption_status', 'Unknown'),
                    report_data.get('os_updates_status', 'Unknown'),
                    report_data.get('running_processes', ''),
                    report_data.get('compliance_score', 0.0),
                    report_data.get('is_compliant', False),
                    report_data.get('details', '')
                ))
                
                conn.commit()
                logger.info(f"Compliance report inserted for device {report_data['device_id']}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error inserting compliance report: {e}")
            return False
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get overall compliance summary"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total devices
                cursor.execute("SELECT COUNT(DISTINCT device_id) as total_devices FROM compliance_reports")
                total_devices = cursor.fetchone()['total_devices']
                
                # Get compliant devices
                cursor.execute("""
                    SELECT COUNT(DISTINCT device_id) as compliant_devices 
                    FROM compliance_reports 
                    WHERE is_compliant = 1
                """)
                compliant_devices = cursor.fetchone()['compliant_devices']
                
                # Calculate compliance rate
                compliance_rate = (compliant_devices / total_devices * 100) if total_devices > 0 else 0
                
                # Get recent non-compliant devices
                cursor.execute("""
                    SELECT device_id, hostname, timestamp, compliance_score, details
                    FROM compliance_reports 
                    WHERE is_compliant = 0
                    ORDER BY timestamp DESC
                    LIMIT 10
                """)
                non_compliant_devices = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'total_devices': total_devices,
                    'compliant_devices': compliant_devices,
                    'compliance_rate': round(compliance_rate, 2),
                    'non_compliant_devices': non_compliant_devices
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting compliance summary: {e}")
            return {
                'total_devices': 0,
                'compliant_devices': 0,
                'compliance_rate': 0,
                'non_compliant_devices': []
            }
    
    def get_device_history(self, device_id: str) -> List[Dict[str, Any]]:
        """Get compliance history for a specific device"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM compliance_reports 
                    WHERE device_id = ? 
                    ORDER BY timestamp DESC
                """, (device_id,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting device history: {e}")
            return []
    
    def get_recent_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent compliance reports"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM compliance_reports 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting recent reports: {e}")
            return []

    def impose_certificate(self, cert_id: str) -> bool:
        """Impose a compliance certificate (add if not already imposed)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO imposed_certificates (cert_id, imposed_at)
                    VALUES (?, ?)
                ''', (cert_id, datetime.now().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error imposing certificate: {e}")
            return False

    def get_imposed_certificates(self) -> list:
        """Get all currently imposed certificates"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT cert_id FROM imposed_certificates')
                return [row['cert_id'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching imposed certificates: {e}")
            return []

# Global database instance
db_manager = DatabaseManager() 