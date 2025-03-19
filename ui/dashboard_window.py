from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QStackedWidget, QMessageBox, QGridLayout, QFrame,
                             QCheckBox)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QScreen
import requests
import os
import time
from datetime import timedelta
from api.api_service import APIService
from dotenv import load_dotenv
load_dotenv()
class DashboardWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.user_data = None
        self.token = None
        self.refresh_token = None
        
        # Session timer variables
        self.elapsed_time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.is_running = False
        self.is_paused = False
        
        # Screenshot timer variables
        self.screenshot_timer = QTimer()
        self.screenshot_timer.timeout.connect(self.take_screenshot)
        self.screenshot_interval = 3 * 60 * 1000  # 3 minutes in milliseconds
        self.auto_screenshot_enabled = False
        
        self.api = APIService()
        # Register the token refresh callback
        self.api.set_token_refresh_callback(self.refresh_token_callback)

        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        
        # Header layout
        header_layout = QHBoxLayout()
        
        # Dashboard title
        title_label = QLabel("Dashboard")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        header_layout.addWidget(title_label)
        
        # Spacer to push logout button to the right
        header_layout.addStretch()
        
        # Logout button
        self.logout_button = QPushButton("Logout")
        self.logout_button.setFixedWidth(100)
        self.logout_button.clicked.connect(self.logout)
        header_layout.addWidget(self.logout_button)
        
        # Add header to main layout
        header_container = QWidget()
        header_container.setLayout(header_layout)
        main_layout.addWidget(header_container)
        
        # Content layout
        content_layout = QVBoxLayout()
        
        # Welcome message
        self.welcome_label = QLabel("Welcome to your dashboard!")
        self.welcome_label.setFont(QFont("Arial", 14))
        content_layout.addWidget(self.welcome_label)
        
        # User info
        self.user_info_label = QLabel()
        content_layout.addWidget(self.user_info_label)
        
        # Stats grid
        stats_layout = QGridLayout()
        
        # Sample stats widgets
        stats_frames = []
        stats_titles = ["Total Logins", "Last Login", "Account Status", "Membership"]
        stats_values = ["15", "March 12, 2025", "Active", "Premium"]
        
        for i in range(4):
            stat_frame = QFrame()
            stat_frame.setFrameShape(QFrame.StyledPanel)
            stat_frame.setMinimumHeight(100)
            
            stat_layout = QVBoxLayout(stat_frame)
            
            title_label = QLabel(stats_titles[i])
            title_label.setFont(QFont("Arial", 10, QFont.Bold))
            stat_layout.addWidget(title_label)
            
            value_label = QLabel(stats_values[i])
            value_label.setFont(QFont("Arial", 16))
            stat_layout.addWidget(value_label)
            
            stats_frames.append(stat_frame)
            stats_layout.addWidget(stat_frame, i // 2, i % 2)
        
        # Add stats to content layout
        content_layout.addLayout(stats_layout)
        
        # Timer section
        timer_frame = QFrame()
        timer_frame.setFrameShape(QFrame.StyledPanel)
        timer_layout = QVBoxLayout(timer_frame)
        
        timer_header = QLabel("Session Timer")
        timer_header.setFont(QFont("Arial", 12, QFont.Bold))
        timer_layout.addWidget(timer_header)
        
        self.timer_display = QLabel("00:00:00")
        self.timer_display.setFont(QFont("Arial", 24))
        self.timer_display.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(self.timer_display)
        
        # Timer control buttons
        timer_buttons_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.setFixedWidth(100)
        self.start_button.clicked.connect(self.start_timer)
        timer_buttons_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setFixedWidth(100)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_timer)
        timer_buttons_layout.addWidget(self.pause_button)
        
        self.end_button = QPushButton("End")
        self.end_button.setFixedWidth(100)
        self.end_button.setEnabled(False)
        self.end_button.clicked.connect(self.end_timer)
        timer_buttons_layout.addWidget(self.end_button)
        
        timer_layout.addLayout(timer_buttons_layout)
        
        # Screenshot section
        screenshot_layout = QVBoxLayout()
        
        screenshot_header = QLabel("Screenshot Settings")
        screenshot_header.setFont(QFont("Arial", 12, QFont.Bold))
        screenshot_layout.addWidget(screenshot_header)
        
        # Screenshot control layout
        screenshot_control_layout = QHBoxLayout()
        
        # Manual screenshot button
        self.screenshot_button = QPushButton("Take Screenshot")
        self.screenshot_button.clicked.connect(self.take_screenshot)
        screenshot_control_layout.addWidget(self.screenshot_button)
        
        # Auto screenshot toggle
        self.auto_screenshot_checkbox = QCheckBox("Auto Screenshot (every 3 min)")
        self.auto_screenshot_checkbox.toggled.connect(self.toggle_auto_screenshot)
        screenshot_control_layout.addWidget(self.auto_screenshot_checkbox)
        
        screenshot_layout.addLayout(screenshot_control_layout)
        
        # Screenshot status label
        self.screenshot_status_label = QLabel("Automatic screenshots: Disabled")
        screenshot_layout.addWidget(self.screenshot_status_label)
        
        # Next screenshot time label
        self.next_screenshot_label = QLabel("")
        screenshot_layout.addWidget(self.next_screenshot_label)
        
        timer_layout.addLayout(screenshot_layout)
        
        content_layout.addWidget(timer_frame)
        content_layout.addStretch()
        
        # Add content to main layout
        content_container = QFrame()
        content_container.setLayout(content_layout)
        content_container.setFrameShape(QFrame.StyledPanel)
        main_layout.addWidget(content_container)
        
        self.setLayout(main_layout)
    
    def set_user_data(self, data):
        self.user_data = data
        self.token = data.get("token")
        self.refresh_token = data.get("refresh_token")  # Store refresh token
        
        # Update the API service with the tokens
        self.api.set_auth_token(self.token, self.refresh_token, self.user_data)
        
        user_info = data.get("user", {})
        first_name = user_info.get("firstName", "User")
        
        self.welcome_label.setText(f"Welcome, {first_name}!")
        
        # Update user info
        email = user_info.get("email", "N/A")
        self.user_info_label.setText(f"Email: {email}")
    
    def refresh_token_callback(self, refresh_token):
        """
        Callback function for the APIService to refresh the token when it expires.
        Returns a tuple of (new_access_token, new_refresh_token)
        """
        try:
            # URL for token refresh
            auth_url = f"{os.getenv('API_URL')}/auth/refresh-token" # Replace with your actual auth endpoint
            
            # Send the refresh token to get a new access token
            response = requests.post(
                auth_url,
                json={"refreshToken": refresh_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                new_token = data['data']["accessToken"]
                new_refresh_token = data['data']["refreshToken"]
                
                # Update local tokens
                self.token = new_token
                self.refresh_token = new_refresh_token
                
                # Update user data if provided in the response
                if "user" in data:
                    self.user_data["user"] = data["user"]
                    
                print("Token refreshed successfully")
                return new_token, new_refresh_token
            else:
                print(f"Failed to refresh token. Status code: {response.status_code}")
                # If refresh fails, user might need to log in again
                self.handle_auth_failure()
                return None, None
                
        except Exception as e:
            print(f"Error refreshing token: {str(e)}")
            self.handle_auth_failure()
            return None, None
    
    def handle_auth_failure(self):
        """Handle authentication failure by logging out and redirecting to login"""
        # Show message to user
        QMessageBox.warning(self, "Session Expired", 
                           "Your session has expired. Please log in again.")
        
        # Logout user
        self.logout()
    
    def start_timer(self):
        self.is_running = True
        self.is_paused = False
        self.timer.start(1000)  # Update every second
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.end_button.setEnabled(True)
        
        # Start automatic screenshots when timer starts
        if not self.auto_screenshot_enabled:
            self.auto_screenshot_checkbox.setChecked(True)
            # toggle_auto_screenshot will be called automatically due to the toggled signal
        
        # Send initial timer start event to API
        self.api.post('timer/start', {})
        
        # Take initial screenshot
        self.take_screenshot()
    
    def pause_timer(self):
        if self.is_paused:
            # Resume timer
            self.is_paused = False
            self.is_running = True
            self.timer.start(1000)
            self.pause_button.setText("Pause")
            
            # Resume automatic screenshots
            if self.auto_screenshot_enabled:
                self.screenshot_timer.start(self.screenshot_interval)
                
            # Send timer resume event to API
            self.api.post('timer/resume', {})
        else:
            # Pause timer
            self.is_paused = True
            self.is_running = False
            self.timer.stop()
            self.pause_button.setText("Resume")
            
            # Pause automatic screenshots
            if self.auto_screenshot_enabled:
                self.screenshot_timer.stop()
                
            # Send timer pause event to API
            self.api.post('timer/pause', {})
    
    def end_timer(self):
        # Send final timer data before stopping
        self.api.post('timer/end', {})
        
        self.is_running = False
        self.is_paused = False
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("Pause")
        self.end_button.setEnabled(False)
        
        # Disable automatic screenshots when timer ends
        if self.auto_screenshot_enabled:
            self.auto_screenshot_checkbox.setChecked(False)
            # toggle_auto_screenshot will be called automatically due to the toggled signal
        
        # Reset timer
        self.elapsed_time = 0
        self.timer_display.setText("00:00:00")
        
    def update_timer(self):
        self.elapsed_time += 1
        formatted_time = str(timedelta(seconds=self.elapsed_time))
        self.timer_display.setText(formatted_time)
        
        # Update next screenshot time if auto screenshots are enabled
        if self.auto_screenshot_enabled:
            remaining_time = self.screenshot_interval - (self.elapsed_time * 1000) % self.screenshot_interval
            remaining_seconds = remaining_time // 1000
            self.next_screenshot_label.setText(f"Next screenshot in: {remaining_seconds} seconds")
        
        # Send periodic updates to API (e.g., every minute)
        if self.elapsed_time % 60 == 0:
            self.api.post('timer/update', {})
    
    def toggle_auto_screenshot(self, checked):
        self.auto_screenshot_enabled = checked
        
        if checked:
            # Only start the screenshot timer if the main timer is running and not paused
            if self.is_running and not self.is_paused:
                self.screenshot_timer.start(self.screenshot_interval)
            self.screenshot_status_label.setText("Automatic screenshots: Enabled (every 3 minutes)")
            
            # Calculate time until next screenshot
            remaining_time = self.screenshot_interval
            remaining_seconds = remaining_time // 1000
            self.next_screenshot_label.setText(f"Next screenshot in: {remaining_seconds} seconds")
        else:
            # Stop the screenshot timer
            self.screenshot_timer.stop()
            self.screenshot_status_label.setText("Automatic screenshots: Disabled")
            self.next_screenshot_label.setText("")
    
    def take_screenshot(self):
        # Get the primary screen
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        
        # Save screenshot to a temporary file
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        home_dir = os.path.expanduser("~")
        save_path = os.path.join(home_dir, "Screenshots")
        
        # Create directory if it doesn't exist
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        full_path = os.path.join(save_path, filename)
        screenshot.save(full_path, "PNG")
        
        # Send to API if token is available
        if self.token:
            self.send_screenshot_to_api(full_path)
        
        # Only show message for manual screenshots
        if not self.sender() == self.screenshot_timer:
            QMessageBox.information(self, "Screenshot", f"Screenshot saved to {full_path}")
    
    def send_screenshot_to_api(self, screenshot_path):
        try:
            # Prepare the file for upload
            with open(screenshot_path, 'rb') as file:
                files = {'screenshot': file}
                
                # Additional data to send along with the screenshot
                data = {
                    'timestamp': time.time(),
                    'user_id': self.user_data.get('user', {}).get('id', ''),
                    'auto_generated': self.sender() == self.screenshot_timer
                }
                
                # Send the request using the API service
                response = self.api.post('screenshot/upload', data=data, files=files)
                
                # Check if the response is None (which happens when the request fails)
                if response is None:
                    print("Failed to upload screenshot. No response received.")
                    return
                    
                print(f"Screenshot uploaded successfully: {screenshot_path}")
                    
        except Exception as e:
            print(f"Error sending screenshot to API: {str(e)}")
    
    def logout(self):
        # Stop all timers
        if self.is_running:
            self.end_timer()
        
        if self.auto_screenshot_enabled:
            self.screenshot_timer.stop()
            self.auto_screenshot_enabled = False
            self.auto_screenshot_checkbox.setChecked(False)
        
        # Clear API service auth token
        self.api.clear_auth_token()
        
        self.user_data = None
        self.token = None
        self.refresh_token = None
        
        QMessageBox.information(self, "Logged Out", "You have been logged out successfully.")
        self.stacked_widget.setCurrentIndex(0)  # Switch to login page