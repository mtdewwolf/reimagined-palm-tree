import sqlite3
from datetime import datetime
import os

class Database:
    def __init__(self, db_path='weighing_system.db'):
        self.db_path = db_path
        self.ensure_db_exists()
        
    def ensure_db_exists(self):
        if not os.path.exists(self.db_path):
            self.create_tables()
            
    def create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create vehicles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_plate TEXT UNIQUE NOT NULL,
                    vehicle_type TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create weight measurements table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weight_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id INTEGER,
                    weight REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operator_id INTEGER,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
                    FOREIGN KEY (operator_id) REFERENCES users(id)
                )
            ''')
            
            # Create audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            conn.commit()
            
    def record_weight(self, weight, vehicle_id=None, operator_id=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO weight_measurements (vehicle_id, weight, operator_id)
                VALUES (?, ?, ?)
            ''', (vehicle_id, weight, operator_id))
            conn.commit()
            
    def log_audit(self, user_id, action, details=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, action, details))
            conn.commit()
            
    def get_recent_weights(self, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT w.weight, w.timestamp, v.license_plate, u.username
                FROM weight_measurements w
                LEFT JOIN vehicles v ON w.vehicle_id = v.id
                LEFT JOIN users u ON w.operator_id = u.id
                ORDER BY w.timestamp DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall() 