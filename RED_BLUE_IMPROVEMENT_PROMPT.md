# Red-Blue Feature Improvement Prompt

## Context
The current red-blue gallery feature needs significant enhancement to become a useful tool for identifying problematic trajectory links. The current implementation shows the first and last frames of the 5 most deviant trajectories, but this doesn't help users identify where bad linking decisions occurred.

## Current Implementation Issues
1. **Poor frame selection**: Shows first vs last frame of trajectories, but bad linking happens at intermediate transitions
2. **No specific link information**: Doesn't highlight which exact frame-to-frame connection caused the problem
3. **Missing useful metadata**: No info about deviation scores, jump distances, or parameter mismatches
4. **Inadequate filtering**: Only shows 5 trajectories without proper thresholding

## Desired Behavior

### 1. Identify Worst Individual Links, Not Entire Trajectories
Instead of scoring entire trajectories, identify the worst individual frame-to-frame links within trajectories based on:
- **Jump distance exceeding search_range**: Calculate `jump_dist = sqrt(dx^2 + dy^2)` for each consecutive frame pair
- **Frame gaps exceeding memory**: Links where particle disappeared for longer than memory parameter
- **Deviation score**: `deviation = max(0, jump_dist - search_range)`
- **Score each link**: Higher score = worse link, similar to current trajectory scoring

### 2. Show the Specific Problem Link
For each worst link, show:
- **Frame i** (red overlay) - where particle was before the bad link
- **Frame i+1** (blue overlay) - where particle moved to in the bad link
- This shows the EXACT problematic transition, not just start/end of trajectory

### 3. Add Filtering Thresholds (Like Errant Particle Gallery)
Similar to how `find_and_save_errant_particles` filters the worst particles, add user-configurable thresholds:
- **Minimum deviation**: Only show links where `jump_dist > search_range * threshold_multiplier` (e.g., 1.5x)
- **Minimum score**: Only show links above a certain deviation score
- **Maximum number to display**: Keep top N worst links (not just 5)

### 4. Add Information Display (Like Errant Particle Gallery)
Create `.txt` files alongside each RB overlay image containing:
```
particle_id: X
frame_i: Y
frame_i+1: Y+1
jump_distance: Z pixels
search_range: S pixels
deviation: D pixels (jump_distance - search_range)
frame_gap: G frames
memory: M frames
score: T (calculated deviation score)
```

### 5. Track the Worst Frame Transition
Store which specific pair of consecutive frames caused each bad link:
- Iterate through trajectory: `for i in range(len(particle_data) - 1)`
- For each pair `(curr, next_p)`, calculate link metrics
- Track the frame pair with highest deviation/score
- Display that specific frame pair in red-blue overlay

### 6. Technical Implementation Details

