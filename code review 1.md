# Code Review 1: Architecture and Design Analysis

## Executive Summary

This document provides a comprehensive analysis of the Particle Tracking GUI codebase architecture, explaining the design principles, file responsibilities, separation of concerns, and how the system adheres to software engineering best practices.

---

## 1. Overall Architecture

The Particle Tracking GUI follows a **layered architecture with dependency injection**, implementing clear separation between:

- **Presentation Layer**: Qt widgets and windows for user interaction
- **Business Logic Layer**: Particle processing, trajectory linking, and data analysis
- **Data Access Layer**: File operations and configuration management
- **Infrastructure Layer**: Project management and threading services

The architecture uses **dependency injection** throughout, ensuring loose coupling and testability. Components communicate via **Qt signals and slots**, maintaining a clean event-driven design.

---

## 2. Core Design Principles

### 2.1 Single Responsibility Principle (SRP)
Each module has one clear purpose:
- `ConfigManager`: Configuration management only
- `FileController`: File operations only
- `ProjectManager`: Project lifecycle only
- Widgets: UI presentation only
- `particle_processing`: Algorithm implementation only

### 2.2 Dependency Injection
All major components accept dependencies through constructors or setter methods:
- `FileController` receives `ConfigManager`
- Widgets receive `ConfigManager` and `FileController` via setters
- `particle_processing` receives `FileController` via module-level setter

### 2.3 Separation of Concerns
- **Configuration**: Isolated in `ConfigManager` and `config_parser.py`
- **File Operations**: Centralized in `FileController`
- **UI Logic**: Contained in widget classes
- **Business Logic**: Separated in `particle_processing.py` and `services.py`

### 2.4 Open/Closed Principle
- Widgets are extensible through inheritance (e.g., `GraphingPanelWidget` base class)
- New processing algorithms can be added without modifying existing code
- Configuration system allows extension without code changes

### 2.5 Interface Segregation
- Widgets expose only necessary methods via setters (`set_config_manager`, `set_file_controller`)
- Thread classes expose minimal, focused signals
- No fat interfaces or unnecessary dependencies

---

## 3. File-by-File Responsibilities

### 3.1 Core Application Files

#### `src/main.py`
**Responsibility**: Application entry point and main controller
- Manages application lifecycle
- Coordinates window switching (start screen ↔ detection ↔ linking)
- Initializes and injects dependencies (`ConfigManager`, `FileController`, `ProjectManager`)
- Handles cleanup on application exit
- **No overlap**: Only file that manages application-level state and window transitions

#### `src/config_manager.py`
**Responsibility**: Centralized configuration management with dependency injection support
- Loads and saves configuration files (template or project-specific)
- Provides typed access to configuration values
- Handles both global template config and project-specific configs
- Converts relative paths to absolute paths
- **No overlap**: Only file that directly manages `configparser.ConfigParser` instances and provides configuration abstraction

#### `src/config_parser.py`
**Responsibility**: Legacy configuration parsing functions (backward compatibility)
- Provides functional interface for reading/writing config values
- Used by some legacy code paths
- **No overlap**: Provides functional API while `ConfigManager` provides OOP API; both serve different access patterns

#### `src/file_controller.py`
**Responsibility**: Centralized file and folder management
- Manages all file system operations (create, delete, read, write)
- Handles folder structure (particles, frames, data, etc.)
- Provides path resolution and file existence checks
- Manages cleanup operations for temporary folders
- **No overlap**: Only file that performs file I/O operations; all other modules delegate file operations here

#### `src/project_manager.py`
**Responsibility**: Project lifecycle management
- Creates new projects with folder structure
- Loads existing projects
- Manages project-specific configuration initialization
- **No overlap**: Only file that handles project creation and loading; `FileController` handles file operations, `ConfigManager` handles config

