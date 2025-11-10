# Dead Code Removal Summary

## Files Deleted

1. **`src/services.py`** - COMPLETELY UNUSED
   - Contained duplicate thread classes (`FindParticlesThread`, `DetectAllFramesThread`, `TrajectoryLinkingThread`)
   - Contained service classes (`ParticleDetectionService`, `TrajectoryLinkingService`) that were never imported
   - All functionality already existed in widget files

## Dead Methods Removed

1. **`src/main.py`**:
   - `cleanup_all_temp_folders()` - Never called (cleanup_on_quit was removed)
   - `get_project_manager()` - Never called
   - `get_file_controller()` - Never called
   - `cleanup_on_quit()` function - Removed since we preserve files on exit

2. **`src/project_manager.py`**:
   - `list_recent_projects()` - Placeholder that just returned empty list
   - `close_project()` - Never called

3. **`src/widgets/ParticleDetectionWindow.py`**:
   - `stream()` - Empty stub method
   - `open_trajectory_linking_window()` - Empty method, signal handled by main controller

4. **`src/widgets/TrajectoryLinkingWindow.py`**:
   - `stream()` - Empty stub method

5. **`src/file_controller.py`**:
   - `save_errant_particle_image()` - Never called, incomplete implementation

## Unused Imports Removed

1. **`src/widgets/DetectionParametersWidget.py`**:
   - Removed `sys.path.append()` - Unnecessary with relative imports
   - Removed duplicate `import cv2` at top (used locally in thread)

2. **`src/widgets/ParticleDetectionWindow.py`**:
   - Removed `sys.path.append()` - Unnecessary
   - Removed unused `QApplication`, `QGridLayout`, `QFormLayout`, `QPushButton`, `QSlider`, `QLabel`, `QFrame`, `QSizePolicy`, `QLineEdit` imports
   - Removed unused `QPixmap` import
   - Removed unused `QUrl` import
   - Removed unused `matplotlib`, `FigureCanvas`, `Figure` imports
   - Removed circular import: `from .TrajectoryLinkingWindow import *`
   - Removed duplicate `import os`
   - Removed unused `from .. import particle_processing` (not used in this file)

3. **`src/widgets/TrajectoryLinkingWindow.py`**:
   - Removed `sys.path.append()` - Unnecessary
   - Removed unused `QApplication`, `QGridLayout`, `QFormLayout`, `QPushButton`, `QSlider`, `QLabel`, `QFrame`, `QSizePolicy`, `QLineEdit` imports
   - Removed unused `QPixmap` import
   - Removed unused `QUrl` import
   - Removed unused `matplotlib`, `FigureCanvas`, `Figure` imports
   - Removed unused `QtWidgets` import
   - Removed circular import: `from .ParticleDetectionWindow import *`
   - Removed unused `from .. import particle_processing` (not used in this file)

4. **`src/widgets/FramePlayerWidget.py`**:
   - Removed `sys.path.append()` - Unnecessary
   - Removed unused `sys` import
   - Removed unused `QApplication`, `QMainWindow` imports
   - Removed unused `QFormLayout` import

5. **`src/widgets/LinkingParametersWidget.py`**:
   - Removed `sys.path.append()` - Unnecessary
   - Removed unused `sys` import

6. **`src/widgets/ErrantTrajectoryGalleryWidget.py`**:
   - Removed `sys.path.append()` - Unnecessary
   - Removed unused `sys` import

7. **`src/widgets/GraphingUtils.py`**:
   - Removed `sys.path.append()` - Unnecessary
   - Removed unused `sys` import
   - Removed duplicate `import os`

8. **`src/widgets/DetectionPlottingWidget.py`**:
   - Removed `sys.path.append()` - Unnecessary
   - Removed unused `sys` import
   - Removed duplicate `import os`

9. **`src/widgets/TrajectoryPlottingWidget.py`**:
   - Removed `sys.path.append()` - Unnecessary
   - Removed unused `sys` import
   - Removed duplicate `import os`

## Dead Code in particle_processing.py

1. **Example/Test Code**:
   - Removed `if __name__ == "__main__"` block with example usage (not needed in library code)

## Configuration Files Removed

1. **`template_config.ini`** - No longer needed, defaults are in code
2. **`config.ini`** - Removed from repo (project-specific configs are created per project)

## Summary

- **1 entire file deleted** (`services.py` - 323 lines)
- **8 dead methods removed**
- **30+ unused imports removed**
- **2 configuration files removed from repo**
- **All `sys.path.append()` calls removed** (8 files)
- **Circular imports removed** (ParticleDetectionWindow ↔ TrajectoryLinkingWindow)

## Result

The codebase is now **tighter and more focused**:
- No duplicate functionality
- No unused imports
- No dead methods
- No circular dependencies
- Clean separation of concerns
- All imports use proper relative imports

