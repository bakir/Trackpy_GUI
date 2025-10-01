import trackpy as tp
import pims
import numpy as np
import pandas as pd
import cv2

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

if __name__ == '__main__':
    pass