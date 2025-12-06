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
    return (1 / 3.0) * red + (1 / 3.0) * green + (1 / 3.0) * blue


def locate_particles(
    frame, feature_size=15, min_mass=100, invert=False, threshold=0
):
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
        threshold=threshold,
    )
    return located_features


def link_particles_to_trajectories(
    video_path, output_folder=None, params=None
):
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
        # Try to get params from file_controller's config_manager
        if (
            file_controller
            and hasattr(file_controller, "config_manager")
            and file_controller.config_manager
        ):
            params = file_controller.config_manager.get_detection_params()
        else:
            # Fallback to defaults
            params = {
                "feature_size": 15,
                "min_mass": 100.0,
                "invert": False,
                "threshold": 0.0
            }

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
    feature_size = int(params.get("feature_size", 15))
    min_mass = float(params.get("min_mass", 100.0))
    invert = bool(params.get("invert", False))
    threshold = float(params.get("threshold", 0.0))

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
            processes=1,  # Use single process to avoid multiprocessing issues
        )
    except Exception as e:
        print(f"Error in particle detection: {e}")
        return None

    print(
        f"Found {len(particles)} particle detections across {particles['frame'].nunique()} frames"
    )

    if len(particles) == 0:
        print("No particles detected!")
        return None

    # Step 2: Link particles into trajectories
    print("Linking particles into trajectories...")

    # Calculate search range based on expected particle speed
    # Assuming max speed of ~100 microns/second and typical fps
    # fps = 30  # Default fps, could be extracted from video
    # scaling = 1.0  # microns per pixel, could be from config
    # max_speed_um_per_sec = 100
    # search_range = int(np.ceil(max_speed_um_per_sec / (fps * scaling)))

    search_range = int(params.get("search_range", 10))
    memory = int(params.get("memory", 10))
    min_trajectory_length = int(params.get("min_trajectory_length", 10))
    drift = bool(params.get("drift", False))

    try:
        trajectories = tp.link_df(
            particles, search_range=search_range, memory=memory
        )
    except Exception as e:
        print(f"Error in trajectory linking: {e}")
        return None

    print(f"Created {trajectories['particle'].nunique()} trajectories")

    # Step 3: Filter short trajectories
    # min_trajectory_length = 10
    print(
        f"Filtering trajectories shorter than {min_trajectory_length} frames..."
    )

    trajectories_filtered = tp.filter_stubs(
        trajectories, min_trajectory_length
    )

    print(
        f"After filtering: {trajectories_filtered['particle'].nunique()} trajectories"
    )

    # Step 4: Drift subtraction (optional but recommended)
    print("Computing and subtracting drift...")
    try:
        # Compute drift
        if drift == True:
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
    file_controller.save_trajectories_data(
        trajectories_final, "trajectories.csv"
    )

    return trajectories_final


# def analyze_trajectories(trajectories_df, scaling=1.0, fps=30):
#     """
#     Analyze linked trajectories to compute MSD and other metrics.

#     Parameters
#     ----------
#     trajectories_df : pandas.DataFrame
#         DataFrame with trajectory data from link_particles_to_trajectories
#     scaling : float
#         Microns per pixel
#     fps : float
#         Frames per second

#     Returns
#     -------
#     dict
#         Dictionary containing analysis results
#     """
#     if trajectories_df is None or len(trajectories_df) == 0:
#         return None

#     results = {}

#     # Compute ensemble mean square displacement (eMSD)
#     try:
#         emsd = tp.emsd(trajectories_df, mpp=scaling, fps=fps, max_lagtime=100)
#         results["emsd"] = emsd
#         print("Computed ensemble MSD")
#     except Exception as e:
#         print(f"Error computing eMSD: {e}")

#     # Compute individual MSD (iMSD)
#     try:
#         imsd = tp.imsd(trajectories_df, mpp=scaling, fps=fps, max_lagtime=100)
#         results["imsd"] = imsd
#         print("Computed individual MSD")
#     except Exception as e:
#         print(f"Error computing iMSD: {e}")

