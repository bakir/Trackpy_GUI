"""
Export Helper Module

Description: Utility functions for exporting data files (CSV, pickle).
"""

import os
import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox


def export_data(parent, file_controller, source_filename, target_format):
    """
    Export data file to user-specified location.

    Parameters
    ----------
    parent : QWidget
        Parent widget for dialogs
    file_controller : FileController
        File controller instance
    source_filename : str
        Name of source file in data folder
    target_format : str
        Export format ('csv' or 'pkl')
    """
    if not file_controller:
        QMessageBox.warning(parent, "Error", "File controller not set.")
        return

    data_folder = file_controller.data_folder
    source_file_path = os.path.join(data_folder, source_filename)

    if not os.path.exists(source_file_path):
        QMessageBox.warning(
            parent,
            "Error",
            f"Could not find selected data file: {source_filename}",
        )
        return

    if target_format == "csv":
        file_filter = "CSV Files (*.csv);;All Files (*)"
    elif target_format == "pkl":
        file_filter = "Pickle Files (*.pkl);;All Files (*)"
    else:
        QMessageBox.critical(
            parent, "Error", f"Unsupported export format '{target_format}'"
        )
        return

    default_name = (
        f"{os.path.splitext(source_filename)[0]}_export.{target_format}"
    )
    save_path, _ = QFileDialog.getSaveFileName(
        parent,
        f"Export {target_format.upper()} Data",
        os.path.join(data_folder, default_name),
        file_filter,
    )

    if not save_path:
        return

    try:
        df = pd.read_csv(source_file_path)

        if target_format == "csv":
            df.to_csv(save_path, index=False)
        elif target_format == "pkl":
            df.to_pickle(save_path)

        QMessageBox.information(
            parent, "Success", f"Data successfully exported to: {save_path}"
        )

    except Exception as e:
        QMessageBox.critical(
            parent, "Export Error", f"An error occurred during export: {e}"
        )
