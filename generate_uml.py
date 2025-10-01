
import graphviz

def generate_uml_diagram():
    dot = graphviz.Digraph('UML_Design_Diagram', comment='UML Design Diagram for Particle Tracking GUI')
    dot.attr('node', shape='record', style='filled', fillcolor='lightblue')
    dot.attr('edge', arrowhead='vee')

    # Main Application
    dot.node('MainWindow', '{MainWindow|+ switch_window()\l}')

    # Windows
    dot.node('ParticleDetectionWindow', '{ParticleDetectionWindow|+ show()\l}')
    dot.node('TrajectoryLinkingWindow', '{TrajectoryLinkingWindow|+ show()\l}')

    # Widgets
    dot.node('GraphingWidget', '{GraphingWidget|+ plot_subpixel_bias()\l+ plot_mass_vs_ecc()\l}')
    dot.node('VideoPlayerWidget', '{VideoPlayerWidget|+ play()\l+ pause()\l+ next_frame()\l+ prev_frame()\l}')
    dot.node('ErrantParticleGalleryWidget', '{ErrantParticleGalleryWidget|+ show_next_particle()\l+ show_prev_particle()\l}')
    dot.node('ParticleInfoWidget', '{ParticleInfoWidget|+ display_info()\l}')
    dot.node('ParticleDetectionParametersWidget', '{ParticleDetectionParametersWidget|+ get_parameters()\l}')
    dot.node('FindParticlesButton', '{FindParticlesButton|+ find_particles()\l}')

    # Relationships
    dot.edge('MainWindow', 'ParticleDetectionWindow', label='manages')
    dot.edge('MainWindow', 'TrajectoryLinkingWindow', label='manages')

    dot.edge('ParticleDetectionWindow', 'GraphingWidget', label='has a')
    dot.edge('ParticleDetectionWindow', 'VideoPlayerWidget', label='has a')
    dot.edge('ParticleDetectionWindow', 'ErrantParticleGalleryWidget', label='has a')
    dot.edge('ParticleDetectionWindow', 'ParticleInfoWidget', label='has a')
    dot.edge('ParticleDetectionWindow', 'ParticleDetectionParametersWidget', label='has a')
    dot.edge('ParticleDetectionWindow', 'FindParticlesButton', label='has a')

    dot.render('uml_design', format='png', view=True)

if __name__ == "__main__":
    generate_uml_diagram()