#     # Basic statistics
#     results["num_trajectories"] = trajectories_df["particle"].nunique()
#     results["num_frames"] = trajectories_df["frame"].nunique()
#     results["total_detections"] = len(trajectories_df)

#     # Trajectory lengths
#     traj_lengths = trajectories_df.groupby("particle").size()
#     results["mean_trajectory_length"] = traj_lengths.mean()
#     results["std_trajectory_length"] = traj_lengths.std()

#     print(f"Analysis complete:")
#     print(f"  - {results['num_trajectories']} trajectories")
#     print(f"  - {results['num_frames']} frames")
#     print(
#         f"  - Mean trajectory length: {results['mean_trajectory_length']:.1f} frames"
#     )

#     return results


# =============================================================================
# PARTICLE PROCESSING FUNCTIONS
# =============================================================================


def find_particles_in_frames(image_paths, params=None, progress_callback=None):
    """
    Finds particles in a series of images and returns the data.

    Parameters
    ----------
    image_paths : list of str
        The paths to the image files.
    params : dict, optional
        Detection parameters.
    progress_callback : Signal, optional
        A signal to emit progress updates.
    
    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the found particles.
    """
    if params is None:
        params = get_detection_params()
    feature_size = int(params.get("feature_size", 15))
    min_mass = float(params.get("min_mass", 100.0))
    invert = bool(params.get("invert", False))
    threshold = float(params.get("threshold", 0.0))

    if feature_size % 2 == 0:
        feature_size += 1

    all_features = []

    for image_path in image_paths:
        basename = os.path.basename(image_path)
        name_part = os.path.splitext(basename)[0]
        frame_number_str = name_part.split("_")[-1]
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
            threshold=threshold,
        )
        features["frame"] = frame_number
        all_features.append(features)

    if not all_features:
        if progress_callback:
            progress_callback.emit("No particles found.")
        return pd.DataFrame()

    combined_features = pd.concat(all_features, ignore_index=True)

    if progress_callback:
        progress_callback.emit("Done.")

    return combined_features


