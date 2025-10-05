from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox, QPushButton
from PySide6.QtCore import Qt, Signal
from config_parser import *
import os
import particle_tracking
import pandas as pd

class LinkingParametersWidget(QWidget):
    particlesDetected = Signal()
    trajectoriesLinked = Signal()
    trajectoryVisualizationCreated = Signal(str)  # Emits image path
    rbGalleryCreated = Signal()  # Signal that RB gallery was created
    goBackToDetection = Signal()  # Signal to go back to detection window
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Store detected particles and linked trajectories
        self.detected_particles = None
        self.linked_trajectories = None

        self.layout = QVBoxLayout(self)

        self.form = QFormLayout()

        # Inputs for trajectory linking parameters
        self.search_range_input = QSpinBox()
        self.search_range_input.setRange(1, 1000)
        self.search_range_input.setSingleStep(1)
        self.search_range_input.setToolTip("Maximum distance a particle can move between frames (pixels).")

        self.memory_input = QSpinBox()
        self.memory_input.setRange(0, 100)
        self.memory_input.setSingleStep(1)
        self.memory_input.setToolTip("Number of frames a particle can disappear and still be linked.")

        self.min_trajectory_length_input = QSpinBox()
        self.min_trajectory_length_input.setRange(1, 1000)
        self.min_trajectory_length_input.setSingleStep(1)
        self.min_trajectory_length_input.setToolTip("Minimum number of frames for a valid trajectory.")

        self.fps_input = QDoubleSpinBox()
        self.fps_input.setDecimals(2)
        self.fps_input.setRange(0.1, 1000.0)
        self.fps_input.setSingleStep(1.0)
        self.fps_input.setToolTip("Frames per second of the video.")

        self.scaling_input = QDoubleSpinBox()
        self.scaling_input.setDecimals(6)
        self.scaling_input.setRange(0.000001, 1000.0)
        self.scaling_input.setSingleStep(0.1)
        self.scaling_input.setToolTip("Microns per pixel (calibration).")

        self.max_speed_input = QDoubleSpinBox()
        self.max_speed_input.setDecimals(2)
        self.max_speed_input.setRange(0.1, 10000.0)
        self.max_speed_input.setSingleStep(10.0)
        self.max_speed_input.setToolTip("Maximum expected particle speed (microns/second).")

        self.form.addRow("Search range", self.search_range_input)
        self.form.addRow("Memory", self.memory_input)
        self.form.addRow("Min trajectory length", self.min_trajectory_length_input)
        self.form.addRow("FPS", self.fps_input)
        self.form.addRow("Scaling (μm/pixel)", self.scaling_input)
        self.form.addRow("Max speed (μm/s)", self.max_speed_input)

        self.layout.addLayout(self.form)

        # Buttons
        self.buttons_layout = QVBoxLayout()
        
        self.find_trajectories_button = QPushButton("Find Trajectories")
        self.find_trajectories_button.clicked.connect(self.find_trajectories)
        self.buttons_layout.addWidget(self.find_trajectories_button, alignment=Qt.AlignRight)
        
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        self.buttons_layout.addWidget(self.back_button, alignment=Qt.AlignRight)
        
        self.layout.addLayout(self.buttons_layout)

        # Load existing values
        self.load_params()

        # Save on Enter / editing finished
        self.search_range_input.editingFinished.connect(self.save_params)
        self.memory_input.editingFinished.connect(self.save_params)
        self.min_trajectory_length_input.editingFinished.connect(self.save_params)
        self.fps_input.editingFinished.connect(self.save_params)
        self.scaling_input.editingFinished.connect(self.save_params)
        self.max_speed_input.editingFinished.connect(self.save_params)
        # Also catch Return in the embedded line edits
        self.search_range_input.lineEdit().returnPressed.connect(self.save_params)
        self.memory_input.lineEdit().returnPressed.connect(self.save_params)
        self.min_trajectory_length_input.lineEdit().returnPressed.connect(self.save_params)
        self.fps_input.lineEdit().returnPressed.connect(self.save_params)
        self.scaling_input.lineEdit().returnPressed.connect(self.save_params)
        self.max_speed_input.lineEdit().returnPressed.connect(self.save_params)

    def load_params(self):
        params = get_linking_params()
        self.search_range_input.setValue(int(params.get('search_range', 10)))
        self.memory_input.setValue(int(params.get('memory', 10)))
        self.min_trajectory_length_input.setValue(int(params.get('min_trajectory_length', 10)))
        self.fps_input.setValue(float(params.get('fps', 30.0)))
        self.scaling_input.setValue(float(params.get('scaling', 1.0)))
        self.max_speed_input.setValue(float(params.get('max_speed', 100.0)))

    def save_params(self):
        params = {
            'search_range': int(self.search_range_input.value()),
            'memory': int(self.memory_input.value()),
            'min_trajectory_length': int(self.min_trajectory_length_input.value()),
            'fps': float(self.fps_input.value()),
            'scaling': float(self.scaling_input.value()),
            'max_speed': float(self.max_speed_input.value()),
        }
        save_linking_params(params)

    def find_trajectories(self):
        """Load detected particles and link them into trajectories."""
        # Ensure latest linking parameters are saved
        self.save_params()
        
        # Get linking parameters
        linking_params = get_linking_params()
        config = get_config()
        particles_folder = config.get('particles_folder', 'particles/')
        
        # Check if particles file exists
        particles_file = os.path.join(particles_folder, 'all_particles.csv')
        if not os.path.exists(particles_file):
            print(f"Particles file not found: {particles_file}")
            print("Please run 'Next' in the particle detection window first.")
            return
        
        try:
            import trackpy as tp
            import pandas as pd
            
            # Load detected particles
            print("Loading detected particles...")
            self.detected_particles = pd.read_csv(particles_file)
            print(f"Loaded {len(self.detected_particles)} particles across {self.detected_particles['frame'].nunique()} frames")
            
            # Get linking parameters
            search_range = int(linking_params.get('search_range', 10))
            memory = int(linking_params.get('memory', 10))
            min_trajectory_length = int(linking_params.get('min_trajectory_length', 10))
            
            print(f"Linking particles with search_range={search_range}, memory={memory}")
            
            # Link particles into trajectories
            trajectories = tp.link_df(
                self.detected_particles,
                search_range=search_range,
                memory=memory
            )
            
            print(f"Created {trajectories['particle'].nunique()} trajectories")
            
            # Filter short trajectories
            print(f"Filtering trajectories shorter than {min_trajectory_length} frames...")
            trajectories_filtered = tp.filter_stubs(trajectories, min_trajectory_length)
            
            print(f"After filtering: {trajectories_filtered['particle'].nunique()} trajectories")
            
            # Store the linked trajectories
            self.linked_trajectories = trajectories_filtered
            
            # Save trajectories
            trajectories_file = os.path.join(particles_folder, 'trajectories.csv')
            trajectories_filtered.to_csv(trajectories_file, index=False)
            print(f"Saved trajectories to: {trajectories_file}")
            
            # Create trajectory visualization
            self.create_trajectory_visualization(trajectories_filtered, particles_folder)
            
            # Create RB gallery for trajectory validation
            self.create_rb_gallery(trajectories_file, particles_folder)
            
            # Emit signals
            self.trajectoriesLinked.emit()
            self.rbGalleryCreated.emit()
            
        except Exception as e:
            print(f"Error linking trajectories: {e}")
            self.linked_trajectories = None

    def create_trajectory_visualization(self, trajectories_df, output_folder):
        """Create a trajectory visualization on white background and save as image."""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Get image dimensions from first frame
            config = get_config()
            frames_folder = config.get('frames_folder', 'frames/')
            frame_files = []
            for filename in sorted(os.listdir(frames_folder)):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff')):
                    frame_files.append(os.path.join(frames_folder, filename))
                    break  # Just need first frame for dimensions
            
            if frame_files:
                import cv2
                first_frame = cv2.imread(frame_files[0])
                if first_frame is not None:
                    height, width = first_frame.shape[:2]
                else:
                    height, width = 800, 600  # Default dimensions
            else:
                height, width = 800, 600  # Default dimensions
            
            # Create figure with white background
            fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            
            # Plot trajectories
            unique_particles = trajectories_df['particle'].unique()
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_particles)))
            
            for i, particle_id in enumerate(unique_particles):
                particle_data = trajectories_df[trajectories_df['particle'] == particle_id]
                x_coords = particle_data['x'].values
                y_coords = particle_data['y'].values
                
                # Plot trajectory line
                ax.plot(x_coords, y_coords, color=colors[i % len(colors)], 
                       linewidth=1.5, alpha=0.7, label=f'Particle {particle_id}')
                
                # Plot start point
                if len(x_coords) > 0:
                    ax.plot(x_coords[0], y_coords[0], 'o', color=colors[i % len(colors)], 
                           markersize=4, markeredgecolor='black', markeredgewidth=0.5)
            
            # Set axis properties
            ax.set_xlim(0, width)
            ax.set_ylim(height, 0)  # Invert y-axis to match image coordinates
            ax.set_aspect('equal')
            ax.set_xlabel('X (pixels)')
            ax.set_ylabel('Y (pixels)')
            ax.set_title('Particle Trajectories')
            
            # Remove top and right spines for cleaner look
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Save the visualization
            trajectory_image_path = os.path.join(output_folder, 'trajectory_visualization.png')
            plt.savefig(trajectory_image_path, dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            print(f"Trajectory visualization saved to: {trajectory_image_path}")
            
            # Emit signal with image path for display
            self.trajectoryVisualizationCreated.emit(trajectory_image_path)
            
        except Exception as e:
            print(f"Error creating trajectory visualization: {e}")

    def create_rb_gallery(self, trajectories_file, particles_folder):
        """Create RB gallery using particle_processing function."""
        try:
            import particle_processing
            config = get_config()
            frames_folder = config.get('frames_folder', 'frames/')
            
            # Call the RB gallery creation function
            particle_processing.create_rb_gallery(
                trajectories_file=trajectories_file,
                frames_folder=frames_folder,
                output_folder=os.path.join(particles_folder, 'rb_gallery')
            )
            
        except Exception as e:
            print(f"Error creating RB gallery: {e}")

    def go_back(self):
        """Emit signal to go back to particle detection window."""
        self.goBackToDetection.emit()
