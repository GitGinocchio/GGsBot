from logging import Logger
import os

from .jsonfile import JsonFile

CONFIG_PATH = os.environ['CONFIG_PATH']

config : dict = JsonFile(CONFIG_PATH, force_load=True)
exceptions : dict = JsonFile(config["paths"]["exceptions"], force_load=True)

def reload_config_files():
    global config, exceptions
    config = JsonFile(CONFIG_PATH, force_load=True)
    exceptions = JsonFile(config["paths"]["exceptions"], force_load=True)

def show_paths(logger : Logger):
    message = 'Config paths:'
    for type, path in config['paths'].items():
        message += f'\n{type:<20}: {path}'
    logger.debug(message)

DEBUG_MODE =            bool(config.get('DEBUG_MODE', False))

TOKEN =                 os.environ.get('TOKEN',              None)
PUBLIC_KEY =            os.environ.get('PUBLIC_KEY',         None)
CLIENT_SECRET =         os.environ.get('CLIENT_SECRET',      None)
APPLICATION_ID =        os.environ.get('APPLICATION_ID',     None)
CLIENT_ID =             os.environ.get('CLIENT_ID',          None)

DEVELOPER_ID =          os.environ.get('DEVELOPER_ID',       None)
DEVELOPER_GUILD_ID =    os.environ.get('DEVELOPER_GUILD_ID', None)

# Development

DEV_TOKEN =             os.environ.get('DEV_TOKEN',          None)
DEV_PUBLIC_KEY =        os.environ.get('DEV_PUBLIC_KEY',     None)
DEV_CLIENT_SECRET =     os.environ.get('DEV_CLIENT_SECRET',  None)
DEV_APPLICATION_ID =    os.environ.get('DEV_APPLICATION_ID', None)
DEV_CLIENT_ID =         os.environ.get('DEV_CLIENT_ID',      None)