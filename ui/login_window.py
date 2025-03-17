from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QStackedWidget, QMessageBox, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
import requests
import json
# Base URL for API requests
API_BASE_URL = "http://localhost:3000/"
class LoginWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        
        # App title
        title_label = QLabel("Login")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Form layout
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(10)
        
        # Username
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.username_input, 0, 1)
        
        # Password
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(password_label, 1, 0)
        form_layout.addWidget(self.password_input, 1, 1)
        
        # Add form to main layout
        form_container = QFrame()
        form_container.setLayout(form_layout)
        form_container.setFrameShape(QFrame.StyledPanel)
        form_container.setMaximumWidth(400)
        main_layout.addWidget(form_container)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setFixedWidth(100)
        self.login_button.clicked.connect(self.login)
        buttons_layout.addWidget(self.login_button)
        
        # Register button (redirects to register page)
        self.register_redirect_button = QPushButton("Register")
        self.register_redirect_button.setFixedWidth(100)
        self.register_redirect_button.clicked.connect(self.go_to_register)
        buttons_layout.addWidget(self.register_redirect_button)
        
        # Add buttons to main layout
        buttons_container = QWidget()
        buttons_container.setLayout(buttons_layout)
        main_layout.addWidget(buttons_container, alignment=Qt.AlignCenter)
        
        self.setLayout(main_layout)
    
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return
        
        try:
            response = requests.post(f"{API_BASE_URL}/auth/login", json={
                "email": username,
                "password": password
            })
            
            data = response.json()
            
            if response.status_code == 200 and data.get("success"):
                # Store token and user data in app
                user_data = {
                    "user": data["data"]["user"],
                    "token": data["data"]["accessToken"]  # Changed from 'token' to 'accessToken'
                }
                self.stacked_widget.dashboard.set_user_data(user_data)
                QMessageBox.information(self, "Success", "Login successful!")
                self.username_input.clear()
                self.password_input.clear()
                self.stacked_widget.setCurrentIndex(1)  # Switch to dashboard
            else:
                QMessageBox.warning(self, "Login Error", data.get("message", "Login failed."))
                
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error", f"Could not connect to server: {str(e)}")
    
    def go_to_register(self):
        self.stacked_widget.setCurrentIndex(1) 