#### `src/particle_processing.py`
**Responsibility**: Core particle detection and tracking algorithms
- Wraps TrackPy functions (`tp.locate`, `tp.link_df`, etc.)
- Implements particle detection workflows
- Generates errant particle crops
- Creates red-blue trajectory overlays
- Performs trajectory analysis (MSD calculations)
- **No overlap**: Only file that contains TrackPy algorithm implementations; widgets call these functions but don't implement algorithms

#### `src/services.py`
**Responsibility**: Background threading services for long-running operations
- `FindParticlesThread`: Background particle detection on single frame
- `DetectAllFramesThread`: Background batch particle detection
- `TrajectoryLinkingThread`: Background trajectory linking
- Emits progress signals for UI updates
- **No overlap**: Only file that implements `QThread` subclasses for background processing; widgets use these but don't implement threading

---

### 3.2 Widget Files (UI Layer)

#### `src/widgets/StartScreen.py`
**Responsibility**: Initial project selection screen
- Displays project management UI (create new, open existing)
- Emits signals when projects are selected
- **No overlap**: Only entry point widget; other windows are workflow screens

#### `src/widgets/NewProjectWindow.py`
**Responsibility**: Dialog for creating new projects
- Collects project name and path from user
- Delegates project creation to `ProjectManager`
- **No overlap**: Only widget that handles project creation UI; `StartScreen` shows it but doesn't create projects

#### `src/widgets/ParticleDetectionWindow.py`
**Responsibility**: Main window container for particle detection workflow
- Composes detection widgets (frame player, parameters, gallery, graphing)
- Coordinates data flow between detection widgets
- Handles window-level state (loading particle data, refreshing displays)
- **No overlap**: Only window that contains detection workflow; individual widgets handle their own UI

#### `src/widgets/TrajectoryLinkingWindow.py`
**Responsibility**: Main window container for trajectory linking workflow
- Composes linking widgets (trajectory player, parameters, gallery, plotting)
- Coordinates data flow between linking widgets
- Handles window-level state
- **No overlap**: Only window that contains linking workflow; separate from detection window

#### `src/widgets/DetectionParametersWidget.py`
**Responsibility**: UI for particle detection parameters
- Displays and manages detection parameter inputs (feature size, min mass, threshold, scaling)
- Triggers particle detection workflows
- Manages frame selection (start, end, step)
- Handles particle data persistence (`all_particles.csv`)
- Emits signals for workflow progression
- **No overlap**: Only widget that manages detection parameters; `LinkingParametersWidget` manages different parameters

#### `src/widgets/LinkingParametersWidget.py`
**Responsibility**: UI for trajectory linking parameters
- Displays and manages linking parameter inputs (search range, memory, fps, max speed)
- Triggers trajectory linking workflows
- Emits signals for workflow progression
- **No overlap**: Only widget that manages linking parameters; separate from detection parameters

#### `src/widgets/FramePlayerWidget.py`
**Responsibility**: Video frame display and navigation for particle detection
- Displays individual frames with particle annotations
- Provides frame navigation controls (slider, prev/next buttons)
- Loads and displays frames from disk
- **No overlap**: Only widget that displays detection frames; `TrajectoryPlayerWidget` displays different content (RB overlays)

#### `src/widgets/TrajectoryPlayerWidget.py`
**Responsibility**: Red-blue overlay display for trajectory validation
- Displays red-blue frame pairs showing trajectory links
- Provides navigation through trajectory overlays
- **No overlap**: Only widget that displays trajectory overlays; `FramePlayerWidget` displays detection frames

#### `src/widgets/ErrantParticleGalleryWidget.py`
**Responsibility**: Gallery of potentially problematic particle detections
- Displays cropped images of errant particles
- Allows navigation through errant particles
- Highlights particles with unusual mass/size properties
- **No overlap**: Only widget that displays errant particle crops; `ErrantTrajectoryGalleryWidget` displays different content

#### `src/widgets/ErrantTrajectoryGalleryWidget.py`
**Responsibility**: Gallery of potentially problematic trajectory links
- Displays red-blue overlays for suspicious trajectory links
- Allows navigation through errant trajectories
- Highlights worst trajectory links for review
- **No overlap**: Only widget that displays errant trajectory links; separate from particle gallery