#### Modified `create_rb_gallery` function:
```python
def create_rb_gallery(trajectories_file, frames_folder=None, output_folder=None, 
                     search_range=None, memory=None, min_deviation_multiplier=1.5, max_displays=10):
    """
    Creates red-blue overlay images for the worst individual trajectory links.
    
    Key changes:
    - Score each frame-to-frame link, not entire trajectories
    - Identify the worst link in each trajectory
    - Only show links exceeding minimum deviation threshold
    - Display that specific frame pair (not first/last)
    - Save metadata in .txt files
    """
    # ... existing setup code ...
    
    # Score individual links instead of trajectories
    link_scores = []
    for particle_id in unique_particles:
        particle_data = trajectories[trajectories['particle'] == particle_id].sort_values('frame')
        
        if len(particle_data) < 2:
            continue
        
        worst_link = None
        worst_score = 0
        
        for i in range(len(particle_data) - 1):
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
            excess_gap = max(0, (frame_gap - 1) - memory) if frame_gap > 1 else 0
            link_score = (jump_dist - search_range) * 10 + deviation + excess_gap * 5
            
            # Track worst link in this trajectory
            if link_score > worst_score:
                worst_score = link_score
                worst_link = {
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
        
        # Add worst link from this trajectory
        if worst_link and worst_link['deviation'] > (search_range * (min_deviation_multiplier - 1)):
            link_scores.append(worst_link)
    
    # Sort by score and take top N
    link_scores.sort(key=lambda x: x['score'], reverse=True)
    top_links = link_scores[:max_displays]
    
    # Create RB overlay for each worst link showing the actual problem frames
    for link_info in top_links:
        frame_i = link_info['frame_i']
        frame_i1 = link_info['frame_i1']
        
        # Load the two frames where the bad link occurred
        # Construct filenames from frame numbers (not array indices)
        frame1_filename = os.path.join(frames_folder, f"frame_{frame_i:05d}.jpg")
        frame2_filename = os.path.join(frames_folder, f"frame_{frame_i1:05d}.jpg")
        frame1 = cv2.imread(frame1_filename)
        frame2 = cv2.imread(frame2_filename)
        
        if frame1 is None or frame2 is None:
            print(f"Warning: Could not load frames {frame_i} or {frame_i1}")
            continue
        
        # ... existing thresholding and overlay code ...
        
        # Save metadata
        metadata_text = f"""particle_id: {link_info['particle_id']}
frame_i: {frame_i}
frame_i+1: {frame_i1}
jump_distance: {link_info['jump_dist']:.2f} pixels
search_range: {search_range} pixels
deviation: {link_info['deviation']:.2f} pixels
frame_gap: {link_info['frame_gap']} frames
memory: {memory} frames
score: {link_info['score']:.2f}"""
        
        # Save .txt file
        # ... existing save code ...
```

### 7. Enhanced ErrantTrajectoryGalleryWidget
Add an info panel similar to ErrantParticleGalleryWidget to display the metadata:
- Add `info_label` widget
- Load and display the corresponding `.txt` file for each RB overlay
- This provides context about why each link is problematic

## Implementation Steps
1. Modify `create_rb_gallery` in `src/particle_processing.py` to:
   - Score individual links instead of trajectories
   - Track the worst frame transition per trajectory
   - Apply minimum deviation filtering
   - Save metadata files

2. Update `ErrantTrajectoryGalleryWidget.py` to:
   - Add info display panel
   - Load and display metadata files
   - Better user experience

3. Consider adding configuration parameters:
   - `min_deviation_multiplier` in config.ini
   - `max_displays` in config.ini
   - Possibly move thresholding logic to a separate function for reusability

## Why This Approach Works
1. **Shows actual problems**: Displays the exact frame transition causing issues, not just trajectory start/end
2. **Actionable information**: User sees where linking failed and why (deviation, gaps, etc.)
3. **Consistent with existing patterns**: Mirrors the errant particle gallery approach
4. **Better filtering**: Only shows truly problematic links, not just "top 5 trajectories"
5. **Metadata-driven**: Info files provide quantitative reasons for each flagged link

## Additional Considerations
- Trackpy operates on frame-to-frame links, so identifying bad individual links aligns with how linking works
- The red-blue overlay visualization approach remains the same, just applied to the right frames
- Users can review multiple worst links from different trajectories, not just 5 total
- Thresholding prevents information overload while highlighting genuine problems

## Critical Bug Fix Needed
The current code has a critical bug at line 534-544 in `create_rb_gallery`: it treats the frame NUMBER from the trajectory data as an INDEX into the frame_files array. This will fail because:
- Frame numbers might not start at 0
- Frame numbers might have gaps
- The `frame` column contains actual frame numbers, not array indices

**Fix**: The frame filenames follow the pattern `frame_{frame_number:05d}.jpg` (e.g., `frame_00005.jpg`). 
- Replace: `frame1 = cv2.imread(frame_files[frame1_idx])`
- With: `frame_filename = f"frame_{frame_i:05d}.jpg"` and construct the full path from frames_folder
- This way we use the actual frame number to construct the filename, not an array index

The prompt implementation should address this mapping issue properly by constructing filenames from frame numbers rather than using array indices.

