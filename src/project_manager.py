"""
Project Manager Module

Description: Handles project creation, management, and configuration.
             Each project has its own folder structure and config file.
"""

import os
import shutil
from .config_manager import ConfigManager


class ProjectManager:
    """Manages particle tracking projects with isolated folder structures."""
    
    def __init__(self):
        """Initialize the project manager."""
        self.current_project_path = None
        self.current_project_config = None
    
    def create_new_project(self, project_folder_path: str, project_name: str = None) -> bool:
        """
        Create a new project with folder structure and config file.
        
        Parameters
        ----------
        project_folder_path : str
            Path where the project folder will be created
        project_name : str, optional
            Name of the project. If None, uses folder name.
            
        Returns
        -------
        bool
            True if project was created successfully, False otherwise
        """
        try:
            # Create project folder
            os.makedirs(project_folder_path, exist_ok=True)
            
            # Set project name
            if project_name is None:
                project_name = os.path.basename(project_folder_path)
            
            # Create project subfolders
            folders = [
                'particles',
                'original_frames', 
                'annotated_frames',
                'rb_gallery',
                'data',
                'videos'
            ]
            
            for folder in folders:
                folder_path = os.path.join(project_folder_path, folder)
                os.makedirs(folder_path, exist_ok=True)
            
            # Copy template config to project folder
            template_config_path = os.path.join(os.path.dirname(__file__), '..', 'template_config.ini')
            project_config_path = os.path.join(project_folder_path, 'config.ini')
            
            if os.path.exists(template_config_path):
                shutil.copy2(template_config_path, project_config_path)
                
                # Update paths in project config to be relative to project folder
                self._update_project_config_paths(project_config_path, project_folder_path)
            else:
                # Create default config if template doesn't exist
                self._create_default_project_config(project_config_path, project_folder_path)
            
            # Create project info file
            self._create_project_info(project_folder_path, project_name)
            
            print(f"Project '{project_name}' created successfully at: {project_folder_path}")
            return True
            
        except Exception as e:
            print(f"Error creating project: {e}")
            return False
    
    def load_project(self, project_folder_path: str) -> bool:
        """
        Load an existing project.
        
        Parameters
        ----------
        project_folder_path : str
            Path to the project folder
            
        Returns
        -------
        bool
            True if project was loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(project_folder_path):
                print(f"Project folder does not exist: {project_folder_path}")
                return False
            
            project_config_path = os.path.join(project_folder_path, 'config.ini')
            if not os.path.exists(project_config_path):
                print(f"Project config file not found: {project_config_path}")
                return False
            
            self.current_project_path = project_folder_path
            self.current_project_config = project_config_path
            
            print(f"Project loaded successfully: {project_folder_path}")
            return True
            
        except Exception as e:
            print(f"Error loading project: {e}")
            return False
    
    def get_project_config(self) -> str:
        """Get the path to the current project's config file."""
        return self.current_project_config
    
    def get_project_path(self) -> str:
        """Get the path to the current project folder."""
        return self.current_project_path
    
    def get_project_folders(self) -> dict:
        """Get all project folder paths."""
        if not self.current_project_path:
            return {}
        
        return {
            'particles': os.path.join(self.current_project_path, 'particles'),
            'original_frames': os.path.join(self.current_project_path, 'original_frames'),
            'annotated_frames': os.path.join(self.current_project_path, 'annotated_frames'),
            'rb_gallery': os.path.join(self.current_project_path, 'rb_gallery'),
            'data': os.path.join(self.current_project_path, 'data'),
            'videos': os.path.join(self.current_project_path, 'videos')
        }
    
    def _update_project_config_paths(self, config_path: str, project_path: str):
        """Update config file paths to be absolute paths relative to project folder."""
        import configparser
        
        config = configparser.ConfigParser()
        config.read(config_path)
        
        # Update paths to be absolute paths relative to project folder
        if 'Paths' in config:
            config['Paths']['particles_folder'] = os.path.abspath(os.path.join(project_path, 'particles'))
            config['Paths']['original_frames_folder'] = os.path.abspath(os.path.join(project_path, 'original_frames'))
            config['Paths']['annotated_frames_folder'] = os.path.abspath(os.path.join(project_path, 'annotated_frames'))
            config['Paths']['rb_gallery_folder'] = os.path.abspath(os.path.join(project_path, 'rb_gallery'))
            config['Paths']['data_folder'] = os.path.abspath(os.path.join(project_path, 'data'))
            config['Paths']['videos_folder'] = os.path.abspath(os.path.join(project_path, 'videos'))
        
        with open(config_path, 'w') as f:
            config.write(f)
    
    def _create_default_project_config(self, config_path: str, project_path: str):
        """Create a default config file for the project with absolute paths."""
        import configparser
        
        config = configparser.ConfigParser()
        
        # Paths section with absolute paths
        config['Paths'] = {
            'particles_folder': os.path.abspath(os.path.join(project_path, 'particles')),
            'original_frames_folder': os.path.abspath(os.path.join(project_path, 'original_frames')),
            'annotated_frames_folder': os.path.abspath(os.path.join(project_path, 'annotated_frames')),
            'rb_gallery_folder': os.path.abspath(os.path.join(project_path, 'rb_gallery')),
            'data_folder': os.path.abspath(os.path.join(project_path, 'data')),
            'videos_folder': os.path.abspath(os.path.join(project_path, 'videos'))
        }
        
        # Detection section
        config['Detection'] = {
            'feature_size': '27',
            'min_mass': '1300.0',
            'invert': 'false',
            'threshold': '0.0',
            'frame_idx': '0'
        }
        
        # Linking section
        config['Linking'] = {
            'search_range': '10',
            'memory': '10',
            'min_trajectory_length': '10',
            'fps': '30.0',
            'scaling': '1.0',
            'max_speed': '100.0'
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
    
    def _create_project_info(self, project_path: str, project_name: str):
        """Create a project info file."""
        info_content = f"""# Project Information
Project Name: {project_name}
Created: {os.path.basename(project_path)}
Path: {project_path}

# Folder Structure
- particles/: Particle images and cropped regions
- original_frames/: Extracted video frames
- annotated_frames/: Frames with particle annotations
- rb_gallery/: Red-blue overlay images for trajectory validation
- data/: CSV and pickle data files
- videos/: Video files for analysis
- config.ini: Project-specific configuration
"""
        
        info_path = os.path.join(project_path, 'README.md')
        with open(info_path, 'w') as f:
            f.write(info_content)
    
    def list_recent_projects(self, max_projects: int = 5) -> list:
        """List recent projects (placeholder for future implementation)."""
        # This could be implemented to track recent projects
        # For now, return empty list
        return []
    
    def close_project(self):
        """Close the current project."""
        self.current_project_path = None
        self.current_project_config = None
        print("Project closed")
