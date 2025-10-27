import graphviz

def generate_uml_diagram():
    """
    Generates and displays an accurate UML diagram for the application structure.
    """
    dot = graphviz.Digraph('UML_Design_Diagram_Corrected', comment='UML Design Diagram for Particle Tracking GUI')
    dot.attr('node', shape='record', style='filled', fillcolor='lightblue')
    
    # --- Main application entry point (The "Whole" or "Controller") ---
    dot.node('main.py', '{main.py|+ show_particle_detection_window()\l+ show_trajectory_linking_window()\l}')

    # --- Main windows (The "Parts") ---
    dot.node('ParticleDetectionWindow', '{ParticleDetectionWindow|+ setup_ui()\l}')
    dot.node('TrajectoryLinkingWindow', '{TrajectoryLinkingWindow|+ setup_ui()\l}')

    # --- Widgets (Particle Detection) ---
    dot.node('GraphingPanelWidget', '{GraphingPanelWidget|+ get_subpixel_bias()\l+ plot_sb()}')
    dot.node('FramePlayerWidget', '{FramePlayerWidget|+ go_to_frame()\l+ display_frame()\l+ load_video()\l}')
    dot.node('ErrantParticleGalleryWidget', '{ErrantParticleGalleryWidget|+ load_particle_files()\l+ next_particle()\l+ prev_particle()\l}')
    dot.node('DetectionParametersWidget', '{DetectionParametersWidget|+ save_params()\l+ find_particles()\l}')

    # --- Widgets (Trajectory Linking) ---
    dot.node('TrajectoryPlottingWidget', '{TrajectoryPlottingWidget|+ create_dummy_scatter_plot()}')
    dot.node('TrajectoryPlayerWidget', '{TrajectoryPlayerWidget|+ display_trajectory_image()}')
    dot.node('ErrantTrajectoryGalleryWidget', '{ErrantTrajectoryGalleryWidget|+ load_rb_gallery_files()\l+ next_trajectory()\l+ prev_trajectory()\l}')
    dot.node('LinkingParametersWidget', '{LinkingParametersWidget|+ save_params()\l+ find_trajectories()\l}')

    # --- Relationships ---

    # main.py is COMPOSED of the main windows it controls
    dot.edge('main.py', 'ParticleDetectionWindow', dir='back', arrowtail='diamond', arrowhead='none')
    dot.edge('main.py', 'TrajectoryLinkingWindow', dir='back', arrowtail='diamond', arrowhead='none')

    # ParticleDetectionWindow is COMPOSED of its widgets
    dot.edge('ParticleDetectionWindow', 'GraphingPanelWidget', dir='back', arrowtail='diamond', arrowhead='none')
    dot.edge('ParticleDetectionWindow', 'FramePlayerWidget', dir='back', arrowtail='diamond', arrowhead='none')
    dot.edge('ParticleDetectionWindow', 'ErrantParticleGalleryWidget', dir='back', arrowtail='diamond', arrowhead='none')
    dot.edge('ParticleDetectionWindow', 'DetectionParametersWidget', dir='back', arrowtail='diamond', arrowhead='none')

    # TrajectoryLinkingWindow is COMPOSED of its widgets
    dot.edge('TrajectoryLinkingWindow', 'TrajectoryPlottingWidget', dir='back', arrowtail='diamond', arrowhead='none')
    dot.edge('TrajectoryLinkingWindow', 'TrajectoryPlayerWidget', dir='back', arrowtail='diamond', arrowhead='none')
    dot.edge('TrajectoryLinkingWindow', 'ErrantTrajectoryGalleryWidget', dir='back', arrowtail='diamond', arrowhead='none')
    dot.edge('TrajectoryLinkingWindow', 'LinkingParametersWidget', dir='back', arrowtail='diamond', arrowhead='none')

    # Render and display the diagram
    dot.render('uml_design', format='png', view=True)

if __name__ == "__main__":
    generate_uml_diagram()