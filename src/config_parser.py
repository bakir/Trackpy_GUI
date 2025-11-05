import configparser
import os

def get_config():
    """
    Reads the config.ini file and returns a dictionary of settings.
    """
    config = configparser.ConfigParser()
    # Assuming config.ini is in the same directory as main.py
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_path)
    
    # Create a dictionary to hold the configuration
    config_dict = {}
    if 'Paths' in config:
        for key, value in config['Paths'].items():
            # Prepend the project root directory to make paths absolute
            config_dict[key] = os.path.join(os.path.dirname(__file__), value)
    
    # Add rb_gallery folder path
    config_dict['rb_gallery_folder'] = os.path.join(os.path.dirname(__file__), 'rb_gallery')
    
    return config_dict

def get_detection_params():
    """Read detection parameters from config.ini under [Detection]."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_path)

    params = {
        'feature_size': 15,
        'min_mass': 100.0,
        'invert': False,
        'threshold': 0.0,
        'frame_idx': 0,
    }

    if config.has_section('Detection'):
        section = config['Detection']
        if 'feature_size' in section:
            try:
                params['feature_size'] = int(section.get('feature_size'))
            except Exception:
                pass
        if 'min_mass' in section:
            try:
                params['min_mass'] = float(section.get('min_mass'))
            except Exception:
                pass
        if 'invert' in section:
            try:
                val = section.get('invert').strip().lower()
                params['invert'] = val in ('1', 'true', 'yes', 'on')
            except Exception:
                pass
        if 'threshold' in section:
            try:
                params['threshold'] = float(section.get('threshold'))
            except Exception:
                pass
        if 'frame_idx' in section:
            try:
                params['frame_idx'] = int(section.get('frame_idx'))
            except Exception:
                pass

    return params

def save_detection_params(params):
    """Write detection parameters to config.ini under [Detection]."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    # Read existing config if present
    if os.path.exists(config_path):
        config.read(config_path)

    if not config.has_section('Detection'):
        config.add_section('Detection')

    config['Detection']['feature_size'] = str(int(params.get('feature_size', 15)))
    config['Detection']['min_mass'] = str(float(params.get('min_mass', 100.0)))
    config['Detection']['invert'] = 'true' if bool(params.get('invert', False)) else 'false'
    config['Detection']['threshold'] = str(float(params.get('threshold', 0.0)))

    with open(config_path, 'w') as f:
        config.write(f)


def get_linking_params():
    """Read linking parameters from config.ini under [Linking]."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_path)

    params = {
        'search_range': 10,
        'memory': 10,
        'min_trajectory_length': 10,
        'fps': 30.0,
        'scaling': 1.0,
        'max_speed': 100.0,
        'max_displays': 5,
    }

    if config.has_section('Linking'):
        section = config['Linking']
        if 'search_range' in section:
            try:
                params['search_range'] = int(section.get('search_range'))
            except Exception:
                pass
        if 'memory' in section:
            try:
                params['memory'] = int(section.get('memory'))
            except Exception:
                pass
        if 'min_trajectory_length' in section:
            try:
                params['min_trajectory_length'] = int(section.get('min_trajectory_length'))
            except Exception:
                pass
        if 'fps' in section:
            try:
                params['fps'] = float(section.get('fps'))
            except Exception:
                pass
        if 'scaling' in section:
            try:
                params['scaling'] = float(section.get('scaling'))
            except Exception:
                pass
        if 'max_speed' in section:
            try:
                params['max_speed'] = float(section.get('max_speed'))
            except Exception:
                pass
        if 'max_displays' in section:
            try:
                params['max_displays'] = int(section.get('max_displays'))
            except Exception:
                pass

    return params


def save_linking_params(params):
    """Write linking parameters to config.ini under [Linking]."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    # Read existing config if present
    if os.path.exists(config_path):
        config.read(config_path)

    if not config.has_section('Linking'):
        config.add_section('Linking')

    config['Linking']['search_range'] = str(int(params.get('search_range', 10)))
    config['Linking']['memory'] = str(int(params.get('memory', 10)))
    config['Linking']['min_trajectory_length'] = str(int(params.get('min_trajectory_length', 10)))
    config['Linking']['fps'] = str(float(params.get('fps', 30.0)))
    config['Linking']['scaling'] = str(float(params.get('scaling', 1.0)))
    config['Linking']['max_speed'] = str(float(params.get('max_speed', 100.0)))
    
    # Save RB gallery parameters if provided
    if 'max_displays' in params:
        config['Linking']['max_displays'] = str(int(params.get('max_displays', 5)))

    with open(config_path, 'w') as f:
        config.write(f)
