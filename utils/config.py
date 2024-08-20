import json
import os

from utils.constants import CONFIG_PATH, DEFAULT_CONFIG_PATH
from utils.debug_utils import debug_print


def save_config_key(key, value):
    # Saves a single key-value pair to the configuration file.
    config = load_config()
    config[key] = value
    save_config(config)


def load_config():
    # Loads the configuration from a file, checks its integrity, and saves it if it's incomplete.
    # Returns:
    # dict: The loaded and possibly updated configuration.
    config = {}
    if os.path.exists(CONFIG_PATH) :
        with open(CONFIG_PATH, 'r') as config_file:
            config = json.load(config_file)
            if check_config_integrity(config):
                debug_print("Config loaded.")
                return config

    load_and_save_default_config()

    return config


def load_and_save_default_config():
    # Loads the default configuration from a file and saves it to the config file.
    with open(DEFAULT_CONFIG_PATH, 'r') as default_config_file:
        config = json.load(default_config_file)
        save_config(config)
        debug_print("Default config loaded and saved.")


def check_config_integrity(config):
    # Checks if the config is complete and updates it with default values if necessary.
    # Args:
    # config (dict): The configuration to check.
    #
    # Returns:
    # bool: True if the configuration was already complete, False if it was updated.
    with open(DEFAULT_CONFIG_PATH, 'r') as default_config_file:
        default_config = json.load(default_config_file)

    updated = False
    for key in default_config:
        if key not in config:
            config[key] = default_config[key]
            updated = True
            debug_print("Config incomplete")

    return not updated


def save_config(config):
    # Saves the configuration to a file.
    # Args:
    # config (dict): The configuration to save.
    with open(CONFIG_PATH, 'w') as config_file:
        json.dump(config, config_file, indent=4)
        debug_print("Config saved.")


def get_value(key):
    config = load_config()
    return config.get(key, None)
