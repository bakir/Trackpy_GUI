"""
Graphing Panel for the ParticleDetectionWindow

Description: Graphing panel showing the subpixel bias, filtering parameters,
             and histograms of all particles based on current tracking parameters.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSpinBox, QFormLayout
from PySide6.QtCore import Qt
import pandas as pd
import pyqtgraph as pg

from ..utils import GraphingUtils
from .DW_LW_FilteringWidget import DWLWFilteringWidget


class DWPlottingWidget(GraphingUtils.GraphingPanelWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup_plot_display()

        self.graphing_buttons = QWidget()
        self.button_layout = QHBoxLayout(self.graphing_buttons)

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

        self.filtering_buttons(self.button_layout, "detection")

        self.hist = QWidget()
        self.hist_layout = QVBoxLayout(self.hist)
        self.hist_label = QLabel("Histograms")
        self.hist_layout.addWidget(self.hist_label, alignment=Qt.AlignTop)

        self.ecc_button = GraphingUtils.GraphingButton(text="Eccentricity", parent=self)
        self.ecc_button.clicked.connect(
            lambda: self.self_plot(self.get_eccentricity_count, self.ecc_button)
        )
        self.hist_layout.addWidget(self.ecc_button, alignment=Qt.AlignTop)

        self.mass_button = GraphingUtils.GraphingButton(text="Mass", parent=self)
        self.mass_button.clicked.connect(
            lambda: self.self_plot(self.get_mass_count, self.mass_button)
        )
        self.hist_layout.addWidget(self.mass_button, alignment=Qt.AlignTop)

        self.bins = 20
        self.hist_bin_row = QFormLayout()
        self.hist_bins = QSpinBox(value=self.bins)
        self.hist_bins.setRange(1, 50)
        self.hist_bins.setToolTip("Number of bins for the histograms.")
        self.hist_bin_row.addRow("Bins: ", self.hist_bins)
        self.hist_layout.addLayout(self.hist_bin_row)
        self.hist_bins.valueChanged.connect(self.update_bins)

        self.button_layout.addWidget(self.hist)
        self.hist_layout.addStretch(1)

        self.layout.addWidget(self.graphing_buttons)

        self.filtering_widget = DWLWFilteringWidget(source_data_file="all_particles.csv")
        self.filtering_widget.filteredParticlesUpdated.connect(
            self.refresh_active_filter_plot
        )
        self.layout.addWidget(self.filtering_widget)
        self.layout.addStretch(1)

    def set_particles(self, particles):
        self.data = particles
        self.self_plot(self.get_subpixel_bias, self.sb_button)

    def set_file_controller(self, file_controller):
        super().set_file_controller(file_controller)
        if hasattr(self, "filtering_widget"):
            self.filtering_widget.set_file_controller(file_controller)
            if file_controller and hasattr(file_controller, "project_path"):
                self.filtering_widget.project_path = file_controller.project_path
        self.load_particle_data()

    def load_particle_data(self):
        if self.file_controller:
            try:
                self.data = self.file_controller.load_particles_data("all_particles.csv")
            except (pd.errors.EmptyDataError, FileNotFoundError):
                self.data = pd.DataFrame()

    def update_bins(self, value):
        self.bins = value
        active = GraphingUtils.GraphingButton.highlighted_button
        if active == self.mass_button:
            self.self_plot(self.get_mass_count, self.mass_button)
        elif active == self.ecc_button:
            self.self_plot(self.get_eccentricity_count, self.ecc_button)

    def get_mass_count(self, page=None):
        try:
            if not self.check_for_empty_data():
                return False
            self._clear_plot()
            plot, fonts = self._add_scaled_plot(title="Mass (Brightness)")
            self._add_histogram(
                plot, self.data["mass"].values, self.bins, xlabel="Mass", fonts=fonts
            )
            return True
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False

    def get_eccentricity_count(self, page=None):
        try:
            if not self.check_for_empty_data():
                return False
            self._clear_plot()
            plot, fonts = self._add_scaled_plot(title="Eccentricity")
            self._add_histogram(
                plot, self.data["ecc"].values, self.bins, xlabel="Eccentricity", fonts=fonts
            )
            return True
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False

    def get_subpixel_bias(self, page=None):
        try:
            if not self.check_for_empty_data():
                return False

            self._clear_plot()
            fonts = self._get_plot_font_sizes()
            pos_columns = ["x", "y"]
            if "z" in self.data.columns:
                pos_columns.append("z")

            for index, column in enumerate(pos_columns):
                plot, _ = self._add_scaled_plot(
                    row=0,
                    col=index,
                    title=f"{column} fractional part",
                )
                fractional = self.data[column].values % 1
                self._add_histogram(
                    plot,
                    fractional,
                    bins=20,
                    xlabel=f"{column} % 1",
                    fonts=fonts,
                )

            title = pg.LabelItem("Subpixel Bias", color="k", size=fonts["title_pt"])
            self.plot_container.addItem(title, row=1, col=0, colspan=len(pos_columns))
            return True
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False
