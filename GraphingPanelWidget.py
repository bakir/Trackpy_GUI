from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import particle_processing
from config_parser import *
import os
from copy import copy

class GraphingPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Graph area
        self.layout = QVBoxLayout(self)
        self.blank_plot()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setFixedSize(500, 400)
        self.layout.addWidget(self.canvas)

        # button for plotting subpixel bias
        self.sb_button = QPushButton(text="Plot Subpixel Bias", parent=self)
        self.sb_button.clicked.connect(self.plot_sb)
        self.layout.addWidget(self.sb_button, alignment=Qt.AlignLeft)

    def blank_plot(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_axis_off()
        return self.fig, self.ax

    def plot_sb(self):
        # Clear the existing axes
        # self.ax.clear()
        for ax in self.fig.axes:
            self.fig.delaxes(ax)
        
        # Call the function that generates the particles and the plot (side effect)
        particles = self.get_subpixel_bias()

        if particles is None:
            self.ax.set_title("Error: No particles found or frames loaded.")
            self.canvas.draw()
            return

        # capture the figure created by tp.subpx_bias
        try:
            # tp.subpx_bias creates two subplots/axes: one for x, one for y
            temp_fig = plt.gcf()
            temp_axes = temp_fig.get_axes()
            temp_ax_x = temp_axes[0]
            temp_ax_y = temp_axes[1]
            
            # Determine the bin count used by the trackpy function
            N_BINS_X = len(temp_ax_x.patches) if temp_ax_x.patches else 25 
            N_BINS_Y = len(temp_ax_y.patches) if temp_ax_y.patches else 25
        except (IndexError, AttributeError):
            self.ax.set_title("No subpixel bias plot generated.")
            self.canvas.draw()
            if 'temp_fig' in locals() and temp_fig is not None:
                 plt.close(temp_fig)
            return

        # Extract data and properties from the temporary axes
        # --- Handle X-Bias Plot (first subplot) ---
        x_artist = temp_ax_x.patches[0] if temp_ax_x.patches else None
        
        if x_artist:
            # Re-create a subplot for the X-Bias plot on the embedded figure
            self.ax_x = self.fig.add_subplot(121) 
            
            # Plot the raw fractional data again
            x_color = temp_ax_x.patches[0].get_facecolor() if temp_ax_x.patches else 'lightblue'
            self.ax_x.hist(particles['x'].values % 1, bins=N_BINS_X, edgecolor='black', color=x_color)
            
            self.ax_x.set_title(temp_ax_x.get_title())
            self.ax_x.set_xlabel(temp_ax_x.get_xlabel())
            self.ax_x.set_ylabel(temp_ax_x.get_ylabel())
            self.ax_x.set_xlim(temp_ax_x.get_xlim())
            
        # --- Handle Y-Bias Plot (second subplot) ---
        y_artist = temp_ax_y.patches[0] if temp_ax_y.patches else None
        
        if y_artist:
            # Re-create a subplot for the Y-Bias plot on the embedded figure
            self.ax_y = self.fig.add_subplot(122) 

            # Plot the raw fractional data again
            y_color = temp_ax_y.patches[0].get_facecolor() if temp_ax_y.patches else 'salmon'
            self.ax_y.hist(particles['y'].values % 1, bins=N_BINS_Y, edgecolor='black', color=y_color)

            self.ax_y.set_title(temp_ax_y.get_title())
            self.ax_y.set_xlabel(temp_ax_y.get_xlabel())
            self.ax_y.set_ylabel(temp_ax_y.get_ylabel())
            self.ax_y.set_xlim(temp_ax_y.get_xlim())
            
        # The original axes (self.ax) is now unused/blank, so remove it
        if len(self.fig.axes) > 2:
             self.fig.delaxes(self.ax)
             # Reassign self.ax to the first new subplot for future clearing
             self.ax = self.ax_x 

        # Close the temporary figure
        plt.close(temp_fig)
        
        # Redraw the canvas
        self.canvas.draw()

    def get_subpixel_bias(self):
        # Get parameters
        params = get_detection_params() 
        config = get_config()
        frames_folder = config.get('frames_folder', 'frames/')
        
        # Check if frames exist
        if not os.path.exists(frames_folder):
            print(f"Frames folder not found: {frames_folder}")
            return
        
        # Get all frame files
        frame_files = []
        for filename in sorted(os.listdir(frames_folder)):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff')):
                frame_files.append(os.path.join(frames_folder, filename))
        
        if not frame_files:
            print("No frame files found in frames folder")
            return
        
        # Check if frames exist (and similar file handling)
        if not os.path.exists(frames_folder) or not frame_files:
            print(f"Frames issue. Folder: {os.path.exists(frames_folder)}, Files: {len(frame_files) if frame_files else 0}")
            return None
            
        try:
            import trackpy as tp
            import cv2
            import pandas as pd

            # Get detection parameters
            feature_size = int(params.get('feature_size', 15))
            min_mass = float(params.get('min_mass', 100.0))
            invert = bool(params.get('invert', False))
            threshold = float(params.get('threshold', 0.0))
            frame_idx = int(params.get('frame_idx', 0))
            frame_idx = int(params.get('frame_idx', 0))

            if frame_idx >= len(frame_files):
                frame_idx = 0 
                
            frame_file = frame_files[frame_idx]

            for frame_num, frame_file in enumerate(frame_files):
                if frame_num == frame_idx:
                    frame = cv2.imread(frame_file)
                    if frame is None:
                        continue
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    # tp.locate returns the pandas DataFrame
                    particles = tp.locate(
                            gray,
                            diameter=feature_size,
                            minmass=min_mass,
                            invert=invert,
                            threshold=threshold
                        )
                    
                    # Check if particles were found before plotting
                    if particles.empty:
                        print("No particles detected in the selected frame.")
                        return None # Return None if nothing was found

                    # Create the plot 
                    tp.subpx_bias(particles)
                    
                    # Return the DataFrame
                    return particles 

        except Exception as e:
            print(f"Error in particle locating or plotting: {e}")
            return None