def save_errant_particle_crops_for_frame(params):
    """
    Saves cropped images of the 10 most errant particles across ALL frames.
    Finds 5 most errant based on mass and 5 most errant based on feature size.
    Stores frame information in filenames and metadata.
    """
    if file_controller is None:
        return

    # Load all particles from filtered_particles.csv
    all_particles = file_controller.load_particles_data("filtered_particles.csv")
    if all_particles.empty:
        return

    # feature_size = int(params.get("feature_size", 15))
    min_size = all_particles['size'].min()
    min_mass = float(params.get("min_mass", 100.0))

    # Calculate errant scores for all particles
    all_particles["mass_diff"] = all_particles["mass"] - min_mass
    all_particles["size_diff"] = abs(all_particles["size"] - min_size)

    # Get top 5 most errant by mass (lowest mass, most negative mass_diff)
    top_5_mass_particles = all_particles.nsmallest(5, "mass_diff")

    # Get top 5 most errant by size (smallest size_diff)
    top_5_size_particles = all_particles.nsmallest(5, "size_diff")

    if top_5_mass_particles.empty and top_5_size_particles.empty:
        return

    file_controller.delete_all_files_in_folder(
        file_controller.particles_folder
    )
    file_controller.ensure_folder_exists(file_controller.particles_folder)

    # Combine and process all 10 particles
    particle_counter = 0

    # Process mass-based errant particles
    for idx, particle in top_5_mass_particles.iterrows():
        frame_num = int(particle["frame"])
        x, y, size = particle["x"], particle["y"], particle["size"]

        image_path = file_controller.get_frame_path(frame_num)
        image_to_crop = cv2.imread(image_path)
        if image_to_crop is None:
            continue

        # Calculate crop boundaries - 4x more zoomed in (25 pixels on each side, then resize to 200x200)
        final_display_size = 200
        crop_radius = 25  # 4x more zoomed: 100/4 = 25 pixels on each side
        x_min = max(0, int(x) - crop_radius)
        y_min = max(0, int(y) - crop_radius)
        x_max = min(image_to_crop.shape[1], int(x) + crop_radius)
        y_max = min(image_to_crop.shape[0], int(y) + crop_radius)

        particle_image = image_to_crop[y_min:y_max, x_min:x_max]

        # Resize to exactly 200x200 for display
        particle_image = cv2.resize(
            particle_image, (final_display_size, final_display_size)
        )

        # Draw crosshair at center
        center_x = final_display_size // 2
        center_y = final_display_size // 2
        cross_size = 5
        cv2.line(
            particle_image,
            (center_x - cross_size, center_y),
            (center_x + cross_size, center_y),
            (255, 255, 255),
            1,
        )
        cv2.line(
            particle_image,
            (center_x, center_y - cross_size),
            (center_x, center_y + cross_size),
            (255, 255, 255),
            1,
        )

        # Save with frame number in filename
        base_filename = (
            f"mass_particle_{particle_counter}_frame_{frame_num:05d}"
        )
        particle_filename = os.path.join(
            file_controller.particles_folder, f"{base_filename}.png"
        )
        cv2.imwrite(particle_filename, particle_image)

        # Save metadata with frame information (frame and position needed for jumping to frame)
        mass_info_filename = os.path.join(
            file_controller.particles_folder, f"{base_filename}.txt"
        )
        with open(mass_info_filename, "w") as f:
            f.write(f"frame: {frame_num}\n")
            f.write(f"x: {particle['x']:.2f}\n")
            f.write(f"y: {particle['y']:.2f}\n")
            f.write(f"mass: {particle['mass']:.2f}\n")
            f.write(f"min_mass: {min_mass}\n")

        particle_counter += 1

    # Process size-based errant particles
    for idx, particle in top_5_size_particles.iterrows():
        frame_num = int(particle["frame"])
        x, y, size = particle["x"], particle["y"], particle["size"]

        image_path = file_controller.get_frame_path(frame_num)
        image_to_crop = cv2.imread(image_path)
        if image_to_crop is None:
            continue

        # Calculate crop boundaries - 4x more zoomed in (25 pixels on each side, then resize to 200x200)
        final_display_size = 200
        crop_radius = 25  # 4x more zoomed: 100/4 = 25 pixels on each side
        x_min = max(0, int(x) - crop_radius)
        y_min = max(0, int(y) - crop_radius)
        x_max = min(image_to_crop.shape[1], int(x) + crop_radius)
        y_max = min(image_to_crop.shape[0], int(y) + crop_radius)

        particle_image = image_to_crop[y_min:y_max, x_min:x_max]

        # Resize to exactly 200x200 for display
        particle_image = cv2.resize(
            particle_image, (final_display_size, final_display_size)
        )

        # Draw crosshair at center
        center_x = final_display_size // 2
        center_y = final_display_size // 2
        cross_size = 5
        cv2.line(
            particle_image,
            (center_x - cross_size, center_y),
            (center_x + cross_size, center_y),
            (255, 255, 255),
            1,
        )
        cv2.line(
            particle_image,
            (center_x, center_y - cross_size),
            (center_x, center_y + cross_size),
            (255, 255, 255),
            1,
        )

        # Save with frame number in filename
        base_filename = (
            f"size_particle_{particle_counter}_frame_{frame_num:05d}"
        )
        particle_filename = os.path.join(
            file_controller.particles_folder, f"{base_filename}.png"
        )
        cv2.imwrite(particle_filename, particle_image)

        # Save metadata with frame information (frame and position needed for jumping to frame)
        size_info_filename = os.path.join(
            file_controller.particles_folder, f"{base_filename}.txt"
        )
        with open(size_info_filename, "w") as f:
            f.write(f"frame: {frame_num}\n")
            f.write(f"x: {particle['x']:.2f}\n")
            f.write(f"y: {particle['y']:.2f}\n")
            f.write(f"size: {particle['size']:.2f}\n")
            f.write(f"min_size: {min_size}\n")

        particle_counter += 1


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
    if (
        file_controller
        and hasattr(file_controller, "config_manager")
        and file_controller.config_manager
    ):
        detection_params = (
            file_controller.config_manager.get_detection_params()
        )
        invert = detection_params.get("invert", False)
    else:
        invert = False

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
        _, thresh1 = cv2.threshold(
            gray1, threshold_val1, 255, cv2.THRESH_BINARY_INV
        )
        _, thresh2 = cv2.threshold(
            gray2, threshold_val2, 255, cv2.THRESH_BINARY_INV
        )
    else:
        # Particles are dark on bright background
        _, thresh1 = cv2.threshold(
            gray1, threshold_val1, 255, cv2.THRESH_BINARY_INV
        )
        _, thresh2 = cv2.threshold(
            gray2, threshold_val2, 255, cv2.THRESH_BINARY_INV
        )

    # Ensure background is white (255) and particles are dark (0)
    white_pixels1 = np.sum(thresh1 == 255)
    white_pixels2 = np.sum(thresh2 == 255)

    if white_pixels1 < (thresh1.size * 0.5):
        thresh1 = cv2.bitwise_not(thresh1)
    if white_pixels2 < (thresh2.size * 0.5):
        thresh2 = cv2.bitwise_not(thresh2)

    # Create white background RGB image
    rb_overlay = (
        np.ones((height, width, 3), dtype=np.uint8) * 255
    )  # White background

    # Create colored versions for overlay
    # Frame 1: Red particles
    # Frame 2: Blue particles

    # Create red image for frame 1: dark pixels (particles) become red
    # In BGR format: red = [0, 0, 255] (B=0, G=0, R=255)
    red_overlay = rb_overlay.copy()
    particle_mask1 = thresh1 == 0  # Dark pixels are particles
    red_overlay[particle_mask1, 0] = 0  # B channel
    red_overlay[particle_mask1, 1] = 0  # G channel
    red_overlay[particle_mask1, 2] = 255  # R channel (red)

    # Create blue image for frame 2: dark pixels (particles) become blue
    # In BGR format: blue = [255, 0, 0] (B=255, G=0, R=0)
    blue_overlay = rb_overlay.copy()
    particle_mask2 = thresh2 == 0  # Dark pixels are particles
    blue_overlay[particle_mask2, 0] = 255  # B channel (blue)
    blue_overlay[particle_mask2, 1] = 0  # G channel
    blue_overlay[particle_mask2, 2] = 0  # R channel

    # Overlay at 50% opacity: blend red and blue
    # Formula: result = alpha * image1 + (1 - alpha) * image2
    alpha = 0.5
    rb_overlay = (alpha * red_overlay + (1 - alpha) * blue_overlay).astype(
        np.uint8
    )

    # Convert BGR to RGB for return
    rb_overlay_rgb = cv2.cvtColor(rb_overlay, cv2.COLOR_BGR2RGB)

    return rb_overlay_rgb


