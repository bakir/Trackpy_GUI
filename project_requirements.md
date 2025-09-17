# Project Requirements

This document outlines the requirements for the TrackPy GUI project. It is a collection of ideas and specifications from different team members.

## Team Member Suggestions

### Bakir

-   Have sliders vs. write-in input options. When you are working on one frame, you can have sliders because they might compute faster. When you are doing more frames, it's too slow to recompute every time you slide.
-   You can pinch to expand sliders and stuff.
-   You can set the range for sliders.
-   There is a pop-up window that will give you the clustering stuff. You can also manually select the ones you want, or have a clustering algorithm done.
-   We should use Qt (PySide6) because that is used in other scientific software. Maybe add some styling to make it look a little bit more not disgusting.
-   There is a small box that tells you how many frames you are looking at. It looks like a library, but you can select and play everything as a video.
-   You can also bring up a pop-up, and that pop-up gives you the chance to...

### Jacqueline

-   Split into sections maybe (easier to find things?).
-   One section that has things to do with the setup of the size of particles, if the video is inverted, microns per pixel, frames per second, and other filtering things.
-   One section that deals with the particle tracking, the amount of frames needed for memory, frames, remove drift.
-   One section that has to do with graphing, mass plot, size vs. mass plot, drift plot, particle tracking plot, and anything else.
-   Some things just need a text box input (microns per pixel, frames per second).
-   Others a check box or some binary graphic (invert, remove drift).
-   Maybe a central image area to look at the current frame, a slider underneath to quickly scroll through frames, and a way to enter a range of frames.
-   Graph stuff on the left, particle size/tracking stuff on the right.
-   Graphs would be pop-ups using buttons maybe.

### Kevin

-   Load video button.
-   Identify first frame and show it to the user, then choose random parameters and allow the user to adjust them, giving live feedback (knobs, bells, sliders, whistles...).
-   Also, allow users to select a different frame than the first (sometimes the first frame doesn’t have all the particles).
-   And then preprocess the whole video behind the scenes, applying these parameters?
-   Have checkboxes that will select a certain group of particles based on some characteristic (size, mass, eccentricity...).
-   Include a button for a pop-up window that allows cluster selection.
-   Some checkbox to turn on particle linking highlighting (two transparent frames overlaid).
-   Another option to highlight all links that are at the very edge of the linking boundaries/constraints/parameters.
-   Checkbox to “Visualize subpixel bias before and after running batch processing.” In notes, but idk what this means.
-   Video streaming option.
-   Processor to remove non-moving trajectories (e.g., from dust on the camera).
-   Add an option to support multiple colors and multiple movies, while the simpler single-color GUI could be submitted to the official TrackPy repository.

## AI Prompt Summary

-   Video centered with a play button and text that says what frame is being displayed.
-   Frame selection control.
-   Several sliders for selecting parameters such as mass, eccentricity, and particle size.
-   Checkbox to invert the video.
-   Checkbox to remove non-moving trajectories.
-   Checkbox to turn on subpixel bias visualization.
-   Graph that plots particles based on some parameters (mass, eccentricity, particle size) that are specified by controls below the graph.
-   Button to highlight particle linking on one frame.
-   Button to upload a new video.
-   Button to turn on streaming mode.
-   Button to turn on multiple colors/movies mode.
-   Button that opens a pop-up that allows cluster selection.

## Proposed Layout

-   **Center:** Video with play button and frame display text.
-   **Right Side Control Panel:**
    -   Frame selection.
    -   Control to select a range of video frames (from 1 to all).
    -   The video will play just these frames with the tracking overlaid on the video.
    -   Several sliders for selecting parameters such as mass, eccentricity, and particle size.
    -   Checkbox to invert the video.
    -   Checkbox to apply some algorithm that removes non-moving trajectories.
    -   Checkbox to turn on subpixel bias visualization.
-   **Left Side Control Panel:**
    -   Graph that plots particles based on some parameters (mass, eccentricity, particle size) that are specified by controls below the graph.
-   **Top Control Panel:**
    -   Button that opens up a pop-up window that highlights particle linking on one frame.
    -   In the pop-up window, have an option to highlight links that are at the extremes of the linking requirement parameters.
    -   Button to upload a new video.
    -   Button to turn on streaming mode.
    -   Button to turn on multiple colors/movies mode.
    -   Button that opens a pop-up that allows cluster selection.
-   **Below Video:**
    -   Spreadsheet with particle data.

## Technology Investigation: TrackPy GUI Project

### Project Purpose and User Overview

Our project aims to create a streamlined graphical user interface for Professor Viva Horowitz's particle tracking research lab, which focuses on modeling and analyzing particle diffusion in artificial cells using TrackPy, a particle tracking software. Currently, for students to use TrackPy, they must engage directly with its code, which creates a significant barrier that slows learning and opposes the objective of the research lab—particle tracking analysis. Our solution addresses this barrier. It will be simple to learn for students new to both the research domain and programming, it will include all crucial steps of the TrackPy workflow, and it will be easily modifiable and extensible to accommodate evolving research needs.

The intended users are emerging researchers in the Horowitz lab who are learning about particle diffusion and tracking methodologies but have less programming experience, and who will find it easier to learn through our GUI with its built-in functionality. They need to quickly modify detection and trajectory parameters while visualizing the effects of their changes in real time, allowing them to build intuition about the research process without coding barriers.

### Development Environment and Project Administration

-   **IDE:** Visual Studio Code
-   **Version Control:** GitHub
-   **AI-Assisted Development:** Gemini CLI

### Backend Environment and Data Management

-   **Environment Management:** Anaconda
-   **Python Version:** 3.10
-   **Data Manipulation:** Pandas

### GUI Framework

-   **Framework:** PySide6
-   **Reasoning:** Extensive widgets, familiar to scientific software users, good for displaying data plots and multiple panels. Licensing (LGPL) is compatible with TrackPy's license.

### Advanced Feature Implementation

-   **Clustering Analysis:** Implement a clustering algorithm (DBSCAN from Scikit-Learn) to show clusters of particles with similar attributes.