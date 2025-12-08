"""
File Controller Module

Description: Centralized file and folder management for the particle tracking application.
             Handles all file operations including cleanup, creation, and data management.
             Now uses dependency injection for configuration.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

import os
import shutil
import pandas as pd
from .ConfigManager import ConfigManager


class FileController:
    """Centralized controller for all file and folder operations."""

    def __init__(self, config_manager: ConfigManager, project_path: str = None):
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
        """
        Load folder paths from configuration.

        Returns
        -------
        None
        """
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
        self.videos_folder = self.config_manager.get_path("videos_folder", self.project_path)
        self.data_folder = self.config_manager.get_path("data_folder", self.project_path)
        self.errant_memory_links_folder = self.config_manager.get_path(
            "errant_memory_links_folder", self.project_path
        )

    def set_project_path(self, project_path: str):
        """
        Set the project path and reload folder paths.

        Parameters
        ----------
        project_path : str
            The project root path.

        Returns
        -------
        None
        """
        self.project_path = project_path
        self._load_paths()

    def ensure_folder_exists(self, folder_path: str) -> None:
        """
        Ensure a folder exists, create it if it doesn't.

        Parameters
        ----------
        folder_path : str
            Path to the folder to ensure exists.

        Returns
        -------
        None
        """
        os.makedirs(folder_path, exist_ok=True)

    def _delete_file_if_exists(self, file_path: str) -> None:
        """
        Delete a file if it exists to ensure clean overwrite.

        Parameters
        ----------
        file_path : str
            Path to the file to delete.

        Returns
        -------
        None
        """
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted existing file: {file_path}")
            except Exception as e:
                print(f"Warning: Could not delete existing file {file_path}: {e}")

    def delete_all_files_in_folder(self, folder_path: str) -> None:
        """
        Delete all files in a folder, keeping the folder structure.

        Parameters
        ----------
        folder_path : str
            Path to the folder to clean.

        Returns
        -------
        None
        """
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

    def cleanup_temp_folders(self, include_errant_particles: bool = False) -> None:
        """
        Clean up temporary folders.

        Parameters
        ----------
        include_errant_particles : bool, optional
            When True, also clears the errant particle gallery folder. Defaults to False.

        Returns
        -------
        None
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
                        [f for f in all_items if os.path.isfile(os.path.join(folder, f))]
                    )
                    dir_count = len(
                        [d for d in all_items if os.path.isdir(os.path.join(folder, d))]
                    )
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

    def cleanup_errant_distance_links(self) -> None:
        """
        Delete all files in the errant_distance_links folder.

        Returns
        -------
        None
        """
        try:
            if os.path.exists(self.errant_distance_links_folder):
                self.delete_all_files_in_folder(self.errant_distance_links_folder)
                print("Cleaned up errant distance links folder")
        except Exception as e:
            print(f"Error cleaning up errant distance links: {e}")

    def save_particles_data(
        self, particles_df: pd.DataFrame, filename: str = "all_particles.csv"
    ) -> str:
        """
        Save particles data to the data folder.

        Parameters
        ----------
        particles_df : pd.DataFrame
            DataFrame containing particle data to save.
        filename : str, optional
            Name of the file to save. Defaults to "all_particles.csv".

        Returns
        -------
        str
            Path to the saved file.
        """
        self.ensure_folder_exists(self.data_folder)
        file_path = os.path.join(self.data_folder, filename)
        # Delete existing file to ensure clean overwrite
        self._delete_file_if_exists(file_path)
        particles_df.to_csv(file_path, index=False)
        print(f"Saved particles data to: {file_path}")
        return file_path

    def save_trajectories_data(
        self, trajectories_df: pd.DataFrame, filename: str = "trajectories.csv"
    ) -> str:
        """
        Save trajectories data to the data folder.

        Parameters
        ----------
        trajectories_df : pd.DataFrame
            DataFrame containing trajectory data to save.
        filename : str, optional
            Name of the file to save. Defaults to "trajectories.csv".

        Returns
        -------
        str
            Path to the saved file.
        """
        self.ensure_folder_exists(self.data_folder)
        file_path = os.path.join(self.data_folder, filename)
        # Delete existing file to ensure clean overwrite
        self._delete_file_if_exists(file_path)
        trajectories_df.to_csv(file_path, index=False)
        print(f"Saved trajectories data to: {file_path}")
        return file_path

    def load_particles_data(self, filename: str = "all_particles.csv") -> pd.DataFrame:
        """
        Load particles data from the data folder.

        Parameters
        ----------
        filename : str, optional
            Name of the file to load. Defaults to "all_particles.csv".

        Returns
        -------
        pd.DataFrame
            Loaded particles data, or empty DataFrame if file doesn't exist.
        """
        file_path = os.path.join(self.data_folder, filename)
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        else:
            print(f"Particles file not found: {file_path}")
            return pd.DataFrame()

    def load_trajectories_data(self, filename: str = "trajectories.csv") -> pd.DataFrame:
        """
        Load trajectories data from the data folder.

        Parameters
        ----------
        filename : str, optional
            Name of the file to load. Defaults to "trajectories.csv".

        Returns
        -------
        pd.DataFrame
            Loaded trajectories data, or empty DataFrame if file doesn't exist.
        """
        file_path = os.path.join(self.data_folder, filename)
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        else:
            print(f"Trajectories file not found: {file_path}")
            return pd.DataFrame()

    def get_data_file_path(self, filename: str) -> str:
        """
        Get the full path to a file in the data folder.

        Parameters
        ----------
        filename : str
            Name of the file.

        Returns
        -------
        str
            Full path to the file in the data folder.
        """
        return os.path.join(self.data_folder, filename)

    def backup_particles_data(self, backup_filename: str = "old_all_particles.csv") -> bool:
        """
        Create a backup of the current particles data.

        Parameters
        ----------
        backup_filename : str, optional
            Name of the backup file. Defaults to "old_all_particles.csv".

        Returns
        -------
        bool
            True if backup was created successfully, False otherwise
        """
        try:
            all_particles_path = self.get_data_file_path("all_particles.csv")
            backup_path = self.get_data_file_path(backup_filename)

            if os.path.exists(all_particles_path):
                shutil.copyfile(all_particles_path, backup_path)
                print(f"Backed up particles data to: {backup_path}")
                return True
            return False
        except Exception as e:
            print(f"Error backing up particles data: {e}")
            return False

    def load_particles_data_from_path(self, external_path: str) -> pd.DataFrame:
        """
        Load particles data from an external file path (outside data folder).

        Parameters
        ----------
        external_path : str
            Full path to the CSV file to load

        Returns
        -------
        pd.DataFrame
            Loaded particles data, or empty DataFrame if file doesn't exist
        """
        if os.path.exists(external_path):
            try:
                return pd.read_csv(external_path)
            except Exception as e:
                print(f"Error loading particles data from {external_path}: {e}")
                return pd.DataFrame()
        else:
            print(f"Particles file not found: {external_path}")
            return pd.DataFrame()

    def save_to_save_folder(self, data: pd.DataFrame, filename: str) -> str:
        """
        Save data to the save folder (used for undo functionality).

        Parameters
        ----------
        data : pd.DataFrame
            Data to save
        filename : str
            Name of the file to save

        Returns
        -------
        str
            Path to the saved file
        """
        save_folder = os.path.join(self.data_folder, "save")
        self.ensure_folder_exists(save_folder)
        save_path = os.path.join(save_folder, filename)
        # Delete existing file to ensure clean overwrite
        self._delete_file_if_exists(save_path)
        data.to_csv(save_path, index=False)
        print(f"Saved to save folder: {save_path}")
        return save_path

    def load_from_save_folder(self, filename: str) -> pd.DataFrame:
        """
        Load data from the save folder (used for undo functionality).

        Parameters
        ----------
        filename : str
            Name of the file to load

        Returns
        -------
        pd.DataFrame
            Loaded data, or empty DataFrame if file doesn't exist
        """
        save_folder = os.path.join(self.data_folder, "save")
        save_path = os.path.join(save_folder, filename)
        if os.path.exists(save_path):
            try:
                return pd.read_csv(save_path)
            except Exception as e:
                print(f"Error loading from save folder {save_path}: {e}")
                return pd.DataFrame()
        else:
            return pd.DataFrame()

    def save_filtered_particles_data(
        self, filtered_df: pd.DataFrame, filename: str = "filtered_particles.csv"
    ) -> str:
        """
        Save filtered particles data to the data folder.

        Parameters
        ----------
        filtered_df : pd.DataFrame
            Filtered particles data
        filename : str, optional
            Name of the file. Defaults to "filtered_particles.csv".

        Returns
        -------
        str
            Path to the saved file
        """
        # save_particles_data already handles deletion, so just call it
        return self.save_particles_data(filtered_df, filename)

    def copy_file_to_save_folder(self, source_path: str, filename: str) -> str:
        """
        Copy a file to the save folder (used for undo functionality).

        Parameters
        ----------
        source_path : str
            Path to the source file
        filename : str
            Name to use in the save folder

        Returns
        -------
        str
            Path to the copied file
        """
        save_folder = os.path.join(self.data_folder, "save")
        self.ensure_folder_exists(save_folder)
        dest_path = os.path.join(save_folder, filename)
        if os.path.exists(source_path):
            # Delete existing file to ensure clean overwrite
            self._delete_file_if_exists(dest_path)
            shutil.copy2(source_path, dest_path)
            print(f"Copied to save folder: {dest_path}")
            return dest_path
        else:
            raise FileNotFoundError(f"Source file not found: {source_path}")

    def create_errant_distance_links_folder(self) -> str:
        """
        Create and return the errant distance links folder path.

        Returns
        -------
        str
            Path to the errant distance links folder.
        """
        self.ensure_folder_exists(self.errant_distance_links_folder)
        return self.errant_distance_links_folder

    def get_frame_path(self, frame_index: int) -> str:
        """
        Get the path for a specific frame.

        Parameters
        ----------
        frame_index : int
            Index of the frame (0-based).

        Returns
        -------
        str
            Path to the frame image file.
        """
        return os.path.join(self.original_frames_folder, f"frame_{frame_index:05d}.jpg")

    def get_annotated_frame_path(self, frame_index: int) -> str:
        """
        Get the path for a specific annotated frame.

        Parameters
        ----------
        frame_index : int
            Index of the frame (0-based).

        Returns
        -------
        str
            Path to the annotated frame image file.
        """
        return os.path.join(self.annotated_frames_folder, f"frame_{frame_index:05d}.jpg")

    def frame_exists(self, frame_index: int) -> bool:
        """
        Check if a frame exists.

        Parameters
        ----------
        frame_index : int
            Index of the frame to check (0-based).

        Returns
        -------
        bool
            True if the frame file exists, False otherwise.
        """
        return os.path.exists(self.get_frame_path(frame_index))

    def annotated_frame_exists(self, frame_index: int) -> bool:
        """
        Check if an annotated frame exists.

        Parameters
        ----------
        frame_index : int
            Index of the frame to check (0-based).

        Returns
        -------
        bool
            True if the annotated frame file exists, False otherwise.
        """
        return os.path.exists(self.get_annotated_frame_path(frame_index))

    def get_total_frames_count(self) -> int:
        """
        Get the total number of frames in the original frames folder.

        Returns
        -------
        int
            Total number of frame files found.
        """
        if not os.path.exists(self.original_frames_folder):
            return 0

        frame_files = [
            f
            for f in os.listdir(self.original_frames_folder)
            if f.startswith("frame_") and f.endswith(".jpg")
        ]
        return len(frame_files)

    def get_all_frame_paths(self) -> list[str]:
        """
        Get a sorted list of all frame paths.

        Returns
        -------
        list[str]
            Sorted list of paths to all frame files.
        """
        if not os.path.exists(self.original_frames_folder):
            return []

        frame_files = [
            os.path.join(self.original_frames_folder, f)
            for f in sorted(os.listdir(self.original_frames_folder))
            if f.startswith("frame_") and f.endswith(".jpg")
        ]
        return frame_files

    def get_frame_files(self, start=None, end=None, step=None):
        """
        Get a list of frame files, optionally filtered by range.

        Parameters
        ----------
        start : int, optional
            Starting frame index (inclusive). If None, starts from beginning.
        end : int, optional
            Ending frame index (inclusive). If None, goes to end.
        step : int, optional
            Step size between frames. If None, returns all frames in range.

        Returns
        -------
        list
            List of frame file paths matching the criteria.
        """
        if not os.path.exists(self.original_frames_folder):
            return []

        all_files = sorted(os.listdir(self.original_frames_folder))

        frame_files = []
        for f in all_files:
            if f.startswith("frame_") and f.endswith(".jpg"):
                try:
                    frame_num = int(f.split("_")[-1].split(".")[0])
                    if (start is None or frame_num >= start) and (end is None or frame_num <= end):
                        frame_files.append(os.path.join(self.original_frames_folder, f))
                except (ValueError, IndexError):
                    continue

        if step is not None and step > 1:
            return frame_files[::step]

        return frame_files
