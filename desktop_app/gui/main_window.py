from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from ..scale.scale_interface import ScaleInterface
from ..database.database import Database
from .vehicle_dialog import VehicleDialog
from .login_dialog import LoginDialog
import sqlite3

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vehicle Weighing System")
        self.setMinimumSize(800, 600)
        
        # Initialize components
        self.scale = ScaleInterface()
        self.db = Database()
        
        # User information
        self.user_id = None
        self.user_role = None
        
        # Show login dialog
        if not self.show_login():
            # If login failed or was cancelled, close the application
            self.close()
            return
            
        # Create main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        
        # Create UI elements
        self.user_label = QLabel(f"Operator: {self.get_username()}")
        self.user_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.weight_label = QLabel("Weight: 0.00 kg")
        self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.weight_label.setStyleSheet("font-size: 24px;")
        
        self.record_button = QPushButton("Record Weight")
        self.record_button.clicked.connect(self.record_weight)
        
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        
        # Add elements to layout
        self.layout.addWidget(self.user_label)
        self.layout.addWidget(self.weight_label)
        self.layout.addWidget(self.record_button)
        self.layout.addWidget(self.logout_button)
        
        # Setup weight update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_weight)
        self.update_timer.start(100)  # Update every 100ms
        
        # Current weight value
        self.current_weight = 0.0
        
    def show_login(self):
        dialog = LoginDialog(self.db.db_path, self)
        if dialog.exec():
            user_info = dialog.get_user_info()
            self.user_id = user_info['id']
            self.user_role = user_info['role']
            return True
        return False
        
    def get_username(self):
        if not self.user_id:
            return "Not logged in"
            
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT username FROM users WHERE id = ?', (self.user_id,))
                result = cursor.fetchone()
                return result[0] if result else "Unknown"
        except:
            return "Unknown"
        
    def logout(self):
        self.user_id = None
        self.user_role = None
        if self.show_login():
            self.user_label.setText(f"Operator: {self.get_username()}")
        else:
            self.close()
        
    def update_weight(self):
        self.current_weight = self.scale.get_weight()
        self.weight_label.setText(f"Weight: {self.current_weight:.2f} kg")
        
    def record_weight(self):
        if not self.user_id:
            QMessageBox.warning(self, "Error", "Please log in to record weights")
            return
            
        dialog = VehicleDialog(self)
        if dialog.exec():
            vehicle_info = dialog.get_vehicle_info()
            
            # Add vehicle to database if it doesn't exist
            try:
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO vehicles (license_plate, vehicle_type, description)
                        VALUES (?, ?, ?)
                    ''', (vehicle_info['license_plate'], vehicle_info['vehicle_type'], vehicle_info['description']))
                    vehicle_id = cursor.lastrowid
                    
                    # Record the weight measurement with operator ID
                    cursor.execute('''
                        INSERT INTO weight_measurements (vehicle_id, weight, operator_id)
                        VALUES (?, ?, ?)
                    ''', (vehicle_id, self.current_weight, self.user_id))
                    
                    # Log the action
                    cursor.execute('''
                        INSERT INTO audit_log (user_id, action, details)
                        VALUES (?, ?, ?)
                    ''', (self.user_id, 'WEIGHT_RECORDED', f"Vehicle: {vehicle_info['license_plate']}, Weight: {self.current_weight}kg"))
                    
                    conn.commit()
                    QMessageBox.information(self, "Success", "Weight recorded successfully!")
                    
            except sqlite3.IntegrityError:
                # Vehicle already exists, get its ID
                cursor.execute('SELECT id FROM vehicles WHERE license_plate = ?', (vehicle_info['license_plate'],))
                vehicle_id = cursor.fetchone()[0]
                
                # Record the weight measurement with operator ID
                cursor.execute('''
                    INSERT INTO weight_measurements (vehicle_id, weight, operator_id)
                    VALUES (?, ?, ?)
                ''', (vehicle_id, self.current_weight, self.user_id))
                
                # Log the action
                cursor.execute('''
                    INSERT INTO audit_log (user_id, action, details)
                    VALUES (?, ?, ?)
                ''', (self.user_id, 'WEIGHT_RECORDED', f"Vehicle: {vehicle_info['license_plate']}, Weight: {self.current_weight}kg"))
                
                conn.commit()
                QMessageBox.information(self, "Success", "Weight recorded successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to record weight: {str(e)}") 