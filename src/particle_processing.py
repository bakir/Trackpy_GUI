"""
Particle Processing Module

Description: Combined particle detection, tracking, and processing functions.
             Includes TrackPy wrapper functions and particle processing workflows.
"""

import cv2
import os
import numpy as np
import pandas as pd
import trackpy as tp
import pims
import matplotlib.pyplot as plt
from .config_parser import get_config
from .file_controller import FileController

# Initialize file controller (will be set by main application)
file_controller = None

def set_file_controller(controller):
    """Set the file controller instance."""
    global file_controller
    file_controller = controller


# =============================================================================
# TRACKPY WRAPPER FUNCTIONS
# =============================================================================

@pims.pipeline
def grayscale(frame):
    """Converts a frame to grayscale."""
    # This function is for use with pims pipelines, which expect RGB.
    # For single frames with OpenCV, use cv2.cvtColor.
    red = frame[:, :, 0]
    green = frame[:, :, 1]
    blue = frame[:, :, 2]
    return (1/3.0) * red + (1/3.0) * green + (1/3.0) * blue


def locate_particles(frame, feature_size=15, min_mass=100, invert=False, threshold=0):
    """
    Locates bright spots (particles) in a single grayscale frame.

    Parameters
    ----------
    frame : array
        A single grayscale frame from a video.
    feature_size : int, optional
        The approximate diameter of features to detect. Must be an odd integer.
    min_mass : float, optional
        The minimum integrated brightness of a feature.
    invert : bool, optional
        Set to True if looking for dark spots on a bright background.
    threshold : float, optional
        Clip band-passed data below this value.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with the coordinates and other properties of the located particles.
    """
    located_features = tp.locate(
        frame,
        diameter=feature_size,
        minmass=min_mass,
        invert=invert,
        threshold=threshold
    )
    return located_features


def link_particles_to_trajectories(video_path, output_folder=None, params=None):
    """
    Main function to detect particles in all frames and link them into trajectories.
    
    Parameters
    ----------
    video_path : str
        Path to the video file to analyze
    output_folder : str, optional
        Folder to save trajectory data. If None, uses data folder from config.
    params : dict, optional
        Detection parameters. If None, reads from config.ini
        
    Returns
    -------
    pandas.DataFrame
        DataFrame with linked trajectories containing columns:
        - x, y: particle coordinates
        - frame: frame number
        - particle: trajectory ID
        - mass, size, ecc: particle properties
    """
    if params is None:
        params = get_detection_params()
    
    if output_folder is None:
        output_folder = file_controller.data_folder
    
    # Ensure output folder exists
    file_controller.ensure_folder_exists(output_folder)
    
    # Load video
    try:
        video = pims.Video(video_path)
    except Exception as e:
        print(f"Error loading video: {e}")
        return None
    
    print(f"Processing video with {len(video)} frames...")
    
    # Get detection parameters
    feature_size = int(params.get('feature_size', 15))
    min_mass = float(params.get('min_mass', 100.0))
    invert = bool(params.get('invert', False))
    threshold = float(params.get('threshold', 0.0))
    
    # Ensure odd feature size as required by trackpy
    if feature_size % 2 == 0:
        feature_size += 1
    
    # Step 1: Detect particles in all frames
    print("Detecting particles in all frames...")
    try:
        # Use trackpy's batch function for efficient processing
        particles = tp.batch(
            video, 
            diameter=feature_size, 
            minmass=min_mass, 
            invert=invert, 
            threshold=threshold,
            processes=1  # Use single process to avoid multiprocessing issues
        )
    except Exception as e:
        print(f"Error in particle detection: {e}")
        return None
    
    print(f"Found {len(particles)} particle detections across {particles['frame'].nunique()} frames")
    
    if len(particles) == 0:
        print("No particles detected!")
        return None
    
    # Step 2: Link particles into trajectories
    print("Linking particles into trajectories...")
    
    # Calculate search range based on expected particle speed
    # Assuming max speed of ~100 microns/second and typical fps
    fps = 30  # Default fps, could be extracted from video
    scaling = 1.0  # microns per pixel, could be from config
    max_speed_um_per_sec = 100
    search_range = int(np.ceil(max_speed_um_per_sec / (fps * scaling)))
    
    # Memory parameter: how many frames a particle can disappear and still be linked
    memory = 10
    
    try:
        trajectories = tp.link_df(
            particles, 
            search_range=search_range, 
            memory=memory
        )
    except Exception as e:
        print(f"Error in trajectory linking: {e}")
        return None
    
    print(f"Created {trajectories['particle'].nunique()} trajectories")
    
    # Step 3: Filter short trajectories
    min_trajectory_length = 10
    print(f"Filtering trajectories shorter than {min_trajectory_length} frames...")
    
    trajectories_filtered = tp.filter_stubs(trajectories, min_trajectory_length)
    
    print(f"After filtering: {trajectories_filtered['particle'].nunique()} trajectories")
    
    # Step 4: Drift subtraction (optional but recommended)
    print("Computing and subtracting drift...")
    try:
        # Compute drift
        drift = tp.compute_drift(trajectories_filtered, smoothing=15)
        
        # Subtract drift
        trajectories_final = tp.subtract_drift(trajectories_filtered, drift)
        trajectories_final = trajectories_final.reset_index(drop=True)
        
        print("Drift subtraction completed")
    except Exception as e:
        print(f"Warning: Drift subtraction failed: {e}")
        print("Using trajectories without drift subtraction")
        trajectories_final = trajectories_filtered
    
    # Step 5: Save results using FileController
    file_controller.save_trajectories_data(trajectories_final, "trajectories.csv")
    
    return trajectories_final