#### `src/widgets/GraphingPanelWidget.py`
**Responsibility**: Base class for plotting panels
- Provides common plotting infrastructure
- Handles matplotlib figure management
- **No overlap**: Base class only; specific plotting widgets inherit from it

#### `src/widgets/DetectionPlottingWidget.py`
**Responsibility**: Plots for particle detection diagnostics
- Displays subpixel bias plots
- Shows particle property distributions
- **No overlap**: Only widget that plots detection diagnostics; `TrajectoryPlottingWidget` plots different data

#### `src/widgets/TrajectoryPlottingWidget.py`
**Responsibility**: Plots for trajectory analysis
- Displays trajectory visualizations
- Shows trajectory statistics
- **No overlap**: Only widget that plots trajectory data; separate from detection plots

#### `src/widgets/GraphingUtils.py`
**Responsibility**: Utility functions for plotting
- Provides helper functions for common plotting tasks
- **No overlap**: Utility functions only; no state or UI

#### `src/widgets/export_helper.py`
**Responsibility**: Data export functionality
- Handles CSV and pickle export dialogs
- Manages file save operations for user data
- **No overlap**: Only file that handles export UI; `FileController` handles file operations but not export dialogs

---

## 4. Separation of Concerns Analysis

### 4.1 Configuration Management
**Separation**: 
- `ConfigManager`: OOP interface, manages configparser instances
- `config_parser.py`: Functional interface for legacy code
- **No overlap**: Different access patterns, both read same files but provide different APIs

### 4.2 File Operations
**Separation**:
- `FileController`: All file I/O operations
- Widgets: Only call `FileController` methods, never perform direct file operations
- `particle_processing.py`: Uses `FileController` for all file operations
- **No overlap**: Single source of truth for file operations

### 4.3 UI and Business Logic
**Separation**:
- Widgets: Only handle UI presentation and user interaction
- `particle_processing.py`: Contains all algorithm implementations
- `services.py`: Contains threading logic
- **No overlap**: Widgets call functions but don't implement algorithms

### 4.4 Data Flow
**Separation**:
- Detection: `DetectionParametersWidget` → `services.py` → `particle_processing.py` → `FileController` → `all_particles.csv`
- Linking: `LinkingParametersWidget` → `services.py` → `particle_processing.py` → `FileController` → `trajectories.csv`
- **No overlap**: Clear unidirectional data flow, no circular dependencies

### 4.5 State Management
**Separation**:
- Window-level state: Managed in `ParticleDetectionWindow` and `TrajectoryLinkingWindow`
- Widget state: Managed within individual widgets
- Persistent state: Stored in config files and CSV files
- **No overlap**: Each level manages its own state scope

---

## 5. Design Pattern Compliance

### 5.1 Dependency Injection ✓
**Evidence**:
- `FileController.__init__(config_manager: ConfigManager, project_path: str)`
- Widgets receive dependencies via setters: `set_config_manager()`, `set_file_controller()`
- `particle_processing.set_file_controller()` for module-level injection
- **Result**: Components are testable and loosely coupled

### 5.2 Observer Pattern ✓
**Evidence**:
- Qt signals and slots throughout (e.g., `particlesUpdated.emit()`, `openTrajectoryLinking.connect()`)
- Thread progress signals (`processing_frame.emit()`)
- **Result**: Decoupled communication between components

### 5.3 Template Method Pattern ✓
**Evidence**:
- `GraphingPanelWidget` base class with common plotting infrastructure
- `DetectionPlottingWidget` and `TrajectoryPlottingWidget` inherit and specialize
- **Result**: Code reuse and consistent plotting interface

### 5.4 Facade Pattern ✓
**Evidence**:
- `FileController` provides simple interface to complex file operations
- `ConfigManager` provides simple interface to configuration complexity
- **Result**: Simplified API for widgets

### 5.5 Strategy Pattern ✓
**Evidence**:
- Different detection parameters can be swapped without code changes
- Different linking algorithms can be used via parameter changes
- **Result**: Flexible algorithm configuration

