import configparser
import os

def get_config():
    """
    Reads the config.txt file and returns a dictionary of settings.
    """
    config = configparser.ConfigParser()
    # Assuming config.txt is in the same directory as main.py
    config_path = os.path.join(os.path.dirname(__file__), 'config.txt')
    config.read(config_path)
    
    # Create a dictionary to hold the configuration
    config_dict = {}
    if 'Paths' in config:
        for key, value in config['Paths'].items():
            # Prepend the project root directory to make paths absolute
            config_dict[key] = os.path.join(os.path.dirname(__file__), value)
    
    return config_dict

def get_detection_params():
    """Read detection parameters from config.txt under [Detection]."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.txt')
    config.read(config_path)

    params = {
        'feature_size': 15,
        'min_mass': 100.0,
        'invert': False,
        'threshold': 0.0,
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

    return params

def save_detection_params(params):
    """Write detection parameters to config.txt under [Detection]."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.txt')
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
