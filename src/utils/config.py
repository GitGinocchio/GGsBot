from .jsonfile import JsonFile, cache

config = JsonFile('./src/config/config.jsonc')
exceptions = JsonFile('./src/config/exceptions.json')

def reload():
    global config, exceptions
    config = JsonFile('./src/config/config.jsonc', force_load=True)
    exceptions = JsonFile('./src/config/exceptions.json', force_load=True)