def create_rb_overlay_image(
    crop1, crop2, x1, y1, x2, y2, threshold_percent=50, crop_size=200
):
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
    if (
        file_controller
        and hasattr(file_controller, "config_manager")
        and file_controller.config_manager
    ):
        detection_params = (
            file_controller.config_manager.get_detection_params()
        )
        invert = detection_params.get("invert", False)
    else:
        invert = False

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
        _, thresh1 = cv2.threshold(
            gray1, threshold_val1, 255, cv2.THRESH_BINARY_INV
        )
        _, thresh2 = cv2.threshold(
            gray2, threshold_val2, 255, cv2.THRESH_BINARY_INV
        )
    else:
        # Particles are dark on bright background
        # Top X% brightest pixels become dark (0), rest becomes white (255)
        # We want to threshold so that pixels BRIGHTER than threshold become dark
        # This means: values > threshold become dark (0), rest becomes white (255)
        _, thresh1 = cv2.threshold(
            gray1, threshold_val1, 255, cv2.THRESH_BINARY_INV
        )
        _, thresh2 = cv2.threshold(
            gray2, threshold_val2, 255, cv2.THRESH_BINARY_INV
        )

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
    rb_overlay = (
        np.ones((crop_size, crop_size, 3), dtype=np.uint8) * 255
    )  # White background

    # Create colored versions for overlay
    # Frame 1 (frame_i): Red particles
    # Frame 2 (frame_i1): Blue particles

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
    rb_overlay = (alpha * red_overlay + (1 - alpha) * blue_overlay).astype(
        np.uint8
    )

    # Convert BGR to RGB
    rb_overlay_rgb = cv2.cvtColor(rb_overlay, cv2.COLOR_BGR2RGB)

    # Calculate the midpoint between the two particle positions
    mid_x = int((x1 + x2) / 2)
    mid_y = int((y1 + y2) / 2)

    # Draw a yellow cross at the midpoint
    cv2.drawMarker(
        rb_overlay_rgb,
        (mid_x, mid_y),
        (255, 255, 0),  # Yellow in RGB
        markerType=cv2.MARKER_CROSS,
        markerSize=8,
        thickness=1,
    )

    return rb_overlay_rgb