def analyze_trajectories(trajectories_df, scaling=1.0, fps=30):
    """
    Analyze linked trajectories to compute MSD and other metrics.
    
    Parameters
    ----------
    trajectories_df : pandas.DataFrame
        DataFrame with trajectory data from link_particles_to_trajectories
    scaling : float
        Microns per pixel
    fps : float
        Frames per second
        
    Returns
    -------
    dict
        Dictionary containing analysis results
    """
    if trajectories_df is None or len(trajectories_df) == 0:
        return None
    
    results = {}
    
    # Compute ensemble mean square displacement (eMSD)
    try:
        emsd = tp.emsd(trajectories_df, mpp=scaling, fps=fps, max_lagtime=100)
        results['emsd'] = emsd
        print("Computed ensemble MSD")
    except Exception as e:
        print(f"Error computing eMSD: {e}")
    
    # Compute individual MSD (iMSD) 
    try:
        imsd = tp.imsd(trajectories_df, mpp=scaling, fps=fps, max_lagtime=100)
        results['imsd'] = imsd
        print("Computed individual MSD")
    except Exception as e:
        print(f"Error computing iMSD: {e}")
    
    # Basic statistics
    results['num_trajectories'] = trajectories_df['particle'].nunique()
    results['num_frames'] = trajectories_df['frame'].nunique()
    results['total_detections'] = len(trajectories_df)
    
    # Trajectory lengths
    traj_lengths = trajectories_df.groupby('particle').size()
    results['mean_trajectory_length'] = traj_lengths.mean()
    results['std_trajectory_length'] = traj_lengths.std()
    
    print(f"Analysis complete:")
    print(f"  - {results['num_trajectories']} trajectories")
    print(f"  - {results['num_frames']} frames")
    print(f"  - Mean trajectory length: {results['mean_trajectory_length']:.1f} frames")
    
    return results


# =============================================================================
# PARTICLE PROCESSING FUNCTIONS
# =============================================================================

def find_and_save_particles(image_paths, params=None, progress_callback=None):
    """
    Finds particles in a series of images and saves the data.

    Parameters
    ----------
    image_paths : list of str
        The paths to the image files.
    progress_callback : Signal, optional
        A signal to emit progress updates.
    """
    if params is None:
        params = get_detection_params()
    feature_size = int(params.get('feature_size', 15))
    min_mass = float(params.get('min_mass', 100.0))
    invert = bool(params.get('invert', False))
    threshold = float(params.get('threshold', 0.0))

    if feature_size % 2 == 0:
        feature_size += 1

    all_features = []

    for image_path in image_paths:
        basename = os.path.basename(image_path)
        name_part = os.path.splitext(basename)[0]
        frame_number_str = name_part.split('_')[-1]
        frame_number = int(frame_number_str)

        if progress_callback:
            progress_callback.emit(f"Processing Frame {frame_number}")
        
        image = cv2.imread(image_path)
        if image is None:
            continue
        
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        features = locate_particles(
            gray_image,
            feature_size=feature_size,
            min_mass=min_mass,
            invert=invert,
            threshold=threshold
        )
        features['frame'] = frame_number
        all_features.append(features)

    if not all_features:
        if progress_callback:
            progress_callback.emit("No particles found.")
        return pd.DataFrame()

    combined_features = pd.concat(all_features, ignore_index=True)

    if not combined_features.empty:
        file_controller.save_particles_data(combined_features, "found_particles.csv")

    if progress_callback:
        progress_callback.emit("Done.")

    return combined_features

