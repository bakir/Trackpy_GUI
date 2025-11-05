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


def create_full_frame_rb_overlay(frame1, frame2, threshold_percent=50):
    """
    Create a full-frame red-blue overlay image from two frames.
    
    Parameters
    ----------
    frame1 : numpy array
        First frame (BGR) - particles will be red
    frame2 : numpy array
        Second frame (BGR) - particles will be blue
    threshold_percent : float
        Threshold percentage (0-100). For dark background, this is the percentage of 
        brightest pixels that become the dark color (red/blue)
    
    Returns
    -------
    numpy array
        RB overlay image (RGB format, white background, red particles from frame1, blue particles from frame2, both at 50% opacity)
    """
    # Ensure frames are same size
    if frame1.shape[:2] != frame2.shape[:2]:
        # Resize frame2 to match frame1
        frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
    
    height, width = frame1.shape[:2]
    
    # Get invert setting from detection parameters
    from .config_parser import get_detection_params
    detection_params = get_detection_params()
    invert = detection_params.get('invert', False)
    
    # Convert to grayscale for thresholding
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Apply percentile-based thresholding
    # Calculate threshold value based on percentile
    percentile = 100 - threshold_percent  # Inverse: 10% means 90th percentile
    
    # Get threshold values
    threshold_val1 = np.percentile(gray1.flatten(), percentile)
    threshold_val2 = np.percentile(gray2.flatten(), percentile)
    
    # Apply thresholding
    if invert:
        # Particles are bright on dark background
        _, thresh1 = cv2.threshold(gray1, threshold_val1, 255, cv2.THRESH_BINARY_INV)
        _, thresh2 = cv2.threshold(gray2, threshold_val2, 255, cv2.THRESH_BINARY_INV)
    else:
        # Particles are dark on bright background
        _, thresh1 = cv2.threshold(gray1, threshold_val1, 255, cv2.THRESH_BINARY_INV)
        _, thresh2 = cv2.threshold(gray2, threshold_val2, 255, cv2.THRESH_BINARY_INV)
    
    # Ensure background is white (255) and particles are dark (0)
    white_pixels1 = np.sum(thresh1 == 255)
    white_pixels2 = np.sum(thresh2 == 255)
    
    if white_pixels1 < (thresh1.size * 0.5):
        thresh1 = cv2.bitwise_not(thresh1)
    if white_pixels2 < (thresh2.size * 0.5):
        thresh2 = cv2.bitwise_not(thresh2)
    
    # Create white background RGB image
    rb_overlay = np.ones((height, width, 3), dtype=np.uint8) * 255  # White background
    
    # Create colored versions for overlay
    # Frame 1: Red particles
    # Frame 2: Blue particles
    
    # Create red image for frame 1: dark pixels (particles) become red
    # In BGR format: red = [0, 0, 255] (B=0, G=0, R=255)
    red_overlay = rb_overlay.copy()
    particle_mask1 = thresh1 == 0  # Dark pixels are particles
    red_overlay[particle_mask1, 0] = 0    # B channel
    red_overlay[particle_mask1, 1] = 0    # G channel
    red_overlay[particle_mask1, 2] = 255  # R channel (red)
    
    # Create blue image for frame 2: dark pixels (particles) become blue
    # In BGR format: blue = [255, 0, 0] (B=255, G=0, R=0)
    blue_overlay = rb_overlay.copy()
    particle_mask2 = thresh2 == 0  # Dark pixels are particles
    blue_overlay[particle_mask2, 0] = 255  # B channel (blue)
    blue_overlay[particle_mask2, 1] = 0    # G channel
    blue_overlay[particle_mask2, 2] = 0    # R channel
    
    # Overlay at 50% opacity: blend red and blue
    # Formula: result = alpha * image1 + (1 - alpha) * image2
    alpha = 0.5
    rb_overlay = (alpha * red_overlay + (1 - alpha) * blue_overlay).astype(np.uint8)
    
    # Convert BGR to RGB for return
    rb_overlay_rgb = cv2.cvtColor(rb_overlay, cv2.COLOR_BGR2RGB)
    
    return rb_overlay_rgb