def create_rb_gallery(
    trajectories_file,
    frames_folder=None,
    output_folder=None,
    search_range=None,
    memory=None,
    min_deviation_multiplier=None,
    max_displays=None,
):
    """
    Finds the worst individual trajectory links and saves their metadata to a JSON file.
    This function no longer creates images directly. The UI is responsible for generation.
    """
    # Check if file_controller is available
    if file_controller is None:
        print("❌ ERROR: file_controller is not set! Cannot process RB gallery.")
        return

    if output_folder is None:
        output_folder = file_controller.rb_gallery_folder

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

    # Get linking parameters
    if (
        file_controller
        and hasattr(file_controller, "config_manager")
        and file_controller.config_manager
    ):
        linking_params = file_controller.config_manager.get_linking_params()
    else:
        linking_params = {
            "search_range": 10, "memory": 10, "max_displays": 5
        }

    if search_range is None:
        search_range = float(linking_params.get("search_range", 10))
    if max_displays is None:
        max_displays = int(linking_params.get("max_displays", 5))

    # For each particle, find its single worst link
    unique_particles = trajectories["particle"].unique()
    worst_links_per_particle = []

    for particle_id in unique_particles:
        particle_data = trajectories[
            trajectories["particle"] == particle_id
        ].sort_values("frame")

        if len(particle_data) < 2:
            continue

        particle_links = []
        for i in range(len(particle_data) - 1):
            curr = particle_data.iloc[i]
            next_p = particle_data.iloc[i + 1]

            # Get frame numbers
            frame_i = int(curr["frame"])
            frame_i1 = int(next_p["frame"])

            # NEW CONDITION: only consider ordinally next frames
            if frame_i1 != (frame_i + 1):
                continue # Skip this link if there's a frame gap

            jump_dist = np.sqrt(
                (next_p["x"] - curr["x"]) ** 2 + (next_p["y"] - curr["y"]) ** 2
            )
            deviation = max(0, jump_dist - search_range)
            link_score = deviation
            
            if np.isnan(link_score) or not np.isfinite(link_score):
                continue

            issues = []
            if jump_dist > search_range:
                excess = jump_dist - search_range
                issues.append(
                    f"Jump distance ({jump_dist:.2f} px) exceeds search_range ({search_range} px) by {excess:.2f} px"
                )
            else:
                issues.append(
                    f"Jump distance ({jump_dist:.2f} px) is within search_range ({search_range} px)"
                )
            
            link_info = {
                "particle_id": int(particle_id),
                "score": link_score,
                "jump_dist": jump_dist,
                "deviation": deviation,
                "frame_i": frame_i,
                "frame_i1": frame_i1,
                "x_i": curr["x"],
                "y_i": curr["y"],
                "x_i1": next_p["x"],
                "y_i1": next_p["y"],
                "issues": issues,
                "search_range": search_range,
            }
            particle_links.append(link_info)

        if particle_links:
            # Find the worst link for this particle and add it to our list
            worst_link = max(particle_links, key=lambda x: x['score'])
            worst_links_per_particle.append(worst_link)

    # Sort the list of worst links from all particles to find the top overall
    worst_links_per_particle.sort(key=lambda x: x["score"], reverse=True)
    top_links = worst_links_per_particle[:max_displays]
    
    if len(top_links) == 0:
        print("⚠️ No problematic trajectory links found to create a gallery.")
        return

    # Save the metadata for the top links to a single JSON file
    metadata_filename = os.path.join(output_folder, "rb_links.json")
    import json
    try:
        with open(metadata_filename, "w") as f:
            json.dump(top_links, f, indent=4)
        print(f"✅ Saved RB gallery metadata for {len(top_links)} links to: {metadata_filename}")
    except Exception as e:
        print(f"    ❌ Failed to save RB gallery metadata: {e}")

    print(f"✅ RB gallery metadata generation complete in: {output_folder}")


