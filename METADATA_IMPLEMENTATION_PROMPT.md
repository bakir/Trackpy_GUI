# Implementation Prompt: Project Metadata and Video/Scaling Input

## Overview
Add metadata collection and video/scaling input to the project creation workflow. The metadata should be collected during project creation, stored in the project's config.ini file, and displayed in the Particle Detection Window.

## Requirements

### 1. Project Creation Dialog (NewProjectWindow)

Add the following input fields to the project creation dialog form, in this order:
- **Project Name** (already exists)
- **Movie Taker**: Text input field for the name of the person who took/recorded the movie
  - Placeholder: "Enter name of person who took the movie (optional)"
  - Optional field
- **Person Doing Analysis**: Text input field for the name of the person performing the particle analysis
  - Placeholder: "Enter name of person doing analysis (optional)"
  - Optional field
- **Movie Taken Date**: Date picker (already exists)
- **Video File**: File input with Browse button
  - Required field
  - File dialog should filter for: "Video Files (*.avi *.mp4 *.mov *.mkv);;All Files (*)"
  - Display the selected file path in a read-only text field
  - Validate that the file exists before allowing project creation
- **Scaling (μm/pixel)**: DoubleSpinBox input
  - Required field
  - Range: 0.000001 to 1000.0
  - Decimals: 6
  - Single step: 0.1
  - Default value: 1.0
  - Tooltip: "Microns per pixel (calibration)."
- **Parent Folder** (already exists)

### 2. Data Storage

#### In NewProjectWindow class:
- Add instance variables: `movie_taker`, `person_doing_analysis`, `video_path`, `scaling`
- Store values from input fields when project is created
- Add getter methods: `get_movie_taker()`, `get_person_doing_analysis()`, `get_video_path()`, `get_scaling()`
- Update validation to require video file and scaling (both must be filled)

#### In ProjectManager.create_new_project():
- Update method signature to accept: `movie_taker`, `person_doing_analysis`, `video_path`, `scaling`
- Copy the video file to the project's `videos/` folder when creating project
  - Extract filename using `os.path.basename(video_path)`
  - Copy to: `{project_folder}/videos/{video_filename}`
  - Use `shutil.copy2()` to preserve file metadata
- Pass video filename (not full path) to config creation

#### In ProjectManager._create_default_project_config():
- Update method signature to accept: `movie_taker`, `person_doing_analysis`, `video_filename`, `scaling`
- Save metadata to `[Metadata]` section:
  ```
  [Metadata]
  movie_taker = {movie_taker}
  person_doing_analysis = {person_doing_analysis}
  movie_taken_date = {movie_taken_date}
  movie_filename = {video_filename}
  ```
- Save scaling to `[Detection]` section:
  ```
  [Detection]
  ...
  scaling = {scaling}
  ```

### 3. ConfigManager Updates

Add method to retrieve metadata:
```python
def get_metadata(self) -> Dict[str, str]:
    """Get metadata as a dictionary."""
    return {
        "movie_taker": self.get("Metadata", "movie_taker", ""),
        "person_doing_analysis": self.get("Metadata", "person_doing_analysis", ""),
        "movie_taken_date": self.get("Metadata", "movie_taken_date", ""),
        "movie_filename": self.get("Metadata", "movie_filename", ""),
    }
```

### 4. StartScreen Updates

Update `create_new_project()` method:
- Get all values from NewProjectWindow dialog:
  - `movie_taker = dialog.get_movie_taker()`
  - `person_doing_analysis = dialog.get_person_doing_analysis()`
  - `video_path = dialog.get_video_path()`
  - `scaling = dialog.get_scaling()`
- Pass all values to `project_manager.create_new_project()`

### 5. Metadata Display Widget

In ParticleDetectionWindow:
- Create a metadata display widget below the DetectionParametersWidget
- Display the following fields (each on its own line):
  - **Movie Taker**: {movie_taker} or "-" if empty
  - **Person Doing Analysis**: {person_doing_analysis} or "-" if empty
  - **Movie Taken Date**: {movie_taken_date} or "-" if empty
  - **Movie Filename**: {movie_filename} or "-" if empty
    - This field should have text wrapping enabled (`setWordWrap(True)`) to handle long filenames
- Use system-native styling (no custom stylesheets)
- Update the display when config_manager is set via `_update_metadata_display()` method
- Call `_update_metadata_display()` in `set_config_manager()`

### 6. Video Auto-Loading

In main.py, when a project is opened:
- After showing particle detection window, check if frames exist
- If no frames exist but video file exists in videos folder:
  - Find the first video file in the videos folder
  - Automatically extract frames using `frame_player.save_video_frames(video_path)`
  - This should happen asynchronously (the method already handles threading)

### 7. File Structure

The metadata should be stored in `config.ini` as:
```ini
[Metadata]
movie_taker = John Doe
person_doing_analysis = Jane Smith
movie_taken_date = 2024-01-15
movie_filename = experiment_video.mp4

[Detection]
feature_size = 15
min_mass = 100.0
invert = false
threshold = 0.0
frame_idx = 0
scaling = 1.5
```

## Implementation Notes

1. **Validation**: The Create Project button should only be enabled when:
   - Project name is filled
   - Parent folder is selected
   - Video file is selected
   - All other fields are optional

2. **Video File Handling**: 
   - When video is selected, validate it exists
   - Copy video to project folder during creation
   - Store only the filename (not full path) in metadata
   - Video should be in `{project}/videos/` folder

3. **Scaling**: 
   - Scaling is a required field with default value 1.0
   - Stored in Detection section of config.ini
   - Used for calibration calculations

4. **Metadata Display**:
   - Should be compact, no border/frame
   - Use system-native fonts and colors
   - Display below parameter settings widget
   - Update automatically when config is loaded

5. **Backward Compatibility**:
   - Handle missing metadata fields gracefully (show "-" if not found)
   - Default values for optional fields should be empty strings

## Testing Checklist

- [ ] Video file is copied to project videos folder
- [ ] Video filename is saved to config.ini metadata
- [ ] Scaling value is saved to config.ini Detection section
- [ ] Movie taker and person doing analysis are saved to config.ini
- [ ] All metadata displays correctly in Particle Detection Window
- [ ] Movie filename wraps if too long
- [ ] Project creation validates video file exists
- [ ] Create button is disabled until all required fields are filled
- [ ] Video auto-extracts frames when project is opened (if no frames exist)

