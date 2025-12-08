"""
Graphing Utilities Module

Description: Base classes and utilities for graphing widgets used in both
             ParticleDetectionWindow and TrajectoryLinkingWindow.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMenu,
    QApplication,
)
from PySide6.QtGui import QAction, QPixmap, QPalette, QColor
from PySide6.QtCore import Qt
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import os
from copy import copy
from . import ParticleProcessing
import sys
import io
from .ScaledLabel import ScaledLabel
from PySide6.QtGui import QGuiApplication
import trackpy as tp
import cv2
import pandas as pd

# Universal graphing label sizes and figure formatting - larger fonts for better visibility
matplotlib.rc("xtick", labelsize=18)
matplotlib.rc("ytick", labelsize=18)
matplotlib.rc("axes", titlesize=22, labelsize=20)
matplotlib.rc("figure", titlesize=26)


class GraphingButton(QPushButton):
    """Button for graphing controls with highlight state management."""

    highlighted_button = None  # Keeps track of which button is currently highlighted

    def __init__(self, text, parent=None):
        """Initialize graphing button.

        Parameters
        ----------
        text : str
            Button text label
        parent : QWidget, optional
            Parent widget
        """
        super(GraphingButton, self).__init__(text, parent)
        # Use native button styling - no custom stylesheets

    def switch_button_color(self):
        """Track which button is highlighted (using native button states)."""

        if self.highlighted_button != None:
            # Reset previous button to normal state
            prev_button = self.highlighted_button
            prev_button.setDown(False)
            prev_button.setChecked(False)

        # Updates the button that is highlighted - use native checked state
        GraphingButton.highlighted_button = self
        self.setChecked(True)


class GraphingPanelWidget(QWidget):
    """Base widget for graphing panels with matplotlib integration."""

    def __init__(self, parent=None):
        """Initialize graphing panel widget.

        Parameters
        ----------
        parent : QWidget, optional
            Parent widget
        """
        super().__init__(parent)

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget.

        Parameters
        ----------
        config_manager : ConfigManager
            Configuration manager instance
        """
        self.config_manager = config_manager

    def set_file_controller(self, file_controller):
        """Set the file controller for this widget.

        Parameters
        ----------
        file_controller : FileController
            File controller instance
        """
        self.file_controller = file_controller

    def setup_plot_display(self):
        """Create the starting graphing area display."""
        self.config_manager = None
        self.file_controller = None
        # Either particle data or trajectory data
        self.data = None

        # Graph area
        self.layout = QVBoxLayout(self)
        self.fig = None

        self.plot_label = ScaledLabel("No plot to display.")
        self.plot_label.setAlignment(Qt.AlignCenter)
        # Give the plot label maximum space - use stretch factor 20 to make it fill the screen
        self.layout.addWidget(self.plot_label, 20)
        self.blank_plot()

    def blank_plot(self):
        """Clear the plot display."""
        if hasattr(self, "plot_label"):
            self.plot_label.setPixmap(QPixmap())

    def check_for_empty_data(self):
        """Check if data has been found.

        Returns
        -------
        None
            If data is empty or None
        """
        # Return None if nothing was found
        if self.data is None or self.data.empty:
            print("No particles detected in the selected frame.")
            return None

    def self_plot(self, plotting_function, button, page=None):
        """Draw a plot to the canvas in the widget.

        Parameters
        ----------
        plotting_function : callable
            Function that returns a matplotlib figure
        button : GraphingButton
            Button associated with this plot
        page : str, optional
            Page identifier ('detection' or 'trajectory')
        """
        # Get figure
        new_fig = plotting_function(page)

        # Close old figure
        if self.fig and self.fig is not new_fig:
            plt.close(self.fig)

        # Handle error/no particles case
        if new_fig is None:
            self.blank_plot()
            return

        # Assign new figure and render it to a pixmap
        self.fig = new_fig

        # Get the actual widget size to generate plot at matching resolution
        widget_width = self.plot_label.width()
        widget_height = self.plot_label.height()

        # If widget hasn't been sized yet, use a reasonable default
        # This can happen on first plot before widget is shown
        if widget_width <= 0 or widget_height <= 0:
            widget_width = 800
            widget_height = 600

        # Account for device pixel ratio for high-DPI displays
        # This ensures the image looks sharp on retina/high-DPI screens
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                device_pixel_ratio = screen.devicePixelRatio()
            else:
                device_pixel_ratio = 1.0
        except:
            device_pixel_ratio = 1.0

        # Calculate target resolution based on actual widget size
        # Use device pixel ratio to ensure sharpness on high-DPI displays
        target_width_px = int(widget_width * device_pixel_ratio)
        target_height_px = int(widget_height * device_pixel_ratio)

        # Use a reasonable DPI - 100 DPI is standard for screen display
        # Higher DPI would make the image larger than needed
        target_dpi = 100

        # Calculate figure size in inches based on target resolution
        width_inches = target_width_px / target_dpi
        height_inches = target_height_px / target_dpi

        # Resize the figure to the calculated size
        self.fig.set_size_inches(width_inches, height_inches)

        # Improve figure formatting - better spacing and layout
        self.fig.tight_layout(pad=1.2)

        # Generate at resolution matching widget size
        buf = io.BytesIO()
        self.fig.savefig(
            buf,
            format="png",
            pad_inches=0.15,
            dpi=target_dpi,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        buf.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue(), "png")

        self.plot_label.setPixmap(pixmap)

        # Switch button color
        button.switch_button_color()

    def filtering_buttons(self, button_layout, page):
        """Set up the buttons for the filtering plots.

        Parameters
        ----------
        button_layout : QHBoxLayout
            Layout to add buttons to
        page : str
            Page identifier ('detection' or 'trajectory')
        """
        self.filter = QWidget()
        self.filter_layout = QVBoxLayout(self.filter)
        self.filter_label = QLabel("Filtering")
        self.filter_layout.addWidget(self.filter_label, alignment=Qt.AlignTop)

        self.mass_ecc_button = GraphingButton(text="Mass vs Eccentricity", parent=self)
        self.mass_ecc_button.clicked.connect(
            lambda: self.self_plot(self.get_mass_ecc, self.mass_ecc_button, page)
        )
        self.filter_layout.addWidget(self.mass_ecc_button, alignment=Qt.AlignTop)

        self.mass_size_button = GraphingButton(text="Mass vs Size", parent=self)
        self.mass_size_button.clicked.connect(
            lambda: self.self_plot(self.get_mass_size, self.mass_size_button, page)
        )
        self.filter_layout.addWidget(self.mass_size_button, alignment=Qt.AlignTop)

        self.size_ecc_button = GraphingButton(text="Size vs Eccentricity", parent=self)
        self.size_ecc_button.clicked.connect(
            lambda: self.self_plot(self.get_size_ecc, self.size_ecc_button, page)
        )
        self.filter_layout.addWidget(self.size_ecc_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.filter)
        self.filter_layout.addStretch(1)

    def get_mass_size(self, page):
        """Create a scatterplot of mass vs size.

        Parameters
        ----------
        page : str
            Page identifier ('detection' or 'trajectory')

        Returns
        -------
        Figure or None
            Matplotlib figure or None on error
        """
        try:
            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            fig, ax = plt.subplots()
            if page == "detection":
                tp.mass_size(self.data, ax=ax)
            else:
                tp.mass_size(self.data.groupby(["particle"]).mean(), ax=ax)

            ax.set_xlabel("Mass")
            ax.set_ylabel("Size")

            temp_fig = plt.gcf()
            temp_fig.suptitle("Mass vs Size")

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def get_mass_ecc(self, page):
        """Create a scatterplot of mass vs eccentricity.

        Parameters
        ----------
        page : str
            Page identifier ('detection' or 'trajectory')

        Returns
        -------
        Figure or None
            Matplotlib figure or None on error
        """
        try:
            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            fig, ax = plt.subplots()
            if page == "detection":
                tp.mass_ecc(self.data, ax=ax)
            else:
                tp.mass_ecc(self.data.groupby(["particle"]).mean(), ax=ax)

            ax.set_xlabel("Mass")
            ax.set_ylabel("Eccentricity")

            temp_fig = plt.gcf()
            temp_fig.suptitle("Mass vs Eccentricity")

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def get_size_ecc(self, page):
        """Create a scatterplot of size vs eccentricity.

        Parameters
        ----------
        page : str
            Page identifier ('detection' or 'trajectory')

        Returns
        -------
        Figure or None
            Matplotlib figure or None on error
        """
        try:
            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            fig, ax = plt.subplots()
            if page == "detection":
                ax.plot(self.data["size"], self.data["ecc"], "ko", alpha=0.1)
            else:
                grouped_data = self.data.groupby(["particle"]).mean()
                ax.plot(grouped_data["size"], grouped_data["ecc"], "ko", alpha=0.1)

            ax.set_xlabel("Size")
            ax.set_ylabel("Eccentricity")

            temp_fig = plt.gcf()
            temp_fig.suptitle("Size vs Eccentricity")

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None
