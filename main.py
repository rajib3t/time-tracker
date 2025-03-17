import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QStackedWidget, QMessageBox, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
from ui.dashboard_window import DashboardWindow
from ui.login_window import LoginWindow  # Import the LoginWindow
# If you have a register window, import it as well
# from ui.register_window import RegisterWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Tracker")
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