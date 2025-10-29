from PySide6.QtCore import QObject, Signal, QThread
from . import particle_processing
import trackpy as tp
import os

class FindParticlesThread(QThread):
    processing_frame = Signal(str)
    finished = Signal()
    particles_found = Signal(object)
    error = Signal(str)

    def __init__(self, frame_paths, params):
        super().__init__()
        self.frame_paths = frame_paths
        self.params = params
        self.particles = None

    def run(self):
        try:
            self.particles = particle_processing.find_and_save_errant_particles(
                self.frame_paths,
                self.params,
                progress_callback=self.processing_frame
            )
            self.particles_found.emit(self.particles)
        except Exception as e:
            self.error.emit(f"Error finding particles: {e}")
        finally:
            self.finished.emit()
    
    def get_particles(self):
        return self.particles

class DetectAllFramesThread(QThread):
    processing_frame = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, frame_paths, params, file_controller):
        super().__init__()
        self.frame_paths = frame_paths
        self.params = params
        self.file_controller = file_controller

    def run(self):
        try:
            import pandas as pd
            import cv2
            
            annotated_frames_folder = self.file_controller.annotated_frames_folder
            data_folder = self.file_controller.data_folder

            feature_size = int(self.params.get('feature_size', 15))
            min_mass = float(self.params.get('min_mass', 100.0))
            invert = bool(self.params.get('invert', False))
            threshold = float(self.params.get('threshold', 0.0))

            if feature_size % 2 == 0:
                feature_size += 1

            all_particles = []
            for frame_idx, frame_file in enumerate(self.frame_paths):
                frame_num = int(os.path.splitext(os.path.basename(frame_file))[0].split('_')[-1])
                self.processing_frame.emit(f"Processing remaining frame {frame_num}")
                
                frame = cv2.imread(frame_file)
                if frame is None:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                particles = tp.locate(gray, diameter=feature_size, minmass=min_mass, invert=invert, threshold=threshold)
                particles['frame'] = frame_num
                all_particles.append(particles)

                if not particles.empty:
                    annotated_image = frame.copy()
                    for index, particle in particles.iterrows():
                        cv2.circle(annotated_image, (int(particle.x), int(particle.y)), int(feature_size/2) + 2, (0, 255, 255), 2)
                    annotated_frame_path = os.path.join(annotated_frames_folder, f"frame_{frame_num:05d}.jpg")
                    cv2.imwrite(annotated_frame_path, annotated_image)

            if all_particles:
                combined_particles = pd.concat(all_particles, ignore_index=True)
                os.makedirs(data_folder, exist_ok=True)
                particles_file = os.path.join(data_folder, 'all_particles.csv')
                
                if os.path.exists(particles_file):
                    existing_df = pd.read_csv(particles_file)
                    combined_particles = pd.concat([existing_df, combined_particles], ignore_index=True)
                
                combined_particles.to_csv(particles_file, index=False)

        except Exception as e:
            self.error.emit(f"Error in DetectAllFramesThread: {e}")
        finally:
            self.finished.emit()

class ParticleDetectionService(QObject):
    processing_frame = Signal(str)
    particles_found = Signal(object)
    find_finished = Signal()
    detect_all_finished = Signal()
    error = Signal(str)

    def __init__(self, file_controller):
        super().__init__()
        self.file_controller = file_controller
        self.find_particles_thread = None
        self.detect_all_thread = None

    def find_particles(self, params, frame_paths):
        self.find_particles_thread = FindParticlesThread(frame_paths, params)
        self.find_particles_thread.processing_frame.connect(self.processing_frame)
        self.find_particles_thread.particles_found.connect(self.particles_found)
        self.find_particles_thread.finished.connect(self.find_finished)
        self.find_particles_thread.error.connect(self.error)
        self.find_particles_thread.start()

    def detect_all_frames(self, params, frame_paths):
        self.detect_all_thread = DetectAllFramesThread(frame_paths, params, self.file_controller)
        self.detect_all_thread.processing_frame.connect(self.processing_frame)
        self.detect_all_thread.finished.connect(self.detect_all_finished)
        self.detect_all_thread.error.connect(self.error)
        self.detect_all_thread.start()

