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
