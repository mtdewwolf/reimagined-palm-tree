from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QComboBox, QPushButton, QTextEdit)
from PyQt6.QtCore import Qt

class VehicleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vehicle Information")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout()
        
        # License Plate
        plate_layout = QHBoxLayout()
        plate_label = QLabel("License Plate:")
        self.plate_edit = QLineEdit()
        plate_layout.addWidget(plate_label)
        plate_layout.addWidget(self.plate_edit)
        
        # Vehicle Type
        type_layout = QHBoxLayout()
        type_label = QLabel("Vehicle Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Truck", "Trailer", "Car", "Other"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        
        # Description
        desc_layout = QVBoxLayout()
        desc_label = QLabel("Description:")
        self.desc_edit = QTextEdit()
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add all layouts to main layout
        layout.addLayout(plate_layout)
        layout.addLayout(type_layout)
        layout.addLayout(desc_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def get_vehicle_info(self):
        return {
            'license_plate': self.plate_edit.text(),
            'vehicle_type': self.type_combo.currentText(),
            'description': self.desc_edit.toPlainText()
        } 