class TrajectoryLinkingService(QObject):
    trajectories_linked = Signal(object)
    trajectory_visualization_created = Signal(str)
    rb_gallery_created = Signal()
    linking_finished = Signal()
    error = Signal(str)

    def __init__(self, file_controller):
        super().__init__()
        self.file_controller = file_controller
        self.linking_thread = None

    def find_trajectories(self, params):
        self.linking_thread = TrajectoryLinkingThread(params, self.file_controller)
        self.linking_thread.trajectories_linked.connect(self.trajectories_linked)
        self.linking_thread.trajectory_visualization_created.connect(self.trajectory_visualization_created)
        self.linking_thread.rb_gallery_created.connect(self.rb_gallery_created)
        self.linking_thread.finished.connect(self.linking_finished)
        self.linking_thread.error.connect(self.error)
        self.linking_thread.start()

class TrajectoryLinkingThread(QThread):
    trajectories_linked = Signal(object)
    trajectory_visualization_created = Signal(str)
    rb_gallery_created = Signal()
    error = Signal(str)
    finished = Signal()

    def __init__(self, params, file_controller):
        super().__init__()
        self.params = params
        self.file_controller = file_controller

    def run(self):
        try:
            import pandas as pd
            import trackpy as tp
            import matplotlib.pyplot as plt
            import numpy as np
            import cv2

            data_folder = self.file_controller.data_folder
            particles_file = os.path.join(data_folder, 'all_particles.csv')
            if not os.path.exists(particles_file):
                print(f"Particles file not found: {particles_file}")
                return

            detected_particles = pd.read_csv(particles_file)
            
            search_range = int(self.params.get('search_range', 10))
            memory = int(self.params.get('memory', 10))
            min_trajectory_length = int(self.params.get('min_trajectory_length', 10))
            
            trajectories = tp.link_df(
                detected_particles,
                search_range=search_range,
                memory=memory
            )
            
            trajectories_filtered = tp.filter_stubs(trajectories, min_trajectory_length)
            
            trajectories_file = os.path.join(data_folder, 'trajectories.csv')
            trajectories_filtered.to_csv(trajectories_file, index=False)
            
            self.trajectories_linked.emit(trajectories_filtered)

            # Create trajectory visualization
            self.create_trajectory_visualization(trajectories_filtered, data_folder)
            
            # Create RB gallery
            self.create_rb_gallery(trajectories_file, data_folder)

        except Exception as e:
            self.error.emit(f"Error linking trajectories: {e}")
        finally:
            self.finished.emit()
        finally:
            self.finished.emit()

    def create_trajectory_visualization(self, trajectories_df, output_folder):
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import cv2

            original_frames_folder = self.file_controller.original_frames_folder
            frame_files = []
            for filename in sorted(os.listdir(original_frames_folder)):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff')):
                    frame_files.append(os.path.join(original_frames_folder, filename))
                    break
            
            if frame_files:
                first_frame = cv2.imread(frame_files[0])
                if first_frame is not None:
                    height, width = first_frame.shape[:2]
                else:
                    height, width = 800, 600
            else:
                height, width = 800, 600
            
            fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            
            unique_particles = trajectories_df['particle'].unique()
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_particles)))
            
            for i, particle_id in enumerate(unique_particles):
                particle_data = trajectories_df[trajectories_df['particle'] == particle_id]
                x_coords = particle_data['x'].values
                y_coords = particle_data['y'].values
                
                ax.plot(x_coords, y_coords, color=colors[i % len(colors)], linewidth=1.5, alpha=0.7, label=f'Particle {particle_id}')
                
                if len(x_coords) > 0:
                    ax.plot(x_coords[0], y_coords[0], 'o', color=colors[i % len(colors)], markersize=4, markeredgecolor='black', markeredgewidth=0.5)
            
            ax.set_xlim(0, width)
            ax.set_ylim(height, 0)
            ax.set_aspect('equal')
            ax.set_xlabel('X (pixels)')
            ax.set_ylabel('Y (pixels)')
            ax.set_title('Particle Trajectories')
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            trajectory_image_path = os.path.join(output_folder, 'trajectory_visualization.png')
            plt.savefig(trajectory_image_path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
            plt.close(fig)
            
            self.trajectory_visualization_created.emit(trajectory_image_path)
            
        except Exception as e:
            print(f"Error creating trajectory visualization: {e}")

    def create_rb_gallery(self, trajectories_file, data_folder):
        try:
            original_frames_folder = self.file_controller.original_frames_folder
            rb_gallery_folder = self.file_controller.rb_gallery_folder
            
            particle_processing.create_rb_gallery(
                trajectories_file=trajectories_file,
                frames_folder=original_frames_folder,
                output_folder=rb_gallery_folder
            )
            self.rb_gallery_created.emit()
        except Exception as e:
            print(f"Error creating RB gallery: {e}")
