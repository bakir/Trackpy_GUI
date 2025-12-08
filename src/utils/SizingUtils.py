"""
Sizing Utilities Module

Description: Finds various screen, window, and widget sizes for various files
"""
from PySide6.QtWidgets import QApplication

WIN_WIDTH = 0
FIG_WIDTH_PX = 0
FIG_HEIGHT_PX = 0
FIG_WIDTH_IN = 0
FIG_HEIGHT_IN = 0
STANDARD_DPI = 100

def get_screen_dims():
    # app = QApplication()
    qapp = QApplication.instance()
    screen = qapp.primaryScreen()
    screen_width = screen.size().width()
    screen_height = screen.size().height()
    return screen_width, screen_height

def get_start_screen_geometry():
    screen_width, screen_height = get_screen_dims()
    start_screen_width = screen_width*0.4
    start_screen_height = screen_height*0.7
    x_left = (screen_width/2) - (start_screen_width/2)
    y_up = (screen_height/2) - (start_screen_height/2)
    return x_left, y_up, start_screen_width, start_screen_height
