import graphviz

def generate_uml_diagram():
    """
    Generates and displays a UML diagram for the application structure.
    """
    dot = graphviz.Digraph('UML_Design_Diagram', comment='UML Design Diagram for Particle Tracking GUI')
    dot.attr('node', shape='record', style='filled', fillcolor='lightblue')
    dot.attr('edge', arrowhead='vee')

    # --- Main application entry point ---
    dot.node('main.py', '{main.py|+ show_particle_detection_window()\l+ show_trajectory_linking_window()\l}')

    # --- Main windows ---
    dot.node('ParticleDetectionWindow', '{ParticleDetectionWindow|+ setup_ui()\l}')
    dot.node('TrajectoryLinkingWindow', '{TrajectoryLinkingWindow|+ setup_ui()\l}')

    # --- Widgets (Particle Detection) ---
    dot.node('GraphingPanelWidget', '{GraphingPanelWidget|}')
    dot.node('FramePlayerWidget', '{FramePlayerWidget|+ go_to_frame()\l+ display_frame()\l+ load_video()\l}')
    dot.node('ErrantParticleGalleryWidget', '{ErrantParticleGalleryWidget|+ load_particle_files()\l+ next_particle()\l+ prev_particle()\l}')
    dot.node('DetectionParametersWidget', '{DetectionParametersWidget|+ save_params()\l+ find_particles()\l}')

    # --- Widgets (Trajectory Linking) ---
    dot.node('TrajectoryPlottingWidget', '{TrajectoryPlottingWidget|}')
    dot.node('TrajectoryPlayerWidget', '{TrajectoryPlayerWidget|+ display_trajectory_image()}')
    dot.node('ErrantTrajectoryGalleryWidget', '{ErrantTrajectoryGalleryWidget|+ load_rb_gallery_files()\l+ next_trajectory()\l+ prev_trajectory()\l}')
    dot.node('LinkingParametersWidget', '{LinkingParametersWidget|+ save_params()\l+ find_trajectories()\l}')

    # --- Relationships ---

    # main.py imports the main windows
    dot.edge('main.py', 'ParticleDetectionWindow', style='dashed', arrowhead='open', label=' «import»')
    dot.edge('main.py', 'TrajectoryLinkingWindow', style='dashed', arrowhead='open', label=' «import»')

    # ParticleDetectionWindow imports its widgets
    dot.edge('ParticleDetectionWindow', 'GraphingPanelWidget', style='dashed', arrowhead='open', label=' «import»')
    dot.edge('ParticleDetectionWindow', 'FramePlayerWidget', style='dashed', arrowhead='open', label=' «import»')
    dot.edge('ParticleDetectionWindow', 'ErrantParticleGalleryWidget', style='dashed', arrowhead='open', label=' «import»')
    dot.edge('ParticleDetectionWindow', 'DetectionParametersWidget', style='dashed', arrowhead='open', label=' «import»')

    # TrajectoryLinkingWindow imports its widgets
    dot.edge('TrajectoryLinkingWindow', 'TrajectoryPlottingWidget', style='dashed', arrowhead='open', label=' «import»')
    dot.edge('TrajectoryLinkingWindow', 'TrajectoryPlayerWidget', style='dashed', arrowhead='open', label=' «import»')
    dot.edge('TrajectoryLinkingWindow', 'ErrantTrajectoryGalleryWidget', style='dashed', arrowhead='open', label=' «import»')
    dot.edge('TrajectoryLinkingWindow', 'LinkingParametersWidget', style='dashed', arrowhead='open', label=' «import»')

    # Render and display the diagram
    dot.render('uml_design', format='png', view=True)

if __name__ == "__main__":
    generate_uml_diagram()