from .jsonfile import JsonFile, cache

config = JsonFile('./config/config.jsonc')
exceptions = JsonFile('./config/exceptions.jsonc')

def reload():
    global config, exceptions
    config = JsonFile('./config/config.jsonc', force_load=True)
    exceptions = JsonFile('./config/exceptions.jsonc', force_load=True)