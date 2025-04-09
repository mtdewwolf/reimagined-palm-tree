from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
import hashlib
import sqlite3

class LoginDialog(QDialog):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.user_id = None
        self.user_role = None
        
        self.setWindowTitle("Login")
        self.setMinimumWidth(300)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        self.username_edit = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_edit)
        
        # Password
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.cancel_button = QPushButton("Cancel")
        self.login_button.clicked.connect(self.try_login)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add all layouts to main layout
        layout.addLayout(username_layout)
        layout.addLayout(password_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def try_login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return
            
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, role FROM users 
                    WHERE username = ? AND password_hash = ?
                ''', (username, password_hash))
                
                result = cursor.fetchone()
                if result:
                    self.user_id = result[0]
                    self.user_role = result[1]
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Invalid username or password")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")
            
    def get_user_info(self):
        return {
            'id': self.user_id,
            'role': self.user_role
        } 