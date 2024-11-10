from enum import StrEnum
import aiohttp

class Levels(StrEnum):
    NOOB = 'Noob'
    EASY = 'Easy'
    MEDIUM = 'Medium'
    HARD = 'Hard'
    PRO = 'Pro'
    RANDOM = 'Random'

class ImageTypes(StrEnum):
    NOOB = 'splash'
    EASY = 'listViewIcon'
    MEDIUM = 'listViewIconTall'
    HARD = 'stylizedBackgroundImage'
    PRO = 'displayIcon'


class MapModes(StrEnum):
    FRAGMENT = 'Fragment'
    NORMAL = 'Normal'

async def asyncget(url : str, mimetype = 'application/json') -> dict | bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            assert response.status == 200, f"Error while fetching {url}: {response.reason}"

            if mimetype == 'application/json':
                return await response.json()
            else:
                return await response.read()

def transform_coordinates(x_game, y_game, x_multiplier, y_multiplier, x_scalar, y_scalar):
    """Funzione per trasformare le coordinate di gioco in coordinate dell'immagine"""
    x_img = (x_game * x_multiplier) + x_scalar
    y_img = (y_game * y_multiplier) + y_scalar
    return int(x_img), int(y_img)