"""
Graphing Panel showing subpixel bias

Description: Graphing panel showing the subpixel bias of all particles based on current tracking parameters.

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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from .. import particle_processing
import os
from copy import copy

TARGET_WIDTH_PX = 500
TARGET_HEIGHT_PX = 400
STANDARD_DPI = 100


class GraphingPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self.file_controller = None
        self.particles = None

        # Graph area
        self.layout = QVBoxLayout(self)
        self.fig = None
        self.highlighted_button = None
        self.blank_plot("beginning")

        self.canvas = FigureCanvas(self.fig)

        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # Add stretch above the canvas for vertical centering
        self.layout.addStretch(1)
        # Center the canvas in the layout
        self.layout.addWidget(self.canvas, alignment=Qt.AlignCenter)

        # buttons
        self.graphing_buttons = QWidget()
        self.button_layout = QHBoxLayout(self.graphing_buttons)

        # subpixel bias
        self.sb = QWidget()
        self.sb_layout = QVBoxLayout(self.sb)
        self.sb_label = QLabel("Subpixel Bias")
        self.sb_layout.addWidget(self.sb_label, alignment=Qt.AlignTop)

        self.sb_button = QPushButton(text="Plot Subpixel Bias", parent=self)
        self.sb_button.clicked.connect(self.plot_sb)
        self.sb_layout.addWidget(self.sb_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.sb)
        self.sb_layout.addStretch(1)

        # filtering
        self.filter = QWidget()
        self.filter_layout = QVBoxLayout(self.filter)
        self.filter_label = QLabel("Filtering")
        self.filter_layout.addWidget(self.filter_label, alignment=Qt.AlignTop)

        self.mass_ecc_button = QPushButton(
            text="Plot Mass vs Eccentricity", parent=self
        )
        self.mass_ecc_button.clicked.connect(self.plot_mass_ecc)
        self.filter_layout.addWidget(self.mass_ecc_button, alignment=Qt.AlignTop)

        self.mass_size_button = QPushButton(text="Plot Mass vs Size", parent=self)
        self.mass_size_button.clicked.connect(self.plot_mass_size)
        self.filter_layout.addWidget(self.mass_size_button, alignment=Qt.AlignTop)

        self.size_ecc_button = QPushButton(
            text="Plot Size vs Eccentricity", parent=self
        )
        self.size_ecc_button.clicked.connect(self.plot_size_ecc)
        self.filter_layout.addWidget(self.size_ecc_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.filter)
        self.filter_layout.addStretch(1)

        # histograms
        self.hist = QWidget()
        self.hist_layout = QVBoxLayout(self.hist)
        self.hist_label = QLabel("Histograms")
        self.hist_layout.addWidget(self.hist_label, alignment=Qt.AlignTop)

        self.ecc_button = QPushButton(text="Plot Eccentricity", parent=self)
        self.ecc_button.clicked.connect(self.plot_ecc)
        self.hist_layout.addWidget(self.ecc_button, alignment=Qt.AlignTop)

        self.mass_button = QPushButton(text="Plot Mass", parent=self)
        self.mass_button.clicked.connect(self.plot_mass)
        self.hist_layout.addWidget(self.mass_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.hist)
        self.hist_layout.addStretch(1)

        # self.hist = QPushButton(text = "Histograms", parent = self)

        # self.ecc_hist = QAction("Eccentricity", self)
        # self.ecc_hist.triggered.connect(self.plot_ecc)
        # self.mass_hist = QAction("Mass", self)
        # self.mass_hist.triggered.connect(self.plot_mass)

        # self.hist_menu = QMenu(self)
        # self.hist_menu.addAction(self.ecc_hist)
        # self.hist_menu.addAction(self.mass_hist)

        # self.hist.setMenu(self.hist_menu)
        # self.button_layout.addWidget(self.hist, alignment = Qt.AlignLeft)

        # self.filter = QPushButton(text = "Filtering", parent = self)

        # self.mass_size = QAction("Mass vs Size", self)
        # self.mass_size.triggered.connect(self.plot_mass_size)
        # self.mass_ecc = QAction("Mass vs Eccentricity", self)
        # self.mass_ecc.triggered.connect(self.plot_mass_ecc)
        # self.size_ecc = QAction("Size vs Eccentricity", self)
        # self.size_ecc.triggered.connect(self.plot_size_ecc)

        # self.filter_menu = QMenu(self)
        # self.filter_menu.addAction(self.mass_ecc)
        # self.filter_menu.addAction(self.mass_size)
        # self.filter_menu.addAction(self.size_ecc)

        # self.filter.setMenu(self.filter_menu)
        # self.button_layout.addWidget(self.filter, alignment = Qt.AlignLeft)

        # self.ecc_button = QPushButton(text = "Plot Eccentricity", parent = self)
        # self.ecc_button.clicked.connect(self.plot_ecc)
        # self.button_layout.addWidget(self.ecc_button, alignment=Qt.AlignLeft)

        # self.mass_size_button = QPushButton(text = "Plot Mass", parent = self)
        # self.mass_size_button.clicked.connect(self.plot_mass)
        # self.button_layout.addWidget(self.mass_size_button, alignment=Qt.AlignLeft)

        # self.mass_size_button = QPushButton(text = "Plot Mass vs Size", parent = self)
        # self.mass_size_button.clicked.connect(self.plot_mass_size)
        # self.button_layout.addWidget(self.mass_size_button, alignment=Qt.AlignLeft)

        # self.mass_ecc_button = QPushButton(text = "Plot Mass vs Eccentricity", parent = self)
        # self.mass_ecc_button.clicked.connect(self.plot_mass_ecc)
        # self.button_layout.addWidget(self.mass_ecc_button, alignment=Qt.AlignLeft)

        # self.size_ecc_button = QPushButton(text = "Plot Size vs Eccentricity", parent = self)
        # self.size_ecc_button.clicked.connect(self.plot_size_ecc)
        # self.button_layout.addWidget(self.size_ecc_button, alignment=Qt.AlignLeft)

        self.layout.addWidget(self.graphing_buttons)
        # Add stretch below the buttons
        self.layout.addStretch(1)

    def set_config_manager(self, config_manager):
        """Set the config manager for this widget."""
        self.config_manager = config_manager

    def set_file_controller(self, file_controller):
        """Set the file controller for this widget."""
        self.file_controller = file_controller

    def get_figure_size_inches(self):
        """Calculates the necessary figsize in inches."""
        width_in = TARGET_WIDTH_PX / STANDARD_DPI
        height_in = TARGET_HEIGHT_PX / STANDARD_DPI
        return (width_in, height_in)

    def switch_button_color(self, button):
        if self.highlighted_button != None:
            self.highlighted_button.setStyleSheet("background-color: light grey")

        self.highlighted_button = button
        button.setStyleSheet("background-color: #1f77b4")

    def blank_plot(self, state):
        """Creates a new blank figure with the correct size."""
        fig_size = self.get_figure_size_inches()
        if self.fig:
            plt.close(self.fig)

        # Ensure the blank figure is created with the target size properties
        self.fig = Figure(figsize=fig_size, dpi=STANDARD_DPI)
        ax = self.fig.add_subplot(111)
        if state == "error":
            print("error")
            ax.set_axis_on()
            self.fig.suptitle("Error: No particles detected.")
        else:
            ax.set_axis_off()

    def set_particles(self, particles):
        self.particles = particles
        self.plot_sb()

    def plot_mass(self):
        # 1. Get the new sized figure
        new_fig = self.get_mass_count()

        # 2. Close the old figure
        if self.fig and self.fig is not new_fig:
            plt.close(self.fig)

        if new_fig is None:
            # Handle error/no particles case
            self.blank_plot("error")
            self.canvas.draw()
            return

        # 3. Assign the new figure
        self.fig = new_fig
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # 4. Redraw the canvas with the new figure
        self.canvas.figure = self.fig
        self.canvas.draw()

        self.switch_button_color(self.mass_button)

    def get_mass_count(self):
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Return None if nothing was found
            if self.particles is None or self.particles.empty:
                print("No particles detected in the selected frame.")
                return None

            # Create the plot
            fig, ax = plt.subplots()
            ax.hist(self.particles["mass"], bins=20)

            # Label the axes
            ax.set_xlabel("Mass", fontsize=20)
            ax.set_ylabel("Count", fontsize=20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)

            temp_fig.suptitle("Mass (Brightness)", fontsize=24)

            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def plot_ecc(self):
        # 1. Get the new sized figure
        new_fig = self.get_eccentriicity_count()

        # 2. Close the old figure
        if self.fig and self.fig is not new_fig:
            plt.close(self.fig)

        if new_fig is None:
            # Handle error/no particles case
            self.blank_plot("error")
            self.canvas.draw()
            return

        # 3. Assign the new figure
        self.fig = new_fig
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # 4. Redraw the canvas with the new figure
        self.canvas.figure = self.fig
        self.canvas.draw()

        self.switch_button_color(self.ecc_button)

    def get_eccentriicity_count(self):
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Return None if nothing was found
            if self.particles is None or self.particles.empty:
                print("No particles detected in the selected frame.")
                return None

            # Create the plot
            fig, ax = plt.subplots()
            ax.hist(self.particles["ecc"], bins=20)

            # Label the axes
            ax.set_xlabel("Eccentricity", fontsize=20)
            ax.set_ylabel("Count", fontsize=20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)

            temp_fig.suptitle("Eccentricity", fontsize=24)

            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def plot_sb(self):
        # 1. Get the new sized figure

        new_fig = self.get_subpixel_bias()

        # 2. Close the old figure
        if self.fig and self.fig is not new_fig:
            plt.close(self.fig)

        if new_fig is None:
            # Handle error/no particles case
            return

        # 3. Assign the new figure
        self.fig = new_fig
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # 4. Redraw the canvas with the new figure
        self.canvas.figure = self.fig
        self.canvas.draw()

        self.switch_button_color(self.sb_button)

    def get_subpixel_bias(self):
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Return None if nothing was found
            if self.particles.empty:
                print("No particles detected in the selected frame.")
                return None

            # Create the plot
            tp.subpx_bias(self.particles)

            temp_fig = plt.gcf()
            temp_fig.subplots_adjust(
                top=0.900, bottom=0.100, left=0.075, right=0.950, wspace=0.250
            )
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)
            temp_fig.suptitle("Subpixel Bias", fontsize=24)

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def plot_mass_size(self):
        # 1. Get the new sized figure
        new_fig = self.get_mass_size()

        # 2. Close the old figure
        if self.fig and self.fig is not new_fig:
            plt.close(self.fig)

        if new_fig is None:
            # Handle error/no particles case
            return

        # 3. Assign the new figure
        self.fig = new_fig
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # 4. Redraw the canvas with the new figure
        self.canvas.figure = self.fig
        self.canvas.draw()

        self.switch_button_color(self.mass_size_button)

    def get_mass_size(self):
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            if self.particles is None or self.particles.empty:
                print("No particles detected in the selected frame.")
                return None  # Return None if nothing was found

            # Create the plot
            fig, ax = plt.subplots()
            tp.mass_size(self.particles, ax=ax)

            ax.set_xlabel("Mass", fontsize=20)
            ax.set_ylabel("Size", fontsize=20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)
            temp_fig.suptitle("Mass vs Size", fontsize=24)

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def plot_mass_ecc(self):
        # 1. Get the new sized figure
        new_fig = self.get_mass_ecc()

        # 2. Close the old figure
        if self.fig and self.fig is not new_fig:
            plt.close(self.fig)

        if new_fig is None:
            # Handle error/no particles case
            return

        # 3. Assign the new figure
        self.fig = new_fig
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # 4. Redraw the canvas with the new figure
        self.canvas.figure = self.fig
        self.canvas.draw()

        self.switch_button_color(self.mass_ecc_button)

    def get_mass_ecc(self):
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            if self.particles is None or self.particles.empty:
                print("No particles detected in the selected frame.")
                return None  # Return None if nothing was found

            # Create the plot
            fig, ax = plt.subplots()
            tp.mass_ecc(self.particles, ax=ax)

            ax.set_xlabel("Mass", fontsize=20)
            ax.set_ylabel("Eccentricity", fontsize=20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)
            temp_fig.suptitle("Mass vs Eccentricity", fontsize=24)

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def plot_size_ecc(self):
        # 1. Get the new sized figure
        new_fig = self.get_size_ecc()

        # 2. Close the old figure
        if self.fig and self.fig is not new_fig:
            plt.close(self.fig)

        if new_fig is None:
            # Handle error/no particles case
            return

        # 3. Assign the new figure
        self.fig = new_fig
        self.canvas.setFixedSize(TARGET_WIDTH_PX, TARGET_HEIGHT_PX)

        # 4. Redraw the canvas with the new figure
        self.canvas.figure = self.fig
        self.canvas.draw()

        self.switch_button_color(self.size_ecc_button)

    def get_size_ecc(self):
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            if self.particles is None or self.particles.empty:
                print("No particles detected in the selected frame.")
                return None  # Return None if nothing was found

            # Create the plot
            fig, ax = plt.subplots()
            ax.plot(self.particles["size"], self.particles["ecc"], "ko", alpha=0.1)
            # tp.mass_ecc(self.particles, ax = ax)

            ax.set_xlabel("Size", fontsize=20)
            ax.set_ylabel("Eccentricity", fontsize=20)

            temp_fig = plt.gcf()
            temp_fig.set_figheight(8)
            temp_fig.set_figwidth(10)
            temp_fig.suptitle("Size vs Eccentricity", fontsize=24)

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None
