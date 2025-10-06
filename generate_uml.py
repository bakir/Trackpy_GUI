import graphviz


def generate_uml_diagram():
    dot = graphviz.Digraph('UML_Design_Diagram', comment='UML Design Diagram for Particle Tracking GUI')
    dot.attr('node', shape='record', style='filled', fillcolor='lightblue')
    dot.attr('edge', arrowhead='vee')

    # --- Place windows on the same level ---
    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('ParticleDetectionWindow', '{ParticleDetectionWindow|+ setup_ui()\l+ go_to_linking()\l+ import_video()\l+ export_data()\l}')
        s.node('TrajectoryLinkingWindow', '{TrajectoryLinkingWindow|+ setup_ui()\l+ go_to_detection()\l+ export_data()\l+ go_to_detection()\l}')

    # Widgets (Particle Detection)
    dot.node('GraphingPanelWidget', '{GraphingPanelWidget|}')
    dot.node('FramePlayerWidget', '{FramePlayerWidget|+ extract_frames()\l+ select_frame()\l+ display_frame()\l}')
    dot.node('ErrantParticleGalleryWidget', '{ErrantParticleGalleryWidget|+ next_particle()\l+ prev_particle()\l}')
    dot.node('DetectionParametersWidget', '{DetectionParametersWidget|+ save_params()\l+ find_particles()\l}')

    # Widgets (Trajectory Linking)
    dot.node('TrajectoryPlottingWidget', '{TrajectoryPlottingWidget|}')
    dot.node('TrajectoryPlayerWidget', '{TrajectoryPlayerWidget|+ display_trajectory_plot()}')
    dot.node('ErrantTrajectoryGalleryWidget', '{ErrantTrajectoryGalleryWidget|+ load_rb_gallery_files()\l+ next_trajectory()\l+ prev_trajectory()\l}')
    dot.node('LinkingParametersWidget', '{LinkingParametersWidget|+ save_params()\l+ find_trajectories()\l}')

    # Composition: ParticleDetectionWindow has widgets
    dot.edge('ParticleDetectionWindow', 'GraphingPanelWidget', label='has')
    dot.edge('ParticleDetectionWindow', 'FramePlayerWidget', label='has')
    dot.edge('ParticleDetectionWindow', 'ErrantParticleGalleryWidget', label='has')
    dot.edge('ParticleDetectionWindow', 'DetectionParametersWidget', label='has')

    # Composition: TrajectoryLinkingWindow has widgets
    dot.edge('TrajectoryLinkingWindow', 'TrajectoryPlottingWidget', label='has')
    dot.edge('TrajectoryLinkingWindow', 'TrajectoryPlayerWidget', label='has')
    dot.edge('TrajectoryLinkingWindow', 'ErrantTrajectoryGalleryWidget', label='has')
    dot.edge('TrajectoryLinkingWindow', 'LinkingParametersWidget', label='has')

    dot.render('uml_design', format='png', view=True)


if __name__ == "__main__":
    generate_uml_diagram()