from .jsonfile import JsonFile

config = JsonFile('./config/config.jsonc')


def reload():
    global config
    config = JsonFile('./config/config.jsonc')