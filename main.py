import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QStackedWidget, QMessageBox, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
from ui.dashboard_window import DashboardWindow
from ui.login_window import LoginWindow  # Import the LoginWindow
# If you have a register window, import it as well
# from ui.register_window import RegisterWindow

from dotenv import load_dotenv
def get_absolute_path():
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, 'frozen', False):
        # We are running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # We are running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path

# Load environment variables
env_path = os.path.join(get_absolute_path(), '.env')
print(f"Looking for .env at: {env_path}")  # Debug print
load_dotenv(env_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(os.getenv('APP_NAME'))
        self.setMinimumSize(800, 800)

        self.stacked_widget = QStackedWidget()
        
        # Create pages in the correct order
        self.dashboard = DashboardWindow(self.stacked_widget)
        self.login = LoginWindow(self.stacked_widget)
        # If you have a register window, create it here
        # self.register = RegisterWindow(self.stacked_widget)
        
        # Add dashboard as an attribute to stacked_widget so login can access it
        self.stacked_widget.dashboard = self.dashboard
        
        # Add widgets to stacked_widget in the correct order
        self.stacked_widget.addWidget(self.login)      # index 0
        # If you have a register window, add it here
        # self.stacked_widget.addWidget(self.register)  # index 1
        self.stacked_widget.addWidget(self.dashboard)  # index 2 (or 1 if no register page)
        
        # Start with the login page
        self.stacked_widget.setCurrentIndex(0)
        
        self.setCentralWidget(self.stacked_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())