---

## 6. No Overlap Verification

### 6.1 Configuration Access
- **`ConfigManager`**: OOP interface, used by new code
- **`config_parser.py`**: Functional interface, used by legacy code
- **No overlap**: Different APIs for same data, clear migration path

### 6.2 File Operations
- **`FileController`**: All file operations
- **Widgets**: Never perform direct file I/O
- **`particle_processing.py`**: Uses `FileController` for all file operations
- **No overlap**: Single source of truth

### 6.3 Particle Detection
- **`DetectionParametersWidget`**: UI and parameter management
- **`services.py` (FindParticlesThread)**: Threading wrapper
- **`particle_processing.py`**: Algorithm implementation
- **No overlap**: Clear separation of UI, threading, and algorithms

### 6.4 Trajectory Linking
- **`LinkingParametersWidget`**: UI and parameter management
- **`services.py` (TrajectoryLinkingThread)**: Threading wrapper
- **`particle_processing.py`**: Algorithm implementation
- **No overlap**: Clear separation of UI, threading, and algorithms

### 6.5 Data Visualization
- **`DetectionPlottingWidget`**: Detection-specific plots
- **`TrajectoryPlottingWidget`**: Trajectory-specific plots
- **`GraphingPanelWidget`**: Base class infrastructure
- **No overlap**: Each widget handles different data types

### 6.6 Frame Display
- **`FramePlayerWidget`**: Detection frames with annotations
- **`TrajectoryPlayerWidget`**: Red-blue trajectory overlays
- **No overlap**: Different content, different purposes

### 6.7 Gallery Display
- **`ErrantParticleGalleryWidget`**: Errant particle crops
- **`ErrantTrajectoryGalleryWidget`**: Errant trajectory links
- **No overlap**: Different content types, different validation purposes

---

## 7. Design Principles Compliance

### 7.1 Single Responsibility Principle ✓
**Every file has one clear purpose:**
- Configuration files: Configuration only
- File operation files: File operations only
- Widget files: UI presentation only
- Processing files: Algorithms only
- Service files: Threading only

### 7.2 Open/Closed Principle ✓
**Extensible without modification:**
- New widgets can inherit from base classes
- New algorithms can be added to `particle_processing.py`
- Configuration can be extended without code changes
- New plot types can be added by inheriting `GraphingPanelWidget`

### 7.3 Liskov Substitution Principle ✓
**Subtypes are substitutable:**
- `DetectionPlottingWidget` and `TrajectoryPlottingWidget` can be used wherever `GraphingPanelWidget` is expected
- All widgets follow Qt widget interface contracts

### 7.4 Interface Segregation Principle ✓
**Focused interfaces:**
- Widgets expose only necessary setters (`set_config_manager`, `set_file_controller`)
- Thread classes expose minimal, focused signals
- No components are forced to depend on interfaces they don't use

### 7.5 Dependency Inversion Principle ✓
**Depend on abstractions:**
- Widgets depend on `ConfigManager` interface, not implementation
- Widgets depend on `FileController` interface, not file system directly
- `particle_processing` depends on `FileController` interface, not file paths

---

## 8. Data Flow Architecture

### 8.1 Detection Workflow
```
User Input (DetectionParametersWidget)
    ↓
Save Parameters (config.ini)
    ↓
Trigger Detection (services.FindParticlesThread / DetectAllFramesThread)
    ↓
Algorithm Execution (particle_processing.find_and_save_errant_particles)
    ↓
File Operations (FileController.save_particles_data)
    ↓
Data Persistence (all_particles.csv)
    ↓
UI Update (particlesUpdated signal → widgets refresh)
```

### 8.2 Linking Workflow
```
User Input (LinkingParametersWidget)
    ↓
Save Parameters (config.ini)
    ↓
Load Particles (FileController.load_particles_data)
    ↓
Trigger Linking (services.TrajectoryLinkingThread)
    ↓
Algorithm Execution (particle_processing.link_particles_to_trajectories)
    ↓
File Operations (FileController.save_trajectories_data)
    ↓
Data Persistence (trajectories.csv)
    ↓
UI Update (trajectoriesLinked signal → widgets refresh)
```

