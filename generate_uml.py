
import graphviz


def generate_uml_diagram():
    dot = graphviz.Digraph('UML_Design_Diagram', comment='UML Design Diagram for Particle Tracking GUI')
    dot.attr('node', shape='record', style='filled', fillcolor='lightblue')
    dot.attr('edge', arrowhead='vee')

    # Controllers / Windows
    dot.node('MainController', '{MainController|+ show_detection_window()\l+ show_linking_window()\l}')
    dot.node('ParticleDetectionWindow', '{ParticleDetectionWindow|+ setup_ui()\l+ import_video()\l}')
    dot.node('TrajectoryLinkingWindow', '{TrajectoryLinkingWindow|+ setup_ui()\l}')

    # Widgets (Particle Detection)
    dot.node('GraphingPanelWidget', '{GraphingPanelWidget|}')
    dot.node('FramePlayerWidget', '{FramePlayerWidget|+ load_video(path)\l+ next_frame()\l+ previous_frame()\l}')
    dot.node('ErrantParticleGalleryWidget', '{ErrantParticleGalleryWidget|+ next_particle()\l+ prev_particle()\l+ refresh_particles()\l}')
    dot.node('DetectionParametersWidget', '{DetectionParametersWidget|+ save_params()\l+ find_particles()\l}')

    # Widgets (Trajectory Linking)
    dot.node('TrajectoryPlottingWidget', '{TrajectoryPlottingWidget|}')
    dot.node('TrajectoryPlayerWidget', '{TrajectoryPlayerWidget|}')
    dot.node('ErrantTrajectoryGalleryWidget', '{ErrantTrajectoryGalleryWidget|}')
    dot.node('LinkingParametersWidget', '{LinkingParametersWidget|}')

    # Relationships
    dot.edge('MainController', 'ParticleDetectionWindow', label='has a')
    dot.edge('MainController', 'TrajectoryLinkingWindow', label='has a')

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
