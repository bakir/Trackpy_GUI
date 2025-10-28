"""
File Controller Module

Description: Centralized file and folder management for the particle tracking application.
             Handles all file operations including cleanup, creation, and data management.
             Now supports project-specific folder structures.
"""

import os
import shutil
import pandas as pd
import configparser
from .config_parser import get_config


class FileController:
    """Centralized controller for all file and folder operations."""
    
    def __init__(self, project_manager=None):
        """Initialize the file controller with configuration."""
        self.project_manager = project_manager
        self._load_config()
    
    def _load_config(self):
        """Load configuration from project or global config."""
        if self.project_manager and self.project_manager.get_project_config():
            # Use project-specific config
            config_path = self.project_manager.get_project_config()
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Get project folder paths
            project_path = self.project_manager.get_project_path()
            
            if 'Paths' in config:
                self.particles_folder = os.path.join(project_path, config['Paths'].get('particles_folder', 'particles/'))
                self.original_frames_folder = os.path.join(project_path, config['Paths'].get('original_frames_folder', 'original_frames/'))
                self.annotated_frames_folder = os.path.join(project_path, config['Paths'].get('annotated_frames_folder', 'annotated_frames/'))
                self.rb_gallery_folder = os.path.join(project_path, config['Paths'].get('rb_gallery_folder', 'rb_gallery'))
                self.videos_folder = os.path.join(project_path, config['Paths'].get('videos_folder', 'videos/'))
                self.data_folder = os.path.join(project_path, config['Paths'].get('data_folder', 'data/'))
            else:
                # Fallback to default project structure
                self.particles_folder = os.path.join(project_path, 'particles')
                self.original_frames_folder = os.path.join(project_path, 'original_frames')
                self.annotated_frames_folder = os.path.join(project_path, 'annotated_frames')
                self.rb_gallery_folder = os.path.join(project_path, 'rb_gallery')
                self.videos_folder = os.path.join(project_path, 'videos')
                self.data_folder = os.path.join(project_path, 'data')
        else:
            # Use global config
            config = get_config()
            self.particles_folder = config.get('particles_folder', 'particles/')
            self.original_frames_folder = config.get('original_frames_folder', 'original_frames/')
            self.annotated_frames_folder = config.get('annotated_frames_folder', 'annotated_frames/')
            self.rb_gallery_folder = config.get('rb_gallery_folder', 'rb_gallery')
            self.videos_folder = config.get('videos_folder', 'videos/')
            self.data_folder = config.get('data_folder', 'data/')
    
    def set_project_manager(self, project_manager):
        """Set the project manager and reload configuration."""
        self.project_manager = project_manager
        self._load_config()
    
    def ensure_folder_exists(self, folder_path: str) -> None:
        """Ensure a folder exists, create it if it doesn't."""
        os.makedirs(folder_path, exist_ok=True)
    
    def delete_all_files_in_folder(self, folder_path: str) -> None:
        """Delete all files in a folder, keeping the folder structure."""
        if not os.path.exists(folder_path):
            return
        
        try:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        except Exception as e:
            print(f"Error cleaning folder {folder_path}: {e}")
    
    def cleanup_temp_folders(self) -> None:
        """Clean up all temporary folders."""
        temp_folders = [
            self.particles_folder,
            self.original_frames_folder,
            self.annotated_frames_folder,
            self.rb_gallery_folder
        ]
        
        print("Starting cleanup of temporary folders...")
        
        for folder in temp_folders:
            try:
                if os.path.exists(folder):
                    # Count files before cleanup
                    all_items = os.listdir(folder)
                    file_count = len([f for f in all_items if os.path.isfile(os.path.join(folder, f))])
                    dir_count = len([d for d in all_items if os.path.isdir(os.path.join(folder, d))])
                    print(f"Found {file_count} files and {dir_count} directories in {folder}")
                    
                    # Clean up the folder
                    self.delete_all_files_in_folder(folder)
                    
                    # Also clean up any subdirectories
                    for item in os.listdir(folder):
                        item_path = os.path.join(folder, item)
                        if os.path.isdir(item_path):
                            try:
                                shutil.rmtree(item_path)
                                print(f"Removed directory: {item_path}")
                            except Exception as e:
                                print(f"Error removing directory {item_path}: {e}")
                    
                    print(f"Successfully cleaned up {folder}")
                else:
                    print(f"Folder {folder} does not exist, skipping")
            except Exception as e:
                print(f"Error cleaning up {folder}: {e}")
        
        print("Cleanup completed.")
    
    def cleanup_rb_gallery(self) -> None:
        """Delete all files in the rb_gallery folder."""
        try:
            if os.path.exists(self.rb_gallery_folder):
                self.delete_all_files_in_folder(self.rb_gallery_folder)
                print("Cleaned up RB gallery folder")
        except Exception as e:
            print(f"Error cleaning up RB gallery: {e}")
    
    def save_particles_data(self, particles_df: pd.DataFrame, filename: str = "all_particles.csv") -> str:
        """Save particles data to the data folder."""
        self.ensure_folder_exists(self.data_folder)
        file_path = os.path.join(self.data_folder, filename)
        particles_df.to_csv(file_path, index=False)
        print(f"Saved particles data to: {file_path}")
        return file_path
    
    def save_trajectories_data(self, trajectories_df: pd.DataFrame, filename: str = "trajectories.csv") -> str:
        """Save trajectories data to the data folder."""
        self.ensure_folder_exists(self.data_folder)
        file_path = os.path.join(self.data_folder, filename)
        trajectories_df.to_csv(file_path, index=False)
        print(f"Saved trajectories data to: {file_path}")
        return file_path
    
    def load_particles_data(self, filename: str = "all_particles.csv") -> pd.DataFrame:
        """Load particles data from the data folder."""
        file_path = os.path.join(self.data_folder, filename)
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        else:
            print(f"Particles file not found: {file_path}")
            return pd.DataFrame()
    
    def load_trajectories_data(self, filename: str = "trajectories.csv") -> pd.DataFrame:
        """Load trajectories data from the data folder."""
        file_path = os.path.join(self.data_folder, filename)
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        else:
            print(f"Trajectories file not found: {file_path}")
            return pd.DataFrame()
    
    def save_errant_particle_image(self, image_data, filename: str) -> str:
        """Save an errant particle image to the particles folder."""
        self.ensure_folder_exists(self.particles_folder)
        file_path = os.path.join(self.particles_folder, filename)
        # This would need to be implemented based on the image data format
        # For now, just return the path
        return file_path
    
    def create_rb_gallery_folder(self) -> str:
        """Create and return the RB gallery folder path."""
        self.ensure_folder_exists(self.rb_gallery_folder)
        return self.rb_gallery_folder
    
    def get_frame_path(self, frame_index: int) -> str:
        """Get the path for a specific frame."""
        return os.path.join(self.original_frames_folder, f"frame_{frame_index:05d}.jpg")
    
    def get_annotated_frame_path(self, frame_index: int) -> str:
        """Get the path for a specific annotated frame."""
        return os.path.join(self.annotated_frames_folder, f"frame_{frame_index:05d}.jpg")
    
    def frame_exists(self, frame_index: int) -> bool:
        """Check if a frame exists."""
        return os.path.exists(self.get_frame_path(frame_index))
    
    def annotated_frame_exists(self, frame_index: int) -> bool:
        """Check if an annotated frame exists."""
        return os.path.exists(self.get_annotated_frame_path(frame_index))
    
    def get_total_frames_count(self) -> int:
        """Get the total number of frames in the original frames folder."""
        if not os.path.exists(self.original_frames_folder):
            return 0
        
        frame_files = [f for f in os.listdir(self.original_frames_folder) 
                      if f.startswith('frame_') and f.endswith('.jpg')]
        return len(frame_files)
    
    def export_data(self, source_filename: str, target_format: str, save_path: str) -> bool:
        """Export data from data folder to a user-specified location."""
        source_file_path = os.path.join(self.data_folder, source_filename)
        
        if not os.path.exists(source_file_path):
            print("Could not find selected data")
            return False
        
        try:
            # Read the source CSV with pandas
            df = pd.read_csv(source_file_path)
            
            if target_format == 'csv':
                # Save the DataFrame to a new CSV file, without the index column
                df.to_csv(save_path, index=False)
            elif target_format == 'pkl':
                # Save the DataFrame to a pickle file
                df.to_pickle(save_path)
            else:
                print(f"Error: Unsupported export format '{target_format}'")
                return False
            
            print(f"Data successfully exported to: {save_path}")
            return True
            
        except Exception as e:
            print(f"An error occurred during export: {e}")
            return False
