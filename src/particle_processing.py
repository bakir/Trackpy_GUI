"""
Particle Processing Module

Description: Core particle processing functions for detection, cropping, and RB gallery creation.
             Initial functions written using Cursor.

"""

import cv2
import os
import numpy as np
import pandas as pd
from . import particle_tracking
from .config_parser import get_config, get_detection_params
import matplotlib.pyplot as plt
import trackpy as tp

config = get_config()
PARTICLES_FOLDER = config.get('particles_folder', 'particles/')
ANNOTATED_FRAMES_FOLDER = config.get('annotated_frames_folder', 'annotated_frames/')

def delete_all_files_in_folder(folder_path):
    """
    Deletes all files within a specified folder.

    Args:
        folder_path (str): The path to the folder.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):  # Ensure it's a file, not a subdirectory
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except OSError as e:
                print(f"Error deleting {file_path}: {e}")

def find_and_save_errant_particles(image_paths, params=None, progress_callback=None):
    """
    Finds particles in a series of images and saves cropped images of the 5 most errant ones.

    Parameters
    ----------
    image_paths : list of str
        The paths to the image files.
    progress_callback : Signal, optional
        A signal to emit progress updates.
    """
    delete_all_files_in_folder(PARTICLES_FOLDER)

    if not os.path.exists(PARTICLES_FOLDER):
        os.makedirs(PARTICLES_FOLDER)
    if not os.path.exists(ANNOTATED_FRAMES_FOLDER):
        os.makedirs(ANNOTATED_FRAMES_FOLDER)

    if params is None:
        params = get_detection_params()
    feature_size = int(params.get('feature_size', 15))
    min_mass = float(params.get('min_mass', 100.0))
    invert = bool(params.get('invert', False))
    threshold = float(params.get('threshold', 0.0))

    if feature_size % 2 == 0:
        feature_size += 1

    all_features = []
    original_images = {}

    for frame_idx, image_path in enumerate(image_paths):
        basename = os.path.basename(image_path)
        name_part = os.path.splitext(basename)[0]
        frame_number_str = name_part.split('_')[-1]
        frame_number = int(frame_number_str)

        if progress_callback:
            progress_callback.emit(f"Processing Frame {frame_number}")
        
        image = cv2.imread(image_path)
        if image is None:
            continue
        
        original_images[frame_idx] = image
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        features = particle_tracking.locate_particles(
            gray_image,
            feature_size=feature_size,
            min_mass=min_mass,
            invert=invert,
            threshold=threshold
        )
        features['frame'] = frame_idx
        all_features.append(features)

        # Annotate and save frame
        if not features.empty:
            annotated_image = image.copy()
            for index, particle in features.iterrows():
                cv2.circle(annotated_image, (int(particle.x), int(particle.y)), int(feature_size/2) + 2, (0, 255, 255), 2)
            annotated_frame_path = os.path.join(ANNOTATED_FRAMES_FOLDER, f"frame_{frame_number:05d}.jpg")
            cv2.imwrite(annotated_frame_path, annotated_image)

    if not all_features:
        if progress_callback:
            progress_callback.emit("No particles found.")
        return pd.DataFrame()

    combined_features = pd.concat(all_features, ignore_index=True)

    if not combined_features.empty:
        combined_features['mass_diff'] = combined_features['mass'] - min_mass
        top_5_particles = combined_features.nsmallest(5, 'mass_diff')

        for i, particle in top_5_particles.iterrows():
            frame_idx = int(particle['frame'])
            image_to_crop = original_images.get(frame_idx)
            if image_to_crop is None:
                continue

            x, y, size = particle['x'], particle['y'], particle['size']
            padding = 5
            half_size = int(size) + padding
            x_min = max(0, int(x) - half_size)
            y_min = max(0, int(y) - half_size)
            x_max = min(image_to_crop.shape[1], int(x) + half_size)
            y_max = min(image_to_crop.shape[0], int(y) + half_size)

            particle_image = image_to_crop[y_min:y_max, x_min:x_max]

            center_x = int(x) - x_min
            center_y = int(y) - y_min
            cross_size = 5
            cv2.line(particle_image, (center_x - cross_size, center_y), (center_x + cross_size, center_y), (255, 255, 255), 1)
            cv2.line(particle_image, (center_x, center_y - cross_size), (center_x, center_y + cross_size), (255, 255, 255), 1)

            base_filename = f"particle_{i}"
            particle_filename = os.path.join(PARTICLES_FOLDER, f"{base_filename}.png")
            cv2.imwrite(particle_filename, particle_image)

            mass_info_filename = os.path.join(PARTICLES_FOLDER, f"{base_filename}.txt")
            with open(mass_info_filename, 'w') as f:
                f.write(f"mass: {particle['mass']:.2f}\n")
                f.write(f"min_mass: {min_mass}\n")

    if progress_callback:
        progress_callback.emit("Done.")

    return combined_features

def create_rb_gallery(trajectories_file, original_frames_folder, output_folder=None):
    """
    Creates red-blue overlay images to visualize particle linking between frames.
    
    Parameters
    ----------
    trajectories_file : str
        Path to the CSV file containing trajectory data
    original_frames_folder : str
        Path to the folder containing frame images
    output_folder : str, optional
        Path to save the RB gallery images. If None, uses rb_gallery/
    """
    import pandas as pd
    from config_parser import get_config
    
    if output_folder is None:
        config = get_config()
        output_folder = config.get('rb_gallery_folder', 'rb_gallery')
    
    # Create output directory
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
        # Clear existing files
        delete_all_files_in_folder(output_folder)
    
    # Load trajectory data
    try:
        trajectories = pd.read_csv(trajectories_file)
    except Exception as e:
        print(f"Error loading trajectories: {e}")
        return
    
    if len(trajectories) == 0:
        print("No trajectory data found")
        return
    
    # Get frame files
    frame_files = []
    for filename in sorted(os.listdir(original_frames_folder)):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff')):
            frame_files.append(os.path.join(original_frames_folder, filename))
    
    if len(frame_files) < 2:
        print("Need at least 2 frames for RB overlay")
        return
    
    print(f"Creating RB gallery with {len(frame_files)} frames...")
    
    # Process each particle trajectory
    unique_particles = trajectories['particle'].unique()
    crop_size = 100  # Size of the crop around each particle
    
    for particle_id in unique_particles:
        particle_data = trajectories[trajectories['particle'] == particle_id].sort_values('frame')
        
        if len(particle_data) < 2:
            continue  # Skip particles with only one detection
        
        # Get first and last frame positions for this particle
        first_frame = particle_data.iloc[0]
        last_frame = particle_data.iloc[-1]
        
        frame1_idx = int(first_frame['frame'])
        frame2_idx = int(last_frame['frame'])
        
        # Skip if same frame
        if frame1_idx == frame2_idx:
            continue
        
        # Skip if frame indices are out of range
        if frame1_idx >= len(frame_files) or frame2_idx >= len(frame_files):
            continue
        
        try:
            # Load the two frames
            frame1 = cv2.imread(frame_files[frame1_idx])
            frame2 = cv2.imread(frame_files[frame2_idx])
            
            if frame1 is None or frame2 is None:
                continue
            
            # Get particle positions
            x1, y1 = int(first_frame['x']), int(first_frame['y'])
            x2, y2 = int(last_frame['x']), int(last_frame['y'])
            
            # Calculate crop boundaries for frame1
            x1_min = max(0, x1 - crop_size // 2)
            y1_min = max(0, y1 - crop_size // 2)
            x1_max = min(frame1.shape[1], x1 + crop_size // 2)
            y1_max = min(frame1.shape[0], y1 + crop_size // 2)
            
            # Calculate crop boundaries for frame2
            x2_min = max(0, x2 - crop_size // 2)
            y2_min = max(0, y2 - crop_size // 2)
            x2_max = min(frame2.shape[1], x2 + crop_size // 2)
            y2_max = min(frame2.shape[0], y2 + crop_size // 2)
            
            # Crop the frames
            crop1 = frame1[y1_min:y1_max, x1_min:x1_max]
            crop2 = frame2[y2_min:y2_max, x2_min:x2_max]
            
            # Resize crops to same size if needed
            target_size = (crop_size, crop_size)
            crop1 = cv2.resize(crop1, target_size)
            crop2 = cv2.resize(crop2, target_size)
            
            # Create red and blue overlay at 50% opacity each
            # Convert to grayscale for better color overlay effect
            gray1 = cv2.cvtColor(crop1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(crop2, cv2.COLOR_BGR2GRAY)
            
            # Create RGB overlay with better color separation
            rb_overlay = np.zeros((crop_size, crop_size, 3), dtype=np.uint8)
            
            # Red channel: frame1 grayscale (will appear red)
            rb_overlay[:, :, 0] = gray1
            
            # Green channel: minimal to avoid washing out colors
            rb_overlay[:, :, 1] = np.minimum(gray1, gray2) // 4  # Very low green
            
            # Blue channel: frame2 grayscale (will appear blue)
            rb_overlay[:, :, 2] = gray2
            
            # Draw particle centers
            center = crop_size // 2
            cv2.circle(rb_overlay, (center, center), 3, (255, 255, 255), -1)  # White center dot
            
            # Add frame information text
            cv2.putText(rb_overlay, f'F{frame1_idx}', (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)  # Red text
            cv2.putText(rb_overlay, f'F{frame2_idx}', (5, crop_size - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)  # Blue text
            
            # Save the RB overlay image
            output_filename = os.path.join(output_folder, f'particle_{particle_id}_rb_overlay.png')
            cv2.imwrite(output_filename, rb_overlay)
            
        except Exception as e:
            print(f"Error processing particle {particle_id}: {e}")
            continue
    
    print(f"RB gallery created in: {output_folder}")
    print(f"Processed {len(unique_particles)} particles")
