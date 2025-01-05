import os

from .jsonfile import JsonFile

config : dict = JsonFile(os.environ["CONFIG_PATH"], force_load=True)
exceptions : dict = JsonFile(config["paths"]["exceptions"], force_load=True)

def reload_config_files():
    global config, exceptions
    config = JsonFile(os.environ["CONFIG_PATH"], force_load=True)
    exceptions = JsonFile(config["paths"]["exceptions"], force_load=True)