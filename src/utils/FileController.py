"""
File Controller Module

Description: Centralized file and folder management for the particle tracking application.
             Handles all file operations including cleanup, creation, and data management.
             Now uses dependency injection for configuration.
"""

import os
import shutil
import pandas as pd
from .ConfigManager import ConfigManager


class FileController:
    """Centralized controller for all file and folder operations."""

    def __init__(
        self, config_manager: ConfigManager, project_path: str = None
    ):
        """
        Initialize the file controller with configuration.

        Parameters
        ----------
        config_manager : ConfigManager
            Configuration manager instance
        project_path : str, optional
            Project root path for project-specific operations
        """
        self.config_manager = config_manager
        self.project_path = project_path
        self._load_paths()

    def _load_paths(self):
        """Load folder paths from configuration."""
        self.errant_particles_folder = self.config_manager.get_path(
            "errant_particles_folder", self.project_path
        )
        self.original_frames_folder = self.config_manager.get_path(
            "original_frames_folder", self.project_path
        )
        self.annotated_frames_folder = self.config_manager.get_path(
            "annotated_frames_folder", self.project_path
        )
        self.errant_distance_links_folder = self.config_manager.get_path(
            "errant_distance_links_folder", self.project_path
        )
        self.videos_folder = self.config_manager.get_path(
            "videos_folder", self.project_path
        )
        self.data_folder = self.config_manager.get_path(
            "data_folder", self.project_path
        )
        self.errant_memory_links_folder = self.config_manager.get_path(
            "errant_memory_links_folder", self.project_path
        )

    def set_project_path(self, project_path: str):
        """Set the project path and reload folder paths."""
        self.project_path = project_path
        self._load_paths()

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

    def cleanup_temp_folders(
        self, include_errant_particles: bool = False
    ) -> None:
        """Clean up temporary folders.

        Parameters
        ----------
        include_errant_particles : bool, optional
            When True, also clears the errant particle gallery folder. Defaults to False.
        """
        temp_folders = [self.errant_distance_links_folder]

        if include_errant_particles:
            temp_folders.append(self.errant_particles_folder)

        print("Starting cleanup of temporary folders...")

        for folder in temp_folders:
            try:
                if os.path.exists(folder):
                    # Count files before cleanup
                    all_items = os.listdir(folder)
                    file_count = len(
                        [
                            f
                            for f in all_items
                            if os.path.isfile(os.path.join(folder, f))
                        ]
                    )
                    dir_count = len(
                        [
                            d
                            for d in all_items
                            if os.path.isdir(os.path.join(folder, d))
                        ]
                    )
                    print(
                        f"Found {file_count} files and {dir_count} directories in {folder}"
                    )

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
                                print(
                                    f"Error removing directory {item_path}: {e}"
                                )

                    print(f"Successfully cleaned up {folder}")
                else:
                    print(f"Folder {folder} does not exist, skipping")
            except Exception as e:
                print(f"Error cleaning up {folder}: {e}")

        print("Cleanup completed.")

    def cleanup_errant_distance_links(self) -> None:
        """Delete all files in the errant_distance_links folder."""
        try:
            if os.path.exists(self.errant_distance_links_folder):
                self.delete_all_files_in_folder(self.errant_distance_links_folder)
                print("Cleaned up errant distance links folder")
        except Exception as e:
            print(f"Error cleaning up errant distance links: {e}")

    def save_particles_data(
        self, particles_df: pd.DataFrame, filename: str = "all_particles.csv"
    ) -> str:
        """Save particles data to the data folder."""
        self.ensure_folder_exists(self.data_folder)
        file_path = os.path.join(self.data_folder, filename)
        particles_df.to_csv(file_path, index=False)
        print(f"Saved particles data to: {file_path}")
        return file_path

    def save_trajectories_data(
        self, trajectories_df: pd.DataFrame, filename: str = "trajectories.csv"
    ) -> str:
        """Save trajectories data to the data folder."""
        self.ensure_folder_exists(self.data_folder)
        file_path = os.path.join(self.data_folder, filename)
        trajectories_df.to_csv(file_path, index=False)
        print(f"Saved trajectories data to: {file_path}")
        return file_path

    def load_particles_data(
        self, filename: str = "all_particles.csv"
    ) -> pd.DataFrame:
        """Load particles data from the data folder."""
        file_path = os.path.join(self.data_folder, filename)
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        else:
            print(f"Particles file not found: {file_path}")
            return pd.DataFrame()

    def load_trajectories_data(
        self, filename: str = "trajectories.csv"
    ) -> pd.DataFrame:
        """Load trajectories data from the data folder."""
        file_path = os.path.join(self.data_folder, filename)
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        else:
            print(f"Trajectories file not found: {file_path}")
            return pd.DataFrame()

    def create_errant_distance_links_folder(self) -> str:
        """Create and return the errant distance links folder path."""
        self.ensure_folder_exists(self.errant_distance_links_folder)
        return self.errant_distance_links_folder
    def get_frame_path(self, frame_index: int) -> str:
        """Get the path for a specific frame."""
        return os.path.join(
            self.original_frames_folder, f"frame_{frame_index:05d}.jpg"
        )

    def get_annotated_frame_path(self, frame_index: int) -> str:
        """Get the path for a specific annotated frame."""
        return os.path.join(
            self.annotated_frames_folder, f"frame_{frame_index:05d}.jpg"
        )

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

        frame_files = [
            f
            for f in os.listdir(self.original_frames_folder)
            if f.startswith("frame_") and f.endswith(".jpg")
        ]
        return len(frame_files)

    def get_all_frame_paths(self) -> list[str]:
        """Get a sorted list of all frame paths."""
        if not os.path.exists(self.original_frames_folder):
            return []

        frame_files = [
            os.path.join(self.original_frames_folder, f)
            for f in sorted(os.listdir(self.original_frames_folder))
            if f.startswith("frame_") and f.endswith(".jpg")
        ]
        return frame_files

    def get_frame_files(self, start=None, end=None, step=None):
        """Get a list of frame files, optionally filtered by range."""
        if not os.path.exists(self.original_frames_folder):
            return []

        all_files = sorted(os.listdir(self.original_frames_folder))
        
        frame_files = []
        for f in all_files:
            if f.startswith("frame_") and f.endswith(".jpg"):
                try:
                    frame_num = int(f.split('_')[-1].split('.')[0])
                    if (start is None or frame_num >= start) and \
                       (end is None or frame_num <= end):
                        frame_files.append(os.path.join(self.original_frames_folder, f))
                except (ValueError, IndexError):
                    continue
        
        if step is not None and step > 1:
            return frame_files[::step]
        
        return frame_files