def save_errant_particle_crops_for_frame(frame_number, particle_data_for_frame, params):
    """Saves cropped images of the 5 most errant particles for a given frame."""
    if file_controller is None:
        return

    file_controller.delete_all_files_in_folder(file_controller.particles_folder)
    file_controller.ensure_folder_exists(file_controller.particles_folder)

    if particle_data_for_frame.empty:
        return

    feature_size = int(params.get('feature_size', 15))
    min_mass = float(params.get('min_mass', 100.0))

    image_path = file_controller.get_frame_path(frame_number)
    image_to_crop = cv2.imread(image_path)
    if image_to_crop is None:
        return

    # Mass difference
    particle_data_for_frame['mass_diff'] = particle_data_for_frame['mass'] - min_mass
    top_5_mass_particles = particle_data_for_frame.nsmallest(5, 'mass_diff')

    for i, particle in top_5_mass_particles.iterrows():
        x, y, size = particle['x'], particle['y'], particle['size']
        padding = 5
        half_size = (int(size) + padding) * 3
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

        base_filename = f"mass_particle_{i}"
        particle_filename = os.path.join(file_controller.particles_folder, f"{base_filename}.png")
        cv2.imwrite(particle_filename, particle_image)

        mass_info_filename = os.path.join(file_controller.particles_folder, f"{base_filename}.txt")
        with open(mass_info_filename, 'w') as f:
            f.write(f"mass: {particle['mass']:.2f}\n")
            f.write(f"min_mass: {min_mass}\n")

    # Feature size difference
    particle_data_for_frame['size_diff'] = abs(particle_data_for_frame['size'] - feature_size)
    top_5_size_particles = particle_data_for_frame.nlargest(5, 'size_diff')

    for i, particle in top_5_size_particles.iterrows():
        x, y, size = particle['x'], particle['y'], particle['size']
        padding = 5
        half_size = (int(size) + padding) * 3
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

        base_filename = f"size_particle_{i}"
        particle_filename = os.path.join(file_controller.particles_folder, f"{base_filename}.png")
        cv2.imwrite(particle_filename, particle_image)

        size_info_filename = os.path.join(file_controller.particles_folder, f"{base_filename}.txt")
        with open(size_info_filename, 'w') as f:
            f.write(f"feature_size: {particle['size']:.2f}\n")
            f.write(f"parameter_feature_size: {feature_size}\n")

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
    if output_folder is None:
        output_folder = file_controller.rb_gallery_folder
    
    # Use FileController for folder management
    file_controller.ensure_folder_exists(output_folder)
    file_controller.delete_all_files_in_folder(output_folder)
    
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


def annotate_frame(frame_number, particle_data_df, feature_size):
    """
    Annotates a single frame using pre-existing particle data and saves it.

    Parameters
    ----------
    frame_number : int
        The frame number to process.
    particle_data_df : pandas.DataFrame
        DataFrame containing all particle data.
    feature_size : int
        The diameter of the features to draw.

    Returns
    -------
    str or None
        The path to the annotated frame, or None if no particles are found for the frame.
    """
    if file_controller is None:
        print("File controller not set in particle_processing.")
        return None

    # Construct paths
    original_frame_path = os.path.join(file_controller.original_frames_folder, f"frame_{frame_number:05d}.jpg")
    annotated_frame_path = os.path.join(file_controller.annotated_frames_folder, f"frame_{frame_number:05d}.jpg")

    # Ensure annotated frames folder exists
    file_controller.ensure_folder_exists(file_controller.annotated_frames_folder)

    # Filter particles for the current frame
    frame_particles = particle_data_df[particle_data_df['frame'] == frame_number]

    # If particles are found for this frame, create and save the annotated image
    if not frame_particles.empty:
        image = cv2.imread(original_frame_path)
        if image is None:
            print(f"Could not read frame: {original_frame_path}")
            return None

        annotated_image = image.copy()
        for _, particle in frame_particles.iterrows():
            cv2.circle(annotated_image, (int(particle.x), int(particle.y)), int(feature_size / 2) + 2, (0, 255, 255), 2)
        
        cv2.imwrite(annotated_frame_path, annotated_image)
        return annotated_frame_path

    # If no particles are found, ensure no old annotated frame exists
    if os.path.exists(annotated_frame_path):
        os.remove(annotated_frame_path)

    return None


if __name__ == '__main__':
    # Example usage
    video_path = "path/to/your/video.avi"
    trajectories = link_particles_to_trajectories(video_path)
    
    if trajectories is not None:
        analysis = analyze_trajectories(trajectories)
        print("Trajectory linking and analysis complete!")
    else:
        print("Trajectory linking failed!")
