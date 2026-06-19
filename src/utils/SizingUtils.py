"""
Sizing Utilities Module

Description: Finds various screen, window, and widget sizes for various files.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

from PySide6.QtWidgets import QApplication

WIN_WIDTH = 0
FIG_WIDTH_PX = 0
FIG_HEIGHT_PX = 0
FIG_WIDTH_IN = 0
FIG_HEIGHT_IN = 0
STANDARD_DPI = 100

REFERENCE_SCREEN_HEIGHT = 1080
REFERENCE_LOGICAL_DPI = 96.0
MIN_UI_SCALE = 0.85
MAX_UI_SCALE = 2.0


def get_screen_dims():
    """
    Get the screen dimensions.

    Returns
    -------
    tuple
        Tuple containing (screen_width, screen_height) in pixels.
    """
    # app = QApplication()
    qapp = QApplication.instance()
    screen = qapp.primaryScreen()
    screen_width = screen.size().width()
    screen_height = screen.size().height()
    return screen_width, screen_height


def get_start_screen_geometry():
    """
    Get the geometry for the start screen window.

    Returns
    -------
    tuple
        Tuple containing (x_position, y_position, width, height) for the start screen window.
    """
    screen_width, screen_height = get_screen_dims()
    start_screen_width = screen_width * 0.4
    start_screen_height = screen_height * 0.7
    x_left = (screen_width / 2) - (start_screen_width / 2)
    y_up = (screen_height / 2) - (start_screen_height / 2)
    return x_left, y_up, start_screen_width, start_screen_height


def get_ui_scale_factor():
    """
    Scale factor for plot fonts and markers relative to a 1080p / 96 DPI baseline.

    Uses the primary screen's available height and logical DPI so plots stay
    readable on high-resolution and high-DPI displays.
    """
    qapp = QApplication.instance()
    if qapp is None:
        return 1.0

    screen = qapp.primaryScreen()
    if screen is None:
        return 1.0

    height = screen.availableGeometry().height()
    dpi = screen.logicalDotsPerInch()
    scale = (height / REFERENCE_SCREEN_HEIGHT) * (dpi / REFERENCE_LOGICAL_DPI)
    return max(MIN_UI_SCALE, min(MAX_UI_SCALE, scale))


def scaled_font_points(base_points, scale=None):
    """Return a font size in points scaled for the current screen."""
    if scale is None:
        scale = get_ui_scale_factor()
    return max(8, round(base_points * scale))


def scaled_length(base_length, scale=None, minimum=1.0):
    """Return a line width, marker size, etc. scaled for the current screen."""
    if scale is None:
        scale = get_ui_scale_factor()
    return max(minimum, base_length * scale)


def get_plot_font_sizes():
    """Font sizes for PyQtGraph titles, axis labels, and tick labels."""
    scale = get_ui_scale_factor()
    tick = scaled_font_points(10, scale)
    label = scaled_font_points(11, scale)
    title = scaled_font_points(13, scale)
    subtitle = scaled_font_points(12, scale)
    return {
        "tick": tick,
        "label": label,
        "title": title,
        "subtitle": subtitle,
        "tick_pt": f"{tick}pt",
        "label_pt": f"{label}pt",
        "title_pt": f"{title}pt",
        "subtitle_pt": f"{subtitle}pt",
        "scale": scale,
    }