def create_rb_overlay_image(crop1, crop2, x1, y1, x2, y2, threshold_percent=50, crop_size=200):
    """
    Create a red-blue overlay image from two cropped frames.
    
    Parameters
    ----------
    crop1 : numpy array
        First cropped frame (BGR)
    crop2 : numpy array
        Second cropped frame (BGR)
    x1, y1 : float
        Particle position in crop1 (relative to crop origin)
    x2, y2 : float
        Particle position in crop2 (relative to crop origin)
    threshold_percent : float
        Threshold percentage (0-100). For dark background, this is the percentage of 
        brightest pixels that become the dark color (red/blue)
    crop_size : int
        Size of the crop (will be used to resize if crops are different sizes)
    
    Returns
    -------
    numpy array
        RB overlay image (RGB format, white background, blue/red particles at 50% opacity)
    """
    # Resize crops to same size if needed
    target_size = (crop_size, crop_size)
    if crop1.shape[:2] != target_size:
        crop1 = cv2.resize(crop1, target_size)
    if crop2.shape[:2] != target_size:
        crop2 = cv2.resize(crop2, target_size)
    
    # Get invert setting from detection parameters
    from .config_parser import get_detection_params
    detection_params = get_detection_params()
    invert = detection_params.get('invert', False)
    
    # Convert to grayscale for thresholding
    gray1 = cv2.cvtColor(crop1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(crop2, cv2.COLOR_BGR2GRAY)
    
    # Apply percentile-based thresholding
    # For dark background: threshold_percent means top X% brightest pixels become dark (particles)
    # For bright background: threshold_percent means top X% brightest pixels become dark (particles)
    
    # Calculate threshold value based on percentile
    # threshold_percent = 10 means top 10% brightest pixels
    percentile = 100 - threshold_percent  # Inverse: 10% means 90th percentile
    
    # Get threshold values
    threshold_val1 = np.percentile(gray1.flatten(), percentile)
    threshold_val2 = np.percentile(gray2.flatten(), percentile)
    
    # Apply thresholding
    if invert:
        # Particles are bright on dark background
        # Top X% brightest pixels become dark (0), rest becomes white (255)
        _, thresh1 = cv2.threshold(gray1, threshold_val1, 255, cv2.THRESH_BINARY_INV)
        _, thresh2 = cv2.threshold(gray2, threshold_val2, 255, cv2.THRESH_BINARY_INV)
    else:
        # Particles are dark on bright background
        # Top X% brightest pixels become dark (0), rest becomes white (255)
        # We want to threshold so that pixels BRIGHTER than threshold become dark
        # This means: values > threshold become dark (0), rest becomes white (255)
        _, thresh1 = cv2.threshold(gray1, threshold_val1, 255, cv2.THRESH_BINARY_INV)
        _, thresh2 = cv2.threshold(gray2, threshold_val2, 255, cv2.THRESH_BINARY_INV)
    
    # Ensure background is white (255) and particles are dark (0)
    # Check if we need to invert based on which is more common (white background should be majority)
    white_pixels1 = np.sum(thresh1 == 255)
    white_pixels2 = np.sum(thresh2 == 255)
    
    # If less than 50% white, assume background is black - invert to get white background
    if white_pixels1 < (thresh1.size * 0.5):
        thresh1 = cv2.bitwise_not(thresh1)
    if white_pixels2 < (thresh2.size * 0.5):
        thresh2 = cv2.bitwise_not(thresh2)
    
    # Create white background RGB image
    rb_overlay = np.ones((crop_size, crop_size, 3), dtype=np.uint8) * 255  # White background
    
    # Create colored versions for overlay
    # Frame 1 (frame_i): Blue particles
    # Frame 2 (frame_i1): Red particles
    
    # Create blue image for frame 1: dark pixels (particles) become blue
    # In BGR format: blue = [255, 0, 0] (B=255, G=0, R=0)
    blue_overlay = rb_overlay.copy()
    particle_mask1 = thresh1 == 0  # Dark pixels are particles
    blue_overlay[particle_mask1, 0] = 255  # B channel (blue)
    blue_overlay[particle_mask1, 1] = 0    # G channel
    blue_overlay[particle_mask1, 2] = 0    # R channel
    
    # Create red image for frame 2: dark pixels (particles) become red
    # In BGR format: red = [0, 0, 255] (B=0, G=0, R=255)
    red_overlay = rb_overlay.copy()
    particle_mask2 = thresh2 == 0  # Dark pixels are particles
    red_overlay[particle_mask2, 0] = 0    # B channel
    red_overlay[particle_mask2, 1] = 0    # G channel
    red_overlay[particle_mask2, 2] = 255  # R channel (red)
    
    # Overlay at 50% opacity: blend blue and red
    # Formula: result = alpha * image1 + (1 - alpha) * image2
    alpha = 0.5
    rb_overlay = (alpha * blue_overlay + (1 - alpha) * red_overlay).astype(np.uint8)
    
    # Convert BGR to RGB for return
    rb_overlay_rgb = cv2.cvtColor(rb_overlay, cv2.COLOR_BGR2RGB)
    
    return rb_overlay_rgb


def create_rb_gallery(trajectories_file, frames_folder=None, output_folder=None, 
                     search_range=None, memory=None, min_deviation_multiplier=None, max_displays=None):
    """
    Creates red-blue overlay images for the worst individual trajectory links.
    
    Parameters
    ----------
    trajectories_file : str
        Path to the CSV file containing trajectory data
    frames_folder : str, optional
        Path to the folder containing frame images. If None, uses file_controller.
    output_folder : str, optional
        Path to save the RB gallery images. If None, uses file_controller.rb_gallery_folder.
    search_range : float, optional
        Maximum expected jump distance for calculating deviations
    memory : int, optional
        Maximum expected memory (frames a particle can disappear)
    min_deviation_multiplier : float, optional
        DEPRECATED: No longer used. All worst links are shown regardless of threshold.
    max_displays : int, optional
        Maximum number of worst links to display (default 5)
    
    Key changes from previous version:
    - Scores individual frame-to-frame links instead of entire trajectories
    - Identifies the worst link in each trajectory
    - Always shows the top N worst links (no threshold filtering)
    - Displays the specific frame pair where the bad link occurred (not first/last)
    - Saves detailed metadata in .txt files explaining why each link is problematic
    """
    # Check if file_controller is available
    if file_controller is None:
        print("❌ ERROR: file_controller is not set! Cannot create RB gallery.")
        print("   Make sure particle_processing.set_file_controller() was called.")
        return
    
    if output_folder is None:
        output_folder = file_controller.rb_gallery_folder
    
    if frames_folder is None:
        frames_folder = file_controller.original_frames_folder
    
    print(f"📁 RB Gallery output folder: {output_folder}")
    print(f"📁 Frames folder: {frames_folder}")
    
    # Use FileController for folder management
    file_controller.ensure_folder_exists(output_folder)
    file_controller.delete_all_files_in_folder(output_folder)
    print(f"✅ Cleared RB gallery folder: {output_folder}")
    
    # Load trajectory data
    try:
        trajectories = pd.read_csv(trajectories_file)
    except Exception as e:
        print(f"Error loading trajectories: {e}")
        return
    
    if len(trajectories) == 0:
        print("No trajectory data found")
        return
    
    # Get linking parameters if not provided
    from .config_parser import get_linking_params
    linking_params = get_linking_params()
    if search_range is None:
        search_range = float(linking_params.get('search_range', 10))
    if memory is None:
        memory = int(linking_params.get('memory', 10))
    # max_displays defaults to 5 (show top 5 worst links)
    if max_displays is None:
        max_displays = int(linking_params.get('max_displays', 5))
    
    print(f"📊 Creating RB gallery with search_range={search_range}, memory={memory}")
    print(f"📊 Showing top {max_displays} worst links per frame pair")
    print(f"📊 Total trajectories: {trajectories['particle'].nunique()}")
    print(f"📊 Total trajectory points: {len(trajectories)}")
    
    # Collect ALL links from ALL trajectories, not just worst per trajectory
    unique_particles = trajectories['particle'].unique()
    all_links = []  # All links from all trajectories
    print(f"📊 Analyzing {len(unique_particles)} unique particles...")
    
    particles_with_links = 0
    particles_without_links = 0
    
    for particle_id in unique_particles:
        particle_data = trajectories[trajectories['particle'] == particle_id].sort_values('frame')
        
        if len(particle_data) < 2:
            particles_without_links += 1
            continue
        
        num_links = len(particle_data) - 1
        if num_links == 0:
            particles_without_links += 1
            continue
        
        # Collect ALL links from this trajectory
        for i in range(num_links):
            curr = particle_data.iloc[i]
            next_p = particle_data.iloc[i + 1]
            
            # Calculate jump distance
            dx = next_p['x'] - curr['x']
            dy = next_p['y'] - curr['y']
            jump_dist = np.sqrt(dx**2 + dy**2)
            
            # Calculate deviation from expected
            deviation = max(0, jump_dist - search_range)
            
            # Frame gap
            frame_gap = next_p['frame'] - curr['frame']
            
            # Score for this individual link
            # Higher score = worse link (more deviation from expected parameters)
            excess_gap = max(0, (frame_gap - 1) - memory) if frame_gap > 1 else 0
            link_score = (jump_dist - search_range) * 10 + deviation + excess_gap * 5
            
            # Skip if link_score is NaN or invalid
            if np.isnan(link_score) or not np.isfinite(link_score):
                continue
            
            # Add ALL links to the collection
            link_info = {
                'particle_id': particle_id,
                'score': link_score,
                'jump_dist': jump_dist,
                'deviation': deviation,
                'frame_gap': frame_gap,
                'frame_i': int(curr['frame']),
                'frame_i1': int(next_p['frame']),
                'x_i': curr['x'],
                'y_i': curr['y'],
                'x_i1': next_p['x'],
                'y_i1': next_p['y'],
                'data': particle_data
            }
            all_links.append(link_info)
        
        particles_with_links += 1
    
    print(f"📊 Particles with links: {particles_with_links}")
    print(f"📊 Particles skipped (no valid links): {particles_without_links}")
    print(f"📊 Total links collected: {len(all_links)}")
    
    # Group links by frame pair (frame_i, frame_i1)
    from collections import defaultdict
    links_by_frame_pair = defaultdict(list)
    for link in all_links:
        frame_pair = (link['frame_i'], link['frame_i1'])
        links_by_frame_pair[frame_pair].append(link)
    
    print(f"📊 Found {len(links_by_frame_pair)} unique frame pairs")
    
    # For each frame pair, get top N worst links
    top_links = []
    for frame_pair, links in links_by_frame_pair.items():
        # Sort links by score (worst first)
        links.sort(key=lambda x: x['score'], reverse=True)
        # Take top N worst links for this frame pair
        top_links_for_pair = links[:max_displays]
        top_links.extend(top_links_for_pair)
        print(f"  Frame pair {frame_pair[0]}->{frame_pair[1]}: {len(links)} total links, selected top {len(top_links_for_pair)} worst")
    
    # Sort all selected links by score for consistent ordering
    top_links.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"📊 Total links selected across all frame pairs: {len(top_links)}")
    if len(top_links) == 0:
        print("   ⚠️  WARNING: No links found! Check if trajectories have at least 2 frames each.")
    
    crop_size = 200  # Size of the crop around each particle (increased for better context)
    
    # Create RB overlay for each worst link showing the actual problem frames
    print(f"🖼️  Creating RB overlay images for {len(top_links)} links...")
    for idx, link_info in enumerate(top_links):
        particle_id = link_info['particle_id']
        frame_i = link_info['frame_i']
        frame_i1 = link_info['frame_i1']
        
        print(f"  [{idx+1}/{len(top_links)}] Processing particle {particle_id}, frames {frame_i}->{frame_i1}...")
        
        # Load the two frames where the bad link occurred
        # Construct filenames from frame numbers (not array indices)
        frame1_filename = os.path.join(frames_folder, f"frame_{frame_i:05d}.jpg")
        frame2_filename = os.path.join(frames_folder, f"frame_{frame_i1:05d}.jpg")
        
        try:
            frame1 = cv2.imread(frame1_filename)
            frame2 = cv2.imread(frame2_filename)
            
            if frame1 is None or frame2 is None:
                print(f"    ⚠️  Warning: Could not load frames {frame_i} or {frame_i1}")
                print(f"       Frame1 path: {frame1_filename} (exists: {os.path.exists(frame1_filename)})")
                print(f"       Frame2 path: {frame2_filename} (exists: {os.path.exists(frame2_filename)})")
                continue
            
            # Get particle positions at the problematic link
            x1, y1 = int(link_info['x_i']), int(link_info['y_i'])
            x2, y2 = int(link_info['x_i1']), int(link_info['y_i1'])
            
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
            
            # Resize crops to same size
            target_size = (crop_size, crop_size)
            crop1 = cv2.resize(crop1, target_size)
            crop2 = cv2.resize(crop2, target_size)
            
            # Generate RB overlay image (default threshold 50% for initial creation)
            rb_overlay = create_rb_overlay_image(
                crop1, crop2, 
                x1 - x1_min, y1 - y1_min,  # Relative positions in crop
                x2 - x2_min, y2 - y2_min,
                threshold_percent=50  # Default 50% for initial creation
            )
            
            # Save the RB overlay image (convert RGB back to BGR for OpenCV save)
            base_filename = f"particle_{particle_id}_link_{frame_i}_to_{frame_i1}"
            output_filename = os.path.join(output_folder, f"{base_filename}_rb_overlay.png")
            rb_overlay_bgr = cv2.cvtColor(rb_overlay, cv2.COLOR_RGB2BGR)
            success = cv2.imwrite(output_filename, rb_overlay_bgr)
            if success:
                print(f"    ✅ Saved RB overlay: {output_filename}")
            else:
                print(f"    ❌ Failed to save RB overlay: {output_filename}")
            
            # Determine why this link is bad
            issues = []
            if link_info['jump_dist'] > search_range:
                excess = link_info['jump_dist'] - search_range
                issues.append(f"Jump distance ({link_info['jump_dist']:.2f} px) exceeds search_range ({search_range} px) by {excess:.2f} px")
            else:
                issues.append(f"Jump distance ({link_info['jump_dist']:.2f} px) is within search_range ({search_range} px)")
            
            if link_info['frame_gap'] > 1:
                gap_violations = link_info['frame_gap'] - 1  # Frames the particle disappeared
                if gap_violations > memory:
                    excess_gap = gap_violations - memory
                    issues.append(f"Frame gap ({link_info['frame_gap']} frames, {gap_violations} disappearances) exceeds memory ({memory} frames) by {excess_gap} frames")
                else:
                    issues.append(f"Frame gap ({link_info['frame_gap']} frames, {gap_violations} disappearances) is within memory ({memory} frames)")
            else:
                issues.append(f"No frame gap (consecutive frames)")
            
            # Save metadata with detailed information (including positions for regeneration)
            metadata_text = f"""PARTICLE ID: {link_info['particle_id']}
FRAME TRANSITION: {frame_i} → {frame_i+1}

POSITION (Frame {frame_i}): x={link_info['x_i']:.2f}, y={link_info['y_i']:.2f}
POSITION (Frame {frame_i1}): x={link_info['x_i1']:.2f}, y={link_info['y_i1']:.2f}

PARAMETER VIOLATIONS:
{chr(10).join(issues)}

METRICS:
Jump Distance: {link_info['jump_dist']:.2f} pixels
Search Range: {search_range} pixels
Deviation: {link_info['deviation']:.2f} pixels (jump_distance - search_range)
Frame Gap: {link_info['frame_gap']} frames
Memory: {memory} frames
Link Score: {link_info['score']:.2f} (higher = worse)"""
            
            # Save .txt file
            metadata_filename = os.path.join(output_folder, f"{base_filename}.txt")
            try:
                with open(metadata_filename, 'w') as f:
                    f.write(metadata_text)
                print(f"    ✅ Saved metadata: {metadata_filename}")
            except Exception as e:
                print(f"    ❌ Failed to save metadata: {e}")
            
        except Exception as e:
            import traceback
            print(f"    ❌ Error processing particle {particle_id} link: {e}")
            traceback.print_exc()
            continue
    
    print(f"✅ RB gallery created in: {output_folder}")
    print(f"✅ Processed {len(top_links)} worst trajectory links")
    if len(top_links) == 0:
        print(f"⚠️  No trajectory links found (need at least 2 frames per particle)")
    else:
        print(f"✅ Created {len(top_links)} RB overlay images with metadata files")
        print(f"   Showing the {len(top_links)} worst links ranked by deviation score")


def annotate_frame(frame_number, particle_data_df, feature_size, highlighted_particle_index=None):
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
    highlighted_particle_index : int, optional
        The index of a specific particle to highlight.

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

        # Highlight the selected errant particle
        if highlighted_particle_index is not None and highlighted_particle_index in frame_particles.index:
            particle_to_highlight = frame_particles.loc[highlighted_particle_index]
            x, y = int(particle_to_highlight.x), int(particle_to_highlight.y)
            size = int(feature_size / 2) + 5  # Make the square a bit larger
            cv2.rectangle(annotated_image, (x - size, y - size), (x + size, y + size), (255, 0, 0), 3) # Blue square

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
