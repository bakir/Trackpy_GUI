"""
UI Utility Functions

Description: Shared utility functions for UI components to reduce code duplication.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtGui import QFont


def create_label_with_info(label_text, tooltip_text, add_stretch=True):
    """
    Create a label widget with an info icon and tooltip.

    Parameters
    ----------
    label_text : str
        The label text to display
    tooltip_text : str
        The tooltip text for the info icon
    add_stretch : bool, optional
        Whether to add a stretch at the end (default: True)

    Returns
    -------
    QWidget
        A widget containing the label and info icon
    """
    label_widget = QWidget()
    label_layout = QHBoxLayout(label_widget)
    label_layout.setContentsMargins(0, 0, 0, 0)
    label_layout.setSpacing(4)
    label = QLabel(label_text)
    info_icon = QLabel("ⓘ")
    info_icon.setToolTip(tooltip_text)
    font = info_icon.font()
    font.setPointSize(10)
    info_icon.setFont(font)
    info_icon.setStyleSheet("color: #0033cc;")
    label_layout.addWidget(label)
    label_layout.addWidget(info_icon)
    if add_stretch:
        label_layout.addStretch()
    return label_widget
