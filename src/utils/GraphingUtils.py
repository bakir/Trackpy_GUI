"""
Graphing Utilities Module

Description: Base classes and utilities for graphing widgets used in both
             ParticleDetectionWindow and TrajectoryLinkingWindow.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal
import numpy as np
import pandas as pd
import pyqtgraph as pg

from .SizingUtils import get_plot_font_sizes, scaled_length
from ..UI.DW_LW_FilteringWidget import compute_filter_pass_mask


pg.setConfigOptions(antialias=True, background="w", foreground="k")


class GraphingButton(QPushButton):
    """Button for graphing controls with highlight state management."""

    highlighted_button = None

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

    def switch_button_color(self):
        if GraphingButton.highlighted_button is not None:
            prev_button = GraphingButton.highlighted_button
            prev_button.setDown(False)
            prev_button.setChecked(False)

        GraphingButton.highlighted_button = self
        self.setChecked(True)


class GraphingPanelWidget(QWidget):
    """Base widget for graphing panels with interactive PyQtGraph plots."""

    pointSelected = Signal(dict)
    plotSwitched = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scatter_plot_df = None
        self._scatter_item = None
        self._scatter_x_col = None
        self._scatter_y_col = None
        self._scatter_pass_mask = None
        self._selected_scatter_index = None
        self._active_scatter_id = None
        self._linked_particle = None

    def set_config_manager(self, config_manager):
        self.config_manager = config_manager

    def set_file_controller(self, file_controller):
        self.file_controller = file_controller

    def setup_plot_display(self):
        self.config_manager = None
        self.file_controller = None
        self.data = None

        self.layout = QVBoxLayout(self)
        self.plot_container = pg.GraphicsLayoutWidget()
        self.plot_container.setBackground("w")
        self.layout.addWidget(self.plot_container, 20)

        self.selection_info_label = QLabel("Click a point to inspect particle coordinates.")
        self.selection_info_label.setWordWrap(True)
        self.selection_info_label.setAlignment(Qt.AlignCenter)
        self.selection_info_label.setStyleSheet(
            """
            QLabel {
                background-color: #f0f0f0;
                padding: 6px;
                border-radius: 4px;
            }
        """
        )
        self.layout.addWidget(self.selection_info_label)

        self.blank_plot()

    def _get_plot_font_sizes(self):
        return get_plot_font_sizes()

    def _get_scaled_scatter_size(self):
        fonts = self._get_plot_font_sizes()
        return scaled_length(6, fonts["scale"])

    def _get_scaled_pen_width(self, base=1.5):
        fonts = self._get_plot_font_sizes()
        return scaled_length(base, fonts["scale"], minimum=1.0)

    def _add_scaled_plot(self, row=0, col=0, colspan=1, title=None):
        fonts = self._get_plot_font_sizes()
        plot = self.plot_container.addPlot(row=row, col=col, colspan=colspan)
        if title:
            plot.setTitle(title, color="k", size=fonts["title_pt"])
        return plot, fonts

    def _teardown_scatter_item(self):
        """Disconnect scatter signals before the item is destroyed."""
        if self._scatter_item is not None:
            try:
                self._scatter_item.sigClicked.disconnect(self._on_scatter_clicked)
            except (TypeError, RuntimeError):
                pass
            try:
                self._scatter_item.sigHovered.disconnect(self._on_scatter_hovered)
            except (TypeError, RuntimeError):
                pass
        self._scatter_item = None
        self._active_scatter_id = None

    def _prepare_for_new_plot(self):
        """Fully reset the plot area before drawing a different plot."""
        self._teardown_scatter_item()
        self._scatter_plot_df = None
        self._scatter_x_col = None
        self._scatter_y_col = None
        self._scatter_pass_mask = None
        self._selected_scatter_index = None
        if hasattr(self, "plot_container"):
            self.plot_container.clear()

    def blank_plot(self):
        if hasattr(self, "plot_container"):
            self._prepare_for_new_plot()
            fonts = self._get_plot_font_sizes()
            label = pg.LabelItem(
                "No plot to display.", color="k", size=fonts["subtitle_pt"]
            )
            self.plot_container.addItem(label, row=0, col=0)
            self._reset_selection_label()

    def _reset_selection_label(self):
        if hasattr(self, "selection_info_label"):
            self.selection_info_label.setText("Click a point to inspect particle coordinates.")

    def _format_particle_info(self, row, x_col=None, y_col=None, prefix="Selected"):
        parts = []
        if x_col is not None and y_col is not None and x_col in row and y_col in row:
            parts.append(f"plot {x_col}={row[x_col]:.3f}")
            parts.append(f"{y_col}={row[y_col]:.3f}")
        if "frame" in row:
            parts.append(f"frame={int(row['frame']) + 1}")
        if "x" in row:
            parts.append(f"x={row['x']:.2f}")
        if "y" in row:
            parts.append(f"y={row['y']:.2f}")
        if "particle" in row:
            parts.append(f"particle={int(row['particle'])}")
        if "mass" in row:
            parts.append(f"mass={row['mass']:.2f}")
        if "size" in row:
            parts.append(f"size={row['size']:.2f}")
        if "ecc" in row:
            parts.append(f"ecc={row['ecc']:.3f}")
        return f"{prefix}: " + " | ".join(parts)

    def _find_row_index_for_particle(self, plot_df, particle):
        if particle is None or plot_df is None or plot_df.empty:
            return None
        frame = int(particle["frame"])
        px = float(particle["x"])
        py = float(particle["y"])
        tol = 0.5
        best_index = None
        best_dist = None
        for i, (_, row) in enumerate(plot_df.iterrows()):
            if int(row["frame"]) != frame:
                continue
            dist = (float(row["x"]) - px) ** 2 + (float(row["y"]) - py) ** 2
            if dist <= tol * tol:
                return i
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_index = i
        if best_index is not None and best_dist is not None:
            max_dist = max(self._get_scaled_scatter_size(), 8.0) ** 2
            if best_dist <= max_dist:
                return best_index
        return None

    def _build_scatter_spots(
        self, plot_df, x_col, y_col, selected_index=None, pass_mask=None
    ):
        size = self._get_scaled_scatter_size()
        selected_size = size * 1.6
        kept_brush = pg.mkBrush(0, 0, 0, 45)
        removed_brush = pg.mkBrush(220, 60, 60, 170)
        selected_brush = pg.mkBrush(0, 200, 0, 230)
        spots = []
        for i, (_, row) in enumerate(plot_df.iterrows()):
            is_selected = selected_index is not None and i == selected_index
            passes = True if pass_mask is None else bool(pass_mask.iloc[i])
            if is_selected:
                brush = selected_brush
                pen = pg.mkPen(0, 160, 0, width=2)
                point_size = selected_size
            elif passes:
                brush = kept_brush
                pen = None
                point_size = size
            else:
                brush = removed_brush
                pen = pg.mkPen(180, 40, 40, width=1)
                point_size = size
            spots.append(
                {
                    "pos": (float(row[x_col]), float(row[y_col])),
                    "data": i,
                    "brush": brush,
                    "size": point_size,
                    "pen": pen,
                }
            )
        return spots

    def _get_filter_pass_mask_for_plot(self, plot_df):
        if not hasattr(self, "filtering_widget") or self.filtering_widget is None:
            return None
        fw = self.filtering_widget
        if not fw.filters and not fw.compound_filters:
            return None
        if plot_df is None or plot_df.empty:
            return None
        return compute_filter_pass_mask(plot_df, fw.filters, fw.compound_filters)

    def _scatter_is_active(self):
        return (
            self._scatter_item is not None
            and self._active_scatter_id is not None
            and id(self._scatter_item) == self._active_scatter_id
        )

    def _update_scatter_highlight(self):
        if not self._scatter_is_active() or self._scatter_plot_df is None:
            return
        if self._scatter_x_col is None or self._scatter_y_col is None:
            return
        spots = self._build_scatter_spots(
            self._scatter_plot_df,
            self._scatter_x_col,
            self._scatter_y_col,
            self._selected_scatter_index,
            self._scatter_pass_mask,
        )
        self._scatter_item.setData(spots=spots)

    def _on_scatter_clicked(self, _plot, points):
        if not self._scatter_is_active() or not points or self._scatter_plot_df is None:
            return
        row_index = points[0].data()
        if row_index is None:
            return
        self._select_scatter_point(int(row_index))

    def _on_scatter_hovered(self, _plot, points):
        if not self._scatter_is_active() or self._scatter_plot_df is None:
            return
        if points:
            row = self._scatter_plot_df.iloc[int(points[0].data())]
            self.selection_info_label.setText(
                self._format_particle_info(
                    row, self._scatter_x_col, self._scatter_y_col, prefix="Hover"
                )
            )
        elif self._selected_scatter_index is None:
            self._reset_selection_label()
        else:
            row = self._scatter_plot_df.iloc[self._selected_scatter_index]
            self.selection_info_label.setText(
                self._format_particle_info(row, self._scatter_x_col, self._scatter_y_col)
            )

    def _select_scatter_point(self, row_index):
        if (
            not self._scatter_is_active()
            or self._scatter_plot_df is None
            or row_index < 0
            or row_index >= len(self._scatter_plot_df)
        ):
            return
        self._selected_scatter_index = row_index
        row = self._scatter_plot_df.iloc[row_index]
        self._linked_particle = {
            "frame": int(row["frame"]),
            "x": float(row["x"]),
            "y": float(row["y"]),
        }
        self._update_scatter_highlight()
        self.selection_info_label.setText(
            self._format_particle_info(row, self._scatter_x_col, self._scatter_y_col)
        )
        self.pointSelected.emit(row.to_dict())

    def _clear_plot(self):
        self._prepare_for_new_plot()

    def has_plot_data(self):
        return self.data is not None and not self.data.empty

    def check_for_empty_data(self):
        if not self.has_plot_data():
            print("No particles detected in the selected frame.")
            return False
        return True

    def self_plot(self, plotting_function, button, page=None, emit_plot_switched=True):
        self._prepare_for_new_plot()
        if emit_plot_switched:
            self.plotSwitched.emit()
        try:
            success = plotting_function(page)
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            success = False
        if not success:
            self.blank_plot()
            return
        button.switch_button_color()

    def clear_linked_particle(self):
        """Clear the particle linked between the frame viewer and scatter plots."""
        self._linked_particle = None
        self._selected_scatter_index = None
        if self._scatter_is_active():
            self._update_scatter_highlight()
        elif hasattr(self, "selection_info_label"):
            self._reset_selection_label()

    def select_particle_from_frame(self, particle_dict):
        """Highlight a particle picked on the frame across filtering scatter plots."""
        if not particle_dict or "frame" not in particle_dict:
            return
        self._linked_particle = {
            "frame": int(particle_dict["frame"]),
            "x": float(particle_dict["x"]),
            "y": float(particle_dict["y"]),
        }
        self.selection_info_label.setText(
            self._format_particle_info(particle_dict, prefix="Frame selection")
        )

        active = GraphingButton.highlighted_button
        filter_buttons = {
            getattr(self, "mass_size_button", None),
            getattr(self, "mass_ecc_button", None),
            getattr(self, "size_ecc_button", None),
        }
        page = getattr(self, "_filter_plot_page", "detection")
        if active in filter_buttons:
            plotters = {
                self.mass_size_button: self.get_mass_size,
                self.mass_ecc_button: self.get_mass_ecc,
                self.size_ecc_button: self.get_size_ecc,
            }
            self.self_plot(plotters[active], active, page, emit_plot_switched=False)
        elif hasattr(self, "mass_size_button"):
            self.self_plot(
                self.get_mass_size,
                self.mass_size_button,
                page,
                emit_plot_switched=False,
            )

    def _style_plot(self, plot, xlabel=None, ylabel=None, fonts=None):
        if fonts is None:
            fonts = self._get_plot_font_sizes()

        plot.showGrid(x=True, y=True, alpha=0.25)
        tick_font = QFont()
        tick_font.setPointSizeF(fonts["tick"])

        for axis_name in ("bottom", "left"):
            axis = plot.getAxis(axis_name)
            axis.setPen(pg.mkPen("k"))
            axis.setTextPen(pg.mkPen("k"))
            axis.setStyle(tickFont=tick_font)

        if xlabel:
            plot.setLabel("bottom", xlabel, color="k", size=fonts["label_pt"])
        if ylabel:
            plot.setLabel("left", ylabel, color="k", size=fonts["label_pt"])

    def _add_histogram(self, plot, values, bins, xlabel=None, ylabel="Count", fonts=None):
        self._style_plot(plot, xlabel=xlabel, ylabel=ylabel, fonts=fonts)
        counts, edges = np.histogram(values, bins=bins)
        if len(counts) == 0:
            return
        bar_width = (edges[1] - edges[0]) * 0.9
        x = (edges[:-1] + edges[1:]) / 2
        plot.addItem(
            pg.BarGraphItem(
                x=x,
                height=counts,
                width=bar_width,
                brush=pg.mkBrush(0, 0, 0, 180),
            )
        )

    def _plot_scatter_panel(self, plot_df, x_col, y_col, title, xlabel, ylabel):
        if self._linked_particle is None:
            self._reset_selection_label()
        pass_mask = self._get_filter_pass_mask_for_plot(plot_df)
        plot_df = plot_df.reset_index(drop=True)
        if pass_mask is not None:
            pass_mask = pass_mask.reset_index(drop=True)
        self._scatter_plot_df = plot_df
        self._scatter_x_col = x_col
        self._scatter_y_col = y_col
        self._scatter_pass_mask = pass_mask
        self._selected_scatter_index = self._find_row_index_for_particle(
            plot_df, self._linked_particle
        )

        plot, fonts = self._add_scaled_plot(title=title)
        self._style_plot(plot, xlabel=xlabel, ylabel=ylabel, fonts=fonts)

        scatter = pg.ScatterPlotItem(
            spots=self._build_scatter_spots(
                plot_df,
                x_col,
                y_col,
                selected_index=self._selected_scatter_index,
                pass_mask=pass_mask,
            ),
            hoverable=True,
            tip=None,
        )
        scatter.sigClicked.connect(self._on_scatter_clicked)
        scatter.sigHovered.connect(self._on_scatter_hovered)
        plot.addItem(scatter)
        self._scatter_item = scatter
        self._active_scatter_id = id(scatter)
        if pass_mask is not None:
            removed = int((~pass_mask).sum())
            kept = int(pass_mask.sum())
            filter_text = (
                f"Filtering plot: {kept} kept (dark), {removed} removed (red). "
                "Click a point to inspect."
            )
            if self._linked_particle is not None and self._selected_scatter_index is not None:
                row = plot_df.iloc[self._selected_scatter_index]
                filter_text += " " + self._format_particle_info(
                    row, x_col, y_col, prefix="Highlighted"
                )
            self.selection_info_label.setText(filter_text)
        elif self._linked_particle is not None and self._selected_scatter_index is not None:
            row = plot_df.iloc[self._selected_scatter_index]
            self.selection_info_label.setText(
                self._format_particle_info(row, x_col, y_col, prefix="Frame selection")
            )
        return True

    def refresh_active_filter_plot(self):
        """Re-draw the active filtering scatter plot after filter edits."""
        active = GraphingButton.highlighted_button
        filter_plotters = {
            getattr(self, "mass_size_button", None): (
                self.get_mass_size,
                getattr(self, "_filter_plot_page", "detection"),
            ),
            getattr(self, "mass_ecc_button", None): (
                self.get_mass_ecc,
                getattr(self, "_filter_plot_page", "detection"),
            ),
            getattr(self, "size_ecc_button", None): (
                self.get_size_ecc,
                getattr(self, "_filter_plot_page", "detection"),
            ),
        }
        for button, (plotter, page) in filter_plotters.items():
            if button is not None and active is button:
                self.self_plot(plotter, button, page, emit_plot_switched=False)
                return

    def _plot_dataframe(self, df, page):
        if page == "detection":
            return df
        return df.groupby(["particle"]).mean()

    def filtering_buttons(self, button_layout, page):
        self._filter_plot_page = page
        self.filter = QWidget()
        self.filter_layout = QVBoxLayout(self.filter)
        self.filter_label = QLabel("Filtering")
        self.filter_layout.addWidget(self.filter_label, alignment=Qt.AlignTop)

        self.mass_ecc_button = GraphingButton(text="Mass vs Eccentricity", parent=self)
        self.mass_ecc_button.clicked.connect(
            lambda: self.self_plot(
                self.get_mass_ecc, self.mass_ecc_button, page, emit_plot_switched=False
            )
        )
        self.filter_layout.addWidget(self.mass_ecc_button, alignment=Qt.AlignTop)

        self.mass_size_button = GraphingButton(text="Mass vs Size", parent=self)
        self.mass_size_button.clicked.connect(
            lambda: self.self_plot(
                self.get_mass_size, self.mass_size_button, page, emit_plot_switched=False
            )
        )
        self.filter_layout.addWidget(self.mass_size_button, alignment=Qt.AlignTop)

        self.size_ecc_button = GraphingButton(text="Size vs Eccentricity", parent=self)
        self.size_ecc_button.clicked.connect(
            lambda: self.self_plot(
                self.get_size_ecc, self.size_ecc_button, page, emit_plot_switched=False
            )
        )
        self.filter_layout.addWidget(self.size_ecc_button, alignment=Qt.AlignTop)

        self.button_layout.addWidget(self.filter)
        self.filter_layout.addStretch(1)

    def get_mass_size(self, page):
        try:
            if not self.check_for_empty_data():
                return False
            plot_df = self._plot_dataframe(self.data, page)
            return self._plot_scatter_panel(
                plot_df,
                "mass",
                "size",
                "Mass vs Size",
                "Mass",
                "Size",
            )
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False

    def get_mass_ecc(self, page):
        try:
            if not self.check_for_empty_data():
                return False
            plot_df = self._plot_dataframe(self.data, page)
            return self._plot_scatter_panel(
                plot_df,
                "mass",
                "ecc",
                "Mass vs Eccentricity",
                "Mass",
                "Eccentricity",
            )
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False

    def get_size_ecc(self, page):
        try:
            if not self.check_for_empty_data():
                return False
            plot_df = self._plot_dataframe(self.data, page)
            return self._plot_scatter_panel(
                plot_df,
                "size",
                "ecc",
                "Size vs Eccentricity",
                "Size",
                "Eccentricity",
            )
        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return False
