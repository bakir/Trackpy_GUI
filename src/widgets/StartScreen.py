"""
Start Screen Widget

Description: Main start screen with project management options.
             Allows users to create new projects or open existing ones.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QFileDialog, QMessageBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon
import os
from ..project_manager import ProjectManager


class StartScreen(QWidget):
    """Main start screen widget for project management."""
    
    project_selected = Signal(str)  # Emits project path when project is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_manager = ProjectManager()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Particle Tracking GUI")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Select a project to begin particle tracking analysis")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 30px;")
        main_layout.addWidget(subtitle_label)
        
        # Project management section
        project_frame = QFrame()
        project_frame.setFrameStyle(QFrame.Box)
        project_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                background-color: #f8f9fa;
                padding: 20px;
            }
        """)
        project_layout = QVBoxLayout(project_frame)
        
        # Recent projects section
        recent_label = QLabel("Recent Projects")
        recent_font = QFont()
        recent_font.setPointSize(14)
        recent_font.setBold(True)
        recent_label.setFont(recent_font)
        recent_label.setStyleSheet("color: #34495e; margin-bottom: 10px;")
        project_layout.addWidget(recent_label)
        
        # Recent projects list (placeholder)
        self.recent_projects_list = QListWidget()
        self.recent_projects_list.setMaximumHeight(100)
        self.recent_projects_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        # Add placeholder items
        placeholder_item = QListWidgetItem("No recent projects")
        placeholder_item.setFlags(Qt.NoItemFlags)  # Make it non-selectable
        self.recent_projects_list.addItem(placeholder_item)
        project_layout.addWidget(self.recent_projects_list)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # New Project button
        self.new_project_btn = QPushButton("Create New Project")
        self.new_project_btn.setMinimumHeight(50)
        self.new_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.new_project_btn.clicked.connect(self.create_new_project)
        button_layout.addWidget(self.new_project_btn)
        
        # Open Project button
        self.open_project_btn = QPushButton("Open Existing Project")
        self.open_project_btn.setMinimumHeight(50)
        self.open_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.open_project_btn.clicked.connect(self.open_existing_project)
        button_layout.addWidget(self.open_project_btn)
        
        project_layout.addLayout(button_layout)
        main_layout.addWidget(project_frame)
        
        # Add some stretch to center everything
        main_layout.addStretch()
        
        # Footer
        footer_label = QLabel("© 2024 Particle Tracking GUI")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #95a5a6; font-size: 10px;")
        main_layout.addWidget(footer_label)
    
    def create_new_project(self):
        """Open dialog to create a new project."""
        from .NewProjectWindow import NewProjectWindow
        
        dialog = NewProjectWindow(self)
        if dialog.exec() == NewProjectWindow.Accepted:
            project_path = dialog.get_project_path()
            project_name = dialog.get_project_name()
            
            if self.project_manager.create_new_project(project_path, project_name):
                QMessageBox.information(
                    self, 
                    "Project Created", 
                    f"Project '{project_name}' created successfully!\n\nPath: {project_path}"
                )
                self.project_selected.emit(project_path)
            else:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    "Failed to create project. Please check the folder path and try again."
                )
    
    def open_existing_project(self):
        """Open dialog to select an existing project."""
        project_folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if project_folder:
            # Check if it's a valid project folder
            config_path = os.path.join(project_folder, 'config.ini')
            if os.path.exists(config_path):
                if self.project_manager.load_project(project_folder):
                    QMessageBox.information(
                        self, 
                        "Project Loaded", 
                        f"Project loaded successfully!\n\nPath: {project_folder}"
                    )
                    self.project_selected.emit(project_folder)
                else:
                    QMessageBox.critical(
                        self, 
                        "Error", 
                        "Failed to load project. Please check the project folder."
                    )
            else:
                QMessageBox.warning(
                    self, 
                    "Invalid Project", 
                    "The selected folder does not appear to be a valid project folder.\n\nA project folder should contain a 'config.ini' file."
                )
    
    def get_project_manager(self):
        """Get the project manager instance."""
        return self.project_manager
