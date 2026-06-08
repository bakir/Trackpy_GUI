"""
Interactive Frame Viewer

Description: Zoomable, pannable video frame display using PyQtGraph (same interaction
             model as the particle plot panels).

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)


class InteractiveFrameViewer(QWidget):
    """Displays a single frame with pan/zoom via PyQtGraph."""

    viewOptionsChanged = Signal()
    particleClicked = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._has_image = False
        self._greyscale = False
        self._threshold_enabled = False
        self._threshold_percent = 50

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.placeholder_label = QLabel("Loading video...")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet(
            """
            QLabel {
                background-color: #1a1a1a;
                color: #cccccc;
                padding: 16px;
            }
        """
        )
        self.stack.addWidget(self.placeholder_label)

        self.graphics = pg.GraphicsLayoutWidget()
        self.graphics.setBackground("#1a1a1a")
        self.stack.addWidget(self.graphics)

        self.plot = self.graphics.addPlot(row=0, col=0)
        self.plot.hideAxis("left")
        self.plot.hideAxis("bottom")
        self.plot.setAspectLocked(True)
        self.plot.invertY(True)
        self.plot.setMenuEnabled(False)

        self.image_item = pg.ImageItem()
        self.plot.addItem(self.image_item)
        self.plot.scene().sigMouseClicked.connect(self._on_scene_mouse_clicked)

        self.stack.setCurrentWidget(self.placeholder_label)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_view_context_menu)
        self.graphics.setContextMenuPolicy(Qt.CustomContextMenu)
        self.graphics.customContextMenuRequested.connect(self._show_view_context_menu)

    def get_view_options(self):
        return {
            "greyscale": self._greyscale,
            "threshold_enabled": self._threshold_enabled,
            "threshold_percent": self._threshold_percent,
        }

    def _show_view_context_menu(self, pos):
        menu = QMenu(self)
        menu.setTitle("View options")

        grey_action = menu.addAction("Greyscale")
        grey_action.setCheckable(True)
        grey_action.setChecked(self._greyscale)
        grey_action.setEnabled(not self._threshold_enabled)

        threshold_action = menu.addAction("Adjustable threshold")
        threshold_action.setCheckable(True)
        threshold_action.setChecked(self._threshold_enabled)

        menu.addSeparator()

        slider_action = QWidgetAction(menu)
        slider_widget = QWidget()
        slider_layout = QHBoxLayout(slider_widget)
        slider_layout.setContentsMargins(12, 6, 12, 6)
        slider_layout.addWidget(QLabel("Threshold"))
        threshold_slider = QSlider(Qt.Horizontal)
        threshold_slider.setRange(0, 100)
        threshold_slider.setValue(self._threshold_percent)
        threshold_slider.setEnabled(self._threshold_enabled)
        threshold_slider.setMinimumWidth(140)
        threshold_value_label = QLabel(f"{self._threshold_percent}%")
        slider_layout.addWidget(threshold_slider)
        slider_layout.addWidget(threshold_value_label)
        slider_action.setDefaultWidget(slider_widget)
        menu.addAction(slider_action)

        def on_greyscale(checked):
            self._greyscale = checked
            self.viewOptionsChanged.emit()

        def on_threshold(checked):
            self._threshold_enabled = checked
            if checked:
                self._greyscale = False
            threshold_slider.setEnabled(checked)
            self.viewOptionsChanged.emit()

        def on_slider(value):
            self._threshold_percent = value
            threshold_value_label.setText(f"{value}%")
            if self._threshold_enabled:
                self.viewOptionsChanged.emit()

        grey_action.toggled.connect(on_greyscale)
        threshold_action.toggled.connect(on_threshold)
        threshold_slider.valueChanged.connect(on_slider)

        sender = self.sender()
        if sender is self.graphics:
            global_pos = self.graphics.mapToGlobal(pos)
        else:
            global_pos = self.mapToGlobal(pos)
        menu.exec(global_pos)

    def set_message(self, message):
        """Show a text placeholder instead of a frame."""
        self._has_image = False
        self.placeholder_label.setText(message)
        self.stack.setCurrentWidget(self.placeholder_label)

    def set_frame_image(self, rgb_image, reset_view=True):
        """
        Display an RGB frame (HxWx3 uint8).

        Parameters
        ----------
        rgb_image : np.ndarray or None
            Image in row-major RGB order.
        reset_view : bool
            If True, fit the full frame in view (used when changing frames).
        """
        if rgb_image is None or rgb_image.size == 0:
            self.set_message("Frame not found")
            return

        self._has_image = True
        self.stack.setCurrentWidget(self.graphics)
        self.image_item.setImage(np.ascontiguousarray(rgb_image), axisOrder="row-major")
        if reset_view:
            self.reset_view()

    def reset_view(self):
        """Fit the entire frame in the viewer."""
        if not self._has_image:
            return
        self.plot.autoRange(padding=0.02)

    def _on_scene_mouse_clicked(self, event):
        """Map a viewer click to image coordinates and emit for particle hit-testing."""
        if not self._has_image or event.button() != Qt.MouseButton.LeftButton:
            return
        scene_pos = event.scenePos()
        if not self.plot.vb.sceneBoundingRect().contains(scene_pos):
            return
        mouse_point = self.plot.vb.mapSceneToView(scene_pos)
        self.particleClicked.emit(float(mouse_point.x()), float(mouse_point.y()))

    def clear(self):
        self._has_image = False
        self.image_item.clear()
        self.set_message("")
