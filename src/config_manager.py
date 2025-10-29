"""
Config Manager Module

Description: Centralized configuration management with dependency injection.
             Handles both global template config and project-specific configs.
"""

import os
import configparser
from typing import Dict, Any, Optional


class ConfigManager:
    """Centralized configuration manager with dependency injection support."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the config manager.
        
        Parameters
        ----------
        config_path : str, optional
            Path to the config file. If None, uses template config.
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """Load the configuration from file."""
        if self.config_path and os.path.exists(self.config_path):
            # Load project-specific config
            self.config.read(self.config_path)
        else:
            # Load template config
            template_path = os.path.join(os.path.dirname(__file__), '..', 'template_config.ini')
            if os.path.exists(template_path):
                self.config.read(template_path)
            else:
                # Create default config if template doesn't exist
                self._create_default_config()
    
    def _create_default_config(self):
        """Create a default configuration."""
        self.config['Paths'] = {
            'particles_folder': 'particles/',
            'original_frames_folder': 'original_frames/',
            'annotated_frames_folder': 'annotated_frames/',
            'rb_gallery_folder': 'rb_gallery/',
            'data_folder': 'data/',
            'videos_folder': 'videos/'
        }
        
        self.config['Detection'] = {
            'feature_size': '27',
            'min_mass': '1300.0',
            'invert': 'false',
            'threshold': '0.0',
            'frame_idx': '0'
        }
        
        self.config['Linking'] = {
            'search_range': '10',
            'memory': '10',
            'min_trajectory_length': '10',
            'fps': '30.0',
            'scaling': '1.0',
            'max_speed': '100.0'
        }
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        Get a configuration value.
        
        Parameters
        ----------
        section : str
            Configuration section name
        key : str
            Configuration key name
        fallback : Any, optional
            Fallback value if key not found
            
        Returns
        -------
        Any
            Configuration value
        """
        try:
            return self.config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_section(self, section: str) -> Dict[str, str]:
        """
        Get all values from a configuration section.
        
        Parameters
        ----------
        section : str
            Configuration section name
            
        Returns
        -------
        Dict[str, str]
            Dictionary of key-value pairs
        """
        try:
            return dict(self.config[section])
        except KeyError:
            return {}
    
    def set(self, section: str, key: str, value: str):
        """
        Set a configuration value.
        
        Parameters
        ----------
        section : str
            Configuration section name
        key : str
            Configuration key name
        value : str
            Value to set
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
    
    def save(self, path: Optional[str] = None):
        """
        Save configuration to file.
        
        Parameters
        ----------
        path : str, optional
            Path to save config. If None, uses current config_path.
        """
        save_path = path or self.config_path
        if save_path:
            with open(save_path, 'w') as f:
                self.config.write(f)
    
    def get_path(self, path_key: str, project_path: Optional[str] = None) -> str:
        """
        Get a path from configuration, always returning absolute paths.
        
        Parameters
        ----------
        path_key : str
            Path configuration key (e.g., 'particles_folder')
        project_path : str, optional
            Project root path. If provided, returns absolute path relative to project.
            
        Returns
        -------
        str
            Absolute path string
        """
        path_value = self.get('Paths', path_key, '')
        
        if project_path and path_value:
            # Return absolute path relative to project
            abs_path = os.path.abspath(os.path.join(project_path, path_value))
            return abs_path
        elif path_value:
            # Return absolute path from current working directory
            abs_path = os.path.abspath(path_value)
            return abs_path
        else:
            # Return empty string if no path configured
            return ""
    
    def get_detection_params(self) -> Dict[str, Any]:
        """Get detection parameters as a dictionary."""
        return {
            'feature_size': int(self.get('Detection', 'feature_size', 27)),
            'min_mass': float(self.get('Detection', 'min_mass', 1300.0)),
            'invert': self.get('Detection', 'invert', 'false').lower() == 'true',
            'threshold': float(self.get('Detection', 'threshold', 0.0)),
            'frame_idx': int(self.get('Detection', 'frame_idx', 0))
        }
    
    def get_linking_params(self) -> Dict[str, Any]:
        """Get linking parameters as a dictionary."""
        return {
            'search_range': int(self.get('Linking', 'search_range', 10)),
            'memory': int(self.get('Linking', 'memory', 10)),
            'min_trajectory_length': int(self.get('Linking', 'min_trajectory_length', 10)),
            'fps': float(self.get('Linking', 'fps', 30.0)),
            'scaling': float(self.get('Linking', 'scaling', 1.0)),
            'max_speed': float(self.get('Linking', 'max_speed', 100.0))
        }
    
    def save_detection_params(self, params: Dict[str, Any]):
        """Save detection parameters."""
        for key, value in params.items():
            self.set('Detection', key, str(value))
        self.save()
    
    def save_linking_params(self, params: Dict[str, Any]):
        """Save linking parameters."""
        for key, value in params.items():
            self.set('Linking', key, str(value))
        self.save()
    
    def is_project_config(self) -> bool:
        """Check if this is a project-specific config."""
        return self.config_path is not None and os.path.exists(self.config_path)
    
    def get_config_type(self) -> str:
        """Get the type of config (template or project)."""
        if self.is_project_config():
            return "project"
        else:
            return "template"