def annotate_frame(
    frame_number,
    particle_data_df,
    feature_size,
    highlighted_particle_index=None,
):
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
    original_frame_path = os.path.join(
        file_controller.original_frames_folder, f"frame_{frame_number:05d}.jpg"
    )
    annotated_frame_path = os.path.join(
        file_controller.annotated_frames_folder,
        f"frame_{frame_number:05d}.jpg",
    )

    # Ensure annotated frames folder exists
    file_controller.ensure_folder_exists(
        file_controller.annotated_frames_folder
    )

    # Filter particles for the current frame
    frame_particles = particle_data_df[
        particle_data_df["frame"] == frame_number
    ]

    # If particles are found for this frame, create and save the annotated image
    if not frame_particles.empty:
        image = cv2.imread(original_frame_path)
        if image is None:
            print(f"Could not read frame: {original_frame_path}")
            return None

        annotated_image = image.copy()
        for _, particle in frame_particles.iterrows():
            cv2.circle(
                annotated_image,
                (int(particle.x), int(particle.y)),
                int(feature_size / 2) + 2,
                (0, 255, 255),
                2,
            )

        cv2.imwrite(annotated_frame_path, annotated_image)
        return annotated_frame_path

    # If no particles are found, ensure no old annotated frame exists
    if os.path.exists(annotated_frame_path):
        os.remove(annotated_frame_path)

    return None


def annotate_memory_link_frame(image, start_pos, end_pos, crop_origin):
    """Draws crosses on a memory link frame."""
    
    # Function to draw a cross at a given point
    def draw_cross(img, point, color, size, thickness):
        x, y = int(point[0]), int(point[1])
        half_size = size // 2
        cv2.line(img, (x - half_size, y), (x + half_size, y), color, thickness)
        cv2.line(img, (x, y - half_size), (x, y + half_size), color, thickness)

    # Calculate positions relative to the crop
    start_x_rel = start_pos[0] - crop_origin[0]
    start_y_rel = start_pos[1] - crop_origin[1]
    end_x_rel = end_pos[0] - crop_origin[0]
    end_y_rel = end_pos[1] - crop_origin[1]
    
    # Draw yellow crosses
    cross_color = (0, 255, 255)  # BGR for Yellow
    cross_size = 5
    cross_thickness = 1 # Use 1 for a finer cross

    draw_cross(image, (start_x_rel, start_y_rel), cross_color, cross_size, cross_thickness)
    draw_cross(image, (end_x_rel, end_y_rel), cross_color, cross_size, cross_thickness)
    
    return image


