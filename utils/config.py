from .jsonfile import JsonFile, cache

config = JsonFile('./config/config.jsonc')

def reload():
    # Eliminare dalla cache il file vecchio e sovrascriverlo... magari aggiungere un parametro all'oggetto JsonFile
    return