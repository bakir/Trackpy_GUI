"""
Graphing Panel for the ParticleDetectionWindow

Description: Graphing panel showing the subpixel bias, filtering parameters, 
             and histograms of all particles based on current tracking parameters.

"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMenu,
    QSpinBox,
    QFormLayout
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import os
from copy import copy
from .. import particle_processing
import pandas as pd

from ..utils import GraphingUtils
from .FilteringWidget import FilteringWidget

class DectectionPlottingWidget(GraphingUtils.GraphingPanelWidget):
    def __init__(self, parent=None):
        super(GraphingUtils.GraphingPanelWidget, self).__init__()

        self.setup_plot_display()

        # Buttons
        self.graphing_buttons = QWidget()
        self.button_layout = QHBoxLayout(self.graphing_buttons)

        # Subpixel bias
        self.sb = QWidget()
        self.sb_layout = QVBoxLayout(self.sb)
        self.sb_label = QLabel("Subpixel Bias")
        self.sb_layout.addWidget(self.sb_label, alignment=Qt.AlignTop)

        self.sb_button = GraphingUtils.GraphingButton(text="Subpixel Bias", parent=self)
        self.sb_button.clicked.connect(
            lambda: self.self_plot(self.get_subpixel_bias, self.sb_button)
        )
        self.sb_layout.addWidget(self.sb_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.sb)
        self.sb_layout.addStretch(1)

        # Filtering
        self.filtering_buttons(self.button_layout, "detection")

        # Histograms
        self.hist = QWidget()
        self.hist_layout = QVBoxLayout(self.hist)
        self.hist_label = QLabel("Histograms")
        self.hist_layout.addWidget(self.hist_label, alignment=Qt.AlignTop)

        self.ecc_button = GraphingUtils.GraphingButton(text="Eccentricity", parent=self)
        self.ecc_button.clicked.connect(
            lambda: self.self_plot(
                self.get_eccentricity_count, self.ecc_button
            )
        )
        self.hist_layout.addWidget(self.ecc_button, alignment=Qt.AlignTop)

        self.mass_button = GraphingUtils.GraphingButton(text="Mass", parent=self)
        self.mass_button.clicked.connect(
            lambda: self.self_plot(self.get_mass_count, self.mass_button)
        )
        self.hist_layout.addWidget(self.mass_button, alignment=Qt.AlignTop)

        # Default number of bins for histograms
        self.bins = 20
        self.hist_bin_row = QFormLayout()
        # Allow user to select bin number for histograms
        self.hist_bins = QSpinBox(value=self.bins)
        self.hist_bins.setRange(1, 50)
        self.hist_bins.setToolTip(
            "Number of bins for the histograms."
        )

        self.hist_bin_row.addRow("Bins: ", self.hist_bins)
        self.hist_layout.addLayout(self.hist_bin_row)
        self.hist_bins.valueChanged.connect(self.update_bins)

        self.button_layout.addWidget(self.hist)
        self.hist_layout.addStretch(1)

        self.layout.addWidget(self.graphing_buttons)
        
        # Add filtering widget below the graphs
        self.filtering_widget = FilteringWidget(source_data_file="all_particles.csv")
        self.layout.addWidget(self.filtering_widget)
        
        # Add stretch below the buttons
        self.layout.addStretch(1)

    def set_particles(self, particles):
        """Sets paritcle data and plots subpixel bias."""
        self.data = particles
        self.self_plot(self.get_subpixel_bias, self.sb_button)

    # def refresh_plots(self):
    #     """Reload data from all_particles.csv and refresh plots."""
    #     if self.file_controller:
    #         try:
    #             self.data = self.file_controller.load_particles_data("all_particles.csv")
    #             if not self.data.empty:
    #                 self.self_plot(self.get_subpixel_bias, self.sb_button)
    #             else:
    #                 self.blank_plot()
    #         except pd.errors.EmptyDataError:
    #             self.data = pd.DataFrame()
    #             self.blank_plot()
      
    def set_file_controller(self, file_controller):
        """Override to also set file controller for filtering widget."""
        super().set_file_controller(file_controller)
        if hasattr(self, 'filtering_widget'):
            self.filtering_widget.set_file_controller(file_controller)
            if file_controller and hasattr(file_controller, 'project_path'):
                self.filtering_widget.project_path = file_controller.project_path
        # Load particle data when file controller is set
        self.load_particle_data()
    
    def load_particle_data(self):
        """Load particle data from file controller if available."""
        if self.file_controller:
            try:
                self.data = self.file_controller.load_particles_data("all_particles.csv")
            except (pd.errors.EmptyDataError, FileNotFoundError):
                self.data = pd.DataFrame()

    def update_bins(self, value):
        self.bins = value

    def get_mass_count(self, page=None):
        """Creates a histogram of all current particles mass."""
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            fig, ax = plt.subplots()
            ax.hist(self.data["mass"], bins=self.bins)

            # Label the axes
            ax.set_xlabel("Mass")
            ax.set_ylabel("Count")

            temp_fig = plt.gcf()

            temp_fig.suptitle("Mass (Brightness)")

            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def get_eccentricity_count(self, page=None):
        """Creates a histogram of all current particles eccentricity."""
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            fig, ax = plt.subplots()
            ax.hist(self.data["ecc"], bins=self.bins)

            # Label the axes
            ax.set_xlabel("Eccentricity")
            ax.set_ylabel("Count")

            temp_fig = plt.gcf()

            temp_fig.suptitle("Eccentricity")

            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None

    def get_subpixel_bias(self, page=None):
        """Creates a plot of the subpixel bias of all current particles."""
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Check if particles were found before plotting
            self.check_for_empty_data()

            # Create the plot
            tp.subpx_bias(self.data)

            temp_fig = plt.gcf()
            temp_fig.subplots_adjust(
                top=0.900, bottom=0.100, left=0.090, right=0.950, wspace=0.250
            )
            temp_fig.suptitle("Subpixel Bias")

            # Return the figure instead of the DataFrame
            return temp_fig

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None