def find_and_save_high_memory_links(trajectories_file, memory_parameter, max_links=5):
    """
    Finds the highest memory links, saves padded and annotated cropped frames,
    and creates a single JSON metadata file for all links.
    """
    if file_controller is None:
        print("File controller not set in particle_processing.")
        return []
    
    try:
        trajectories = pd.read_csv(trajectories_file)
    except Exception as e:
        print(f"Error loading trajectories: {e}")
        return []
    
    if len(trajectories) == 0:
        print("No trajectory data found")
        return []
    
    memory_links_found = []
    unique_particles = trajectories['particle'].unique()
    
    for particle_id in unique_particles:
        particle_data = trajectories[trajectories['particle'] == particle_id].sort_values('frame')
        
        if len(particle_data) < 2:
            continue
        
        frames = particle_data['frame'].values
        for i in range(len(frames) - 1):
            frame_gap = frames[i + 1] - frames[i]
            if frame_gap > 1:
                memory_used = frame_gap - 1
                if memory_used < memory_parameter:
                    last_frame = int(frames[i])
                    reappear_frame = int(frames[i + 1])
                    
                    start_pos_data = particle_data.iloc[i]
                    end_pos_data = particle_data.iloc[i+1]

                    memory_links_found.append({
                        'particle_id': int(particle_id),
                        'memory_used': int(memory_used),
                        'last_frame': int(last_frame),
                        'reappear_frame': int(reappear_frame),
                        'frames': list(range(last_frame, reappear_frame + 1)),
                        'start_pos': (float(start_pos_data['x']), float(start_pos_data['y'])),
                        'end_pos': (float(end_pos_data['x']), float(end_pos_data['y'])),
                    })
    
    memory_links_found.sort(key=lambda x: x['memory_used'], reverse=True)
    top_links = memory_links_found[:max_links]
    
    if len(top_links) == 0:
        print("No high-memory links found")
        return []
    
    memory_folder = file_controller.memory_folder
    file_controller.ensure_folder_exists(memory_folder)
    file_controller.delete_all_files_in_folder(memory_folder)
    
    original_frames_folder = file_controller.original_frames_folder
    
    links_metadata_for_json = []

    for link_idx, link in enumerate(top_links):
        link_folder_name = f"memory_link_{link_idx}"
        link_folder_path = os.path.join(memory_folder, link_folder_name)
        file_controller.ensure_folder_exists(link_folder_path)
        
        start_pos = link['start_pos']
        end_pos = link['end_pos']

        center_x = (start_pos[0] + end_pos[0]) / 2
        center_y = (start_pos[1] + end_pos[1]) / 2
        crop_radius = 75
        target_dim = 150
        
        crop_origin_x = int(center_x - crop_radius)
        crop_origin_y = int(center_y - crop_radius)
        crop_origin = (crop_origin_x, crop_origin_y)

        # Add data to the list for the final JSON file
        link_metadata = link.copy()
        link_metadata['link_folder'] = link_folder_name
        link_metadata['crop_origin'] = crop_origin
        links_metadata_for_json.append(link_metadata)

        # Crop and save annotated images
        for frame_num in link['frames']:
            source_frame_path = os.path.join(original_frames_folder, f"frame_{frame_num:05d}.jpg")
            if os.path.exists(source_frame_path):
                dest_frame_path = os.path.join(link_folder_path, f"frame_{frame_num:05d}.jpg")
                
                full_image = cv2.imread(source_frame_path)
                if full_image is not None:
                    canvas = np.zeros((target_dim, target_dim, 3), dtype=np.uint8)
                    
                    src_x_start = max(0, crop_origin_x)
                    src_y_start = max(0, crop_origin_y)
                    src_x_end = min(full_image.shape[1], crop_origin_x + target_dim)
                    src_y_end = min(full_image.shape[0], crop_origin_y + target_dim)
                    
                    dest_x_start = max(0, -crop_origin_x)
                    dest_y_start = max(0, -crop_origin_y)
                    dest_x_end = dest_x_start + (src_x_end - src_x_start)
                    dest_y_end = dest_y_start + (src_y_end - src_y_start)
                    
                    canvas[dest_y_start:dest_y_end, dest_x_start:dest_x_end] = full_image[src_y_start:src_y_end, src_x_start:src_x_end]
                    
                    annotated_canvas = annotate_memory_link_frame(canvas, start_pos, end_pos, crop_origin)
                    
                    cv2.imwrite(dest_frame_path, annotated_canvas)

    # Save the consolidated metadata to a single JSON file
    json_path = os.path.join(memory_folder, "memory_links.json")
    import json
    try:
        with open(json_path, 'w') as f:
            json.dump(links_metadata_for_json, f, indent=4)
        print(f"✅ Saved memory links metadata to: {json_path}")
    except Exception as e:
        print(f"❌ Failed to save memory links metadata: {e}")

    print(f"Found {len(top_links)} high-memory links and saved frames to {memory_folder}")
    return top_links
