"""
Graphing Utilities Module

Description: Base classes and utilities for graphing widgets used in both
             ParticleDetectionWindow and TrajectoryLinkingWindow.
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMenu,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import os
from copy import copy
from .. import particle_processing

TARGET_WIDTH_PX = 500
TARGET_HEIGHT_PX = 400
STANDARD_DPI = 100

# Universal grphing label sizes
matplotlib.rc('xtick', labelsize=20) 
matplotlib.rc('ytick', labelsize=20)
matplotlib.rc('axes', titlesize=22, labelsize=22)
matplotlib.rc('figure', titlesize=25, figsize=(10, 8), dpi=STANDARD_DPI)

class GraphingButton(QPushButton):
    """Button for graphing controls with highlight state management."""

    highlighted_button = None  # Keeps track of which button is currently blue

    def __init__(self, text, parent=None):
        """Initialize graphing button.

        Parameters
        ----------
        text : str
            Button text label
        parent : QWidget, optional
            Parent widget
        """
        super(GraphingButton, self).__init__()
        self.setText(text)

    def switch_button_color(self):
        """Track which button is highlighted (styling removed, keeping logic)."""
        # Keep the tracking logic but remove visual styling
        # The button state is tracked for functional purposes
        GraphingButton.highlighted_button = self


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

    def get_figure_size_inches(self):
        """Calculate the necessary figure size in inches.

        Returns
        -------
        tuple
            (width, height) in inches
        """
        width_in = TARGET_WIDTH_PX / STANDARD_DPI
        height_in = TARGET_HEIGHT_PX / STANDARD_DPI
        return (width_in, height_in)

    def set_up_canvas(self):
        """Create the starting graphing area canvas."""
        self.config_manager = None
        self.file_controller = None
        # Either particle data or trajectory data
        self.data = None

        # Graph area
        self.layout = QVBoxLayout(self)
        self.fig = None
        self.blank_plot

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # Add stretch above the canvas for vertical centering
        self.layout.addStretch(1)
        # Center the canvas in the layout
        self.layout.addWidget(self.canvas, alignment=Qt.AlignCenter)

    def blank_plot(self):
        """Create a new blank figure with the correct size."""
        fig_size = self.get_figure_size_inches()

        if self.fig:
            plt.close(self.fig)

        # Ensure the blank figure is created with the target size properties
        self.fig = Figure()
        ax = self.fig.add_subplot(111)
        ax.set_axis_off()

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
            self.canvas.draw()
            return

        # Assign new figure and redraw canvas
        self.fig = new_fig
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)
        self.canvas.figure = self.fig
        self.canvas.draw()

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

        self.mass_ecc_button = GraphingButton(
            text="Plot Mass vs Eccentricity", parent=self
        )
        self.mass_ecc_button.clicked.connect(
            lambda: self.self_plot(
                self.get_mass_ecc, self.mass_ecc_button, page
            )
        )
        self.filter_layout.addWidget(
            self.mass_ecc_button, alignment=Qt.AlignTop
        )

        self.mass_size_button = GraphingButton(
            text="Plot Mass vs Size", parent=self
        )
        self.mass_size_button.clicked.connect(
            lambda: self.self_plot(
                self.get_mass_size, self.mass_size_button, page
            )
        )
        self.filter_layout.addWidget(
            self.mass_size_button, alignment=Qt.AlignTop
        )

        self.size_ecc_button = GraphingButton(
            text="Plot Size vs Eccentricity", parent=self
        )
        self.size_ecc_button.clicked.connect(
            lambda: self.self_plot(
                self.get_size_ecc, self.size_ecc_button, page
            )
        )
        self.filter_layout.addWidget(
            self.size_ecc_button, alignment=Qt.AlignTop
        )

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
            import trackpy as tp
            import cv2
            import pandas as pd

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
            import trackpy as tp
            import cv2
            import pandas as pd

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
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            fig, ax = plt.subplots()
            if page == "detection":
                ax.plot(self.data["size"], self.data["ecc"], "ko", alpha=0.1)
            else:
                grouped_data = self.data.groupby(["particle"]).mean()
                ax.plot(
                    grouped_data["size"], grouped_data["ecc"], "ko", alpha=0.1
                )

            ax.set_xlabel("Size")
            ax.set_ylabel("Eccentricity")

            temp_fig = plt.gcf()
            temp_fig.suptitle("Size vs Eccentricity")

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None
