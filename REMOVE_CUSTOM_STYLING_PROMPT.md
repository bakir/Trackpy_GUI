# Implementation Prompt: Remove Custom Styling and Use Native PySide6 Styling

## Overview
Remove all custom styling (setStyleSheet calls) from the application and rely on native PySide6 system styling. This will make the application look native on each operating system (macOS on macOS, Windows on Windows, etc.). **CRITICAL: Do not remove any functional code - only remove visual styling.**

## Important Warnings

⚠️ **DO NOT REMOVE:**
- Any functional code that controls behavior
- Signal connections
- Event handlers
- Data processing logic
- Widget creation and layout code
- Any code that affects application functionality

⚠️ **ONLY REMOVE:**
- `setStyleSheet()` method calls
- Custom color definitions
- Custom border/background styling
- Custom font styling (unless it's functional, like making text bold for emphasis)
- Custom button appearance styling

⚠️ **PRESERVE:**
- Font size changes for titles/headers (using QFont, not stylesheets)
- Functional styling like `setWordWrap()`, `setAlignment()`, `setReadOnly()`
- Size constraints like `setMinimumHeight()`, `setFixedSize()` if they're functional
- Frame styles that are functional (like `QFrame.Box` for visual separation - but remove custom colors/borders)

## Files to Modify

### 1. src/main.py
**Current State:** May have style factory settings
**Action Required:**
- Update `main()` function to use system-native styling
- For macOS (Darwin): Don't set a style, let Qt use native macOS styling
- For Windows: Use "Windows" style if available
- For Linux: Use "Fusion" as fallback
- Remove any hardcoded style like "Fusion" for macOS

**Example:**
```python
def main():
    app = QApplication(sys.argv)
    
    # Set the application style based on operating system
    system = platform.system()
    available_styles = QtWidgets.QStyleFactory.keys()
    
    if system == "Darwin":  # macOS
        # Don't set a style - let Qt use native macOS styling
        pass
    elif system == "Windows":
        if "Windows" in available_styles:
            app.setStyle(QtWidgets.QStyleFactory.create("Windows"))
        else:
            app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    else:
        # Linux or other
        app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    
    # ... rest of main function
```

### 2. src/widgets/NewProjectWindow.py
**Action Required:**
- Remove ALL `setStyleSheet()` calls
- Keep all functional code (validation, file dialogs, etc.)
- Keep QFont usage for title/header text (this is functional, not just styling)

**What to Remove:**
- Any `widget.setStyleSheet("...")` calls
- Custom color definitions in stylesheets
- Custom border/background styling

**What to Keep:**
- `title_font.setBold(True)` and `title_font.setPointSize()` - these are functional
- All validation logic
- All button connections
- All form layout code

### 3. src/widgets/StartScreen.py
**Action Required:**
- Remove ALL `setStyleSheet()` calls
- Keep all functional code

**What to Remove:**
- All `setStyleSheet()` calls on labels, buttons, frames

**What to Keep:**
- `setFont()` calls with QFont (functional for text emphasis)
- All button connections
- All layout code

### 4. src/widgets/ParticleDetectionWindow.py
**Action Required:**
- Remove `setStyleSheet()` calls from metadata widget
- Keep all functional code

**What to Remove:**
- `metadata_frame.setStyleSheet()` if it exists
- Any label styling

**What to Keep:**
- `setFont()` for title (functional)
- `setWordWrap(True)` for movie filename (functional)
- All metadata display logic

### 5. src/widgets/FilteringWidget.py
**Action Required:**
- Remove ALL `setStyleSheet()` calls
- Replace font styling with QFont if needed for functional emphasis

**What to Remove:**
- `self.setStyleSheet()` in FilterCard
- `label.setStyleSheet("font-weight: bold;")` - replace with QFont
- `delete_button.setStyleSheet()` - remove all button styling
- `add_button.setStyleSheet()` - remove all button styling
- `scroll_area.setStyleSheet()` - remove border styling
- `status_label.setStyleSheet()` - remove color styling

**What to Keep:**
- All filter logic
- All button connections
- Frame style if it's functional (QFrame.Box for visual separation is okay, but remove custom colors)

**Example Fix:**
```python
# BEFORE:
label.setStyleSheet("font-weight: bold;")

# AFTER:
label_font = QFont()
label_font.setBold(True)
label.setFont(label_font)
```

### 6. src/widgets/FramePlayerWidget.py
**Action Required:**
- Remove `setStyleSheet()` calls
- Keep functional frame display code

**What to Remove:**
- `frame_label.setStyleSheet()` - remove border/background styling
- `import_video_button.setStyleSheet()` - remove button styling

**What to Keep:**
- All frame display logic
- All button functionality
- Size constraints if functional

### 7. src/widgets/ErrantParticleGalleryWidget.py
**Action Required:**
- Remove initial `setStyleSheet()` call on `photo_label` (line ~37) - this is just visual
- **CRITICAL: The border color change in `_on_show_particle_checkbox_changed()` is FUNCTIONAL**
- This method changes the border color (blue vs black) to indicate whether "Show particle on frame" checkbox is checked
- **DO NOT REMOVE THIS FUNCTIONALITY** - it provides important visual feedback to the user

**What to Remove:**
- Initial `photo_label.setStyleSheet("background-color: #222; color: #ccc; border: 2px solid black;")` - this is just initial styling

**What to Keep:**
- The checkbox state change handler (`_on_show_particle_checkbox_changed`)
- The logic that changes border color based on checkbox state
- **IMPORTANT**: The border color change (blue when checked, black when unchecked) is functional - it shows the user whether "show on frame" is active
- **OPTION**: If you want to remove even this functional styling, replace it with an alternative visual indicator:
  - Add a status label (e.g., "Show on frame: ON" / "Show on frame: OFF")
  - Add an icon indicator
  - Use a different visual approach

**Example - Current Functional Code (DO NOT REMOVE without replacement):**
```python
def _on_show_particle_checkbox_changed(self, state):
    """Handle state change of 'Show particle on frame' checkbox."""
    self.update_required.emit()
    
    # This border color change is FUNCTIONAL - indicates checkbox state
    if self.is_show_on_frame_checked():
        self.photo_label.setStyleSheet(
            "background-color: #222; color: #ccc; border: 2px solid blue;"
        )
    else:
        self.photo_label.setStyleSheet(
            "background-color: #222; color: #ccc; border: 2px solid black;"
        )
```

**If Removing Functional Border Color, Use Alternative:**
```python
def _on_show_particle_checkbox_changed(self, state):
    """Handle state change of 'Show particle on frame' checkbox."""
    self.update_required.emit()
    
    # Alternative: Use a status label instead of border color
    if self.is_show_on_frame_checked():
        if not hasattr(self, 'status_indicator'):
            self.status_indicator = QLabel("Show on frame: ON")
            # Add to layout
        self.status_indicator.setText("Show on frame: ON")
        self.status_indicator.setStyleSheet("color: blue;")  # Minimal styling for functional purpose
    else:
        if hasattr(self, 'status_indicator'):
            self.status_indicator.setText("Show on frame: OFF")
            self.status_indicator.setStyleSheet("")  # No special styling
```

**Decision Rule for Functional Styling:**
- If styling provides functional feedback (like indicating state), either:
  1. Keep minimal styling for that specific functional purpose (preferred if it's the clearest way)
  2. Replace with alternative visual indicator (label, icon, etc.)
  3. Use native widget properties if available
- **When in doubt, keep functional styling** - it's better to have some styling than to lose important user feedback

### 8. src/widgets/TrajectoryPlayerWidget.py
**Action Required:**
- Remove `setStyleSheet()` calls
- Keep all functional code

### 9. src/widgets/ErrantTrajectoryGalleryWidget.py
**Action Required:**
- Remove `setStyleSheet()` calls
- Keep all functional code

### 10. src/widgets/GraphingUtils.py
**Action Required:**
- Remove `setStyleSheet()` calls from GraphingButton
- **CRITICAL: Keep the highlighting logic** - just remove the visual styling

**What to Remove:**
- `self.setStyleSheet("background-color: ...")` calls
- `self.highlighted_button.setStyleSheet()` calls

**What to Keep:**
- The `highlight()` method logic
- The tracking of which button is highlighted
- Consider using a different visual indicator (like a border frame or icon) if highlighting is functional

**Example:**
```python
# BEFORE:
def highlight(self):
    if self.highlighted_button != None:
        self.highlighted_button.setStyleSheet("background-color: light grey")
    GraphingButton.highlighted_button = self
    self.setStyleSheet("background-color: #1f77b4")

# AFTER - Remove styling but keep logic:
def highlight(self):
    if self.highlighted_button != None:
        # Remove styling, but keep the logic
        pass
    GraphingButton.highlighted_button = self
    # Remove styling, but keep the tracking
    # Note: If highlighting is important for UX, consider using
    # a different approach like a border or icon indicator
```

## Step-by-Step Process

### Step 1: Identify All Styling
1. Search for all `setStyleSheet` calls in the codebase
2. Review each one to determine if it's purely visual or functional
3. Make a list of files that need modification

### Step 2: Remove Styling Safely
For each file:
1. Read the entire file to understand context
2. Identify which `setStyleSheet` calls are purely visual
3. Remove only the visual styling
4. If styling was used for functional purposes (like indicating state), consider alternative approaches:
   - Use icons or labels
   - Use widget properties (enabled/disabled state)
   - Use different widget types
   - Keep minimal functional styling only if absolutely necessary

### Step 3: Replace Functional Styling
If styling was used functionally:
- **Font styling**: Replace `setStyleSheet("font-weight: bold")` with `QFont().setBold(True)`
- **Text emphasis**: Use QFont for titles/headers
- **State indication**: Use widget properties or alternative visual indicators

### Step 4: Update Main Function
- Modify `main()` to use system-native styling
- Test on target operating systems

### Step 5: Verify Functionality
After removing styling:
- Test all buttons still work
- Test all dialogs still function
- Test all data processing still works
- Verify no functional code was accidentally removed
- Check that visual state indicators (if any) still work through alternative means

## Common Patterns to Remove

### Pattern 1: Button Styling
```python
# REMOVE THIS:
button.setStyleSheet("""
    QPushButton {
        background-color: #27ae60;
        color: white;
        border: none;
        border-radius: 5px;
    }
""")

# KEEP THIS (functional):
button.clicked.connect(self.some_function)
```

### Pattern 2: Label Styling
```python
# REMOVE THIS:
label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")

# KEEP THIS (functional):
font = QFont()
font.setBold(True)
font.setPointSize(18)
label.setFont(font)
```

### Pattern 3: Frame Styling
```python
# REMOVE THIS:
frame.setStyleSheet("""
    QFrame {
        border: 2px solid #bdc3c7;
        background-color: #f8f9fa;
    }
""")

# KEEP THIS (functional, if needed for visual separation):
frame.setFrameStyle(QFrame.Box)  # This is okay, it's a functional frame style
```

### Pattern 4: Input Field Styling
```python
# REMOVE THIS:
line_edit.setStyleSheet("""
    QLineEdit {
        padding: 10px;
        border: 2px solid #bdc3c7;
        border-radius: 5px;
    }
""")

# KEEP THIS (functional):
line_edit.setPlaceholderText("Enter text...")
line_edit.setReadOnly(True)
```

## Special Cases

### Case 1: Highlighting/State Indication
If styling was used to indicate state (like a selected button):
- **Option A**: Remove the visual indication if it's not critical
- **Option B**: Use widget properties (like `setEnabled(False)` for disabled state)
- **Option C**: Add a simple visual indicator widget (like a small icon or label)
- **Option D**: Use native widget selection states if available

### Case 2: Functional Borders
If borders were used to indicate state (like "show on frame" checkbox):
- Consider removing the border color change
- Or use a minimal native approach
- Or add a text label indicator instead

### Case 3: Required Visual Feedback
If styling provided critical user feedback:
- Find alternative native approaches
- Use widget states (enabled/disabled, checked/unchecked)
- Use icons or labels for status indication
- Only keep minimal styling if absolutely necessary for functionality

## Testing Checklist

After implementation, verify:
- [ ] All buttons work correctly
- [ ] All dialogs open and function
- [ ] All form inputs work
- [ ] All data processing works
- [ ] No functional code was removed
- [ ] Application looks native on target OS
- [ ] No visual styling remains (except system-native)
- [ ] All state indicators still work (if they were functional)
- [ ] Text wrapping and alignment still work
- [ ] All widget layouts are correct

## Files That Should NOT Be Modified

- Any file in `src/particle_processing.py` - this is pure logic
- Any file in `src/config_manager.py` - this is configuration logic
- Any file in `src/file_controller.py` - this is file I/O logic
- Any file in `src/project_manager.py` - this is project management logic
- Core logic in widget files - only remove styling, not functionality

## Final Notes

1. **When in doubt, keep the code** - It's better to leave some styling than to break functionality
2. **Test thoroughly** - Make sure nothing breaks after removing styling
3. **Use system defaults** - Let Qt handle all visual appearance
4. **Preserve functionality** - If something was styled for a functional reason, find an alternative approach rather than just removing it
5. **Check for hidden dependencies** - Some code might depend on styling for functionality (like color changes indicating state)

## Example: Complete File Transformation

### Before (with styling):
```python
button = QPushButton("Click Me")
button.setStyleSheet("""
    QPushButton {
        background-color: #27ae60;
        color: white;
        border-radius: 5px;
        padding: 10px;
    }
    QPushButton:hover {
        background-color: #229954;
    }
""")
button.clicked.connect(self.handle_click)
```

### After (native styling):
```python
button = QPushButton("Click Me")
button.clicked.connect(self.handle_click)
# That's it! Qt will use native system styling
```