### 8.3 Configuration Flow
```
Application Start
    ↓
ConfigManager loads template_config.ini
    ↓
Project Selected
    ↓
ConfigManager loads project/config.ini
    ↓
FileController initialized with ConfigManager
    ↓
Widgets receive ConfigManager and FileController via setters
    ↓
User changes parameters
    ↓
Widgets save via ConfigManager
    ↓
ConfigManager persists to config.ini
```

---

## 9. Threading Architecture

### 9.1 Background Processing
- **`FindParticlesThread`**: Single frame detection (non-blocking)
- **`DetectAllFramesThread`**: Batch frame detection (non-blocking)
- **`TrajectoryLinkingThread`**: Trajectory linking (non-blocking)

### 9.2 Signal-Based Communication
- Threads emit progress signals: `processing_frame.emit()`
- Threads emit completion signals: `finished.emit()`
- Threads emit error signals: `error.emit()`
- Widgets connect to signals for UI updates

### 9.3 Separation
- **Widgets**: Handle UI, emit signals to trigger threads
- **Threads**: Handle background processing, emit progress signals
- **Processing**: Pure algorithm functions, no threading concerns
- **No overlap**: Clear separation between UI thread and worker threads

---

## 10. Error Handling and Resilience

### 10.1 Configuration Errors
- `ConfigManager` provides fallback values
- `config_parser.py` uses try/except for parsing errors
- **No overlap**: Both handle errors in their respective domains

### 10.2 File Operation Errors
- `FileController` methods check file existence
- Error messages logged, operations fail gracefully
- **No overlap**: Single point of error handling for file operations

### 10.3 Threading Errors
- Thread classes emit error signals
- Widgets display error messages to users
- **No overlap**: Threads handle processing errors, widgets handle UI errors

---

## 11. Testability

### 11.1 Dependency Injection Enables Testing
- Components can receive mock `ConfigManager` and `FileController`
- Widgets can be tested in isolation
- Processing functions can be tested without file system

### 11.2 Separation Enables Unit Testing
- Algorithms in `particle_processing.py` can be tested independently
- File operations can be tested with mock file systems
- UI can be tested with mock data

---

## 12. Maintainability

### 12.1 Clear Module Boundaries
- Each file has a single, well-defined responsibility
- Dependencies flow in one direction (UI → Services → Processing → FileController)
- No circular dependencies

### 12.2 Consistent Patterns
- All widgets follow same dependency injection pattern
- All threads follow same signal emission pattern
- All file operations go through `FileController`

### 12.3 Extensibility
- New detection algorithms: Add to `particle_processing.py`
- New widgets: Inherit from base classes or create new widgets
- New parameters: Add to config files and parameter widgets
- New file types: Add methods to `FileController`

---

## 13. Conclusion

The Particle Tracking GUI codebase demonstrates **excellent adherence to software engineering principles**:

✓ **Single Responsibility**: Each file has one clear purpose
✓ **No Overlap**: Clear boundaries between components
✓ **Dependency Injection**: Loose coupling throughout
✓ **Separation of Concerns**: UI, business logic, and data access are separated
✓ **Design Patterns**: Appropriate use of Observer, Facade, Template Method, and Strategy patterns
✓ **Testability**: Components can be tested in isolation
✓ **Maintainability**: Clear structure and consistent patterns
✓ **Extensibility**: Easy to add new features without modifying existing code

The architecture successfully separates:
- **Configuration** (ConfigManager, config_parser)
- **File Operations** (FileController)
- **Project Management** (ProjectManager)
- **UI Presentation** (Widgets)
- **Business Logic** (particle_processing)
- **Threading** (services)

Each component has a well-defined responsibility with no functional overlap, making the codebase maintainable, testable, and extensible.

