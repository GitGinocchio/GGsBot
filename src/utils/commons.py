from nextcord import IntegrationType, Interaction, Colour
from functools import wraps
from typing import Callable
from enum import StrEnum
import aiohttp

from .config import     \
    DEVELOPER_GUILD_ID, \
    DEVELOPER_ID

class Extensions(StrEnum):
    AICHATBOT = 'aichatbot'
    GREETINGS = 'greetings'
    CHEAPGAMES = 'cheapgames'
    VALQUIZ = 'valquiz'
    STAFF = 'staff'
    TEMPVC = 'tempvc'
    VERIFY = 'verify'

GLOBAL_INTEGRATION = [
    IntegrationType.guild_install,
    IntegrationType.user_install
]

GUILD_INTEGRATION = [
    IntegrationType.guild_install,
]

USER_INTEGRATION = [
    IntegrationType.user_install
]

def hex_to_rgb(hex : str) -> tuple[int, int, int]:
    """
    Converts a hexadecimal color code to RGB format.
    Args:
       hex (:class:`str`): The hexadecimal color code to convert.
    Returns:
       :class:`tuple[int, int, int]`: The RGB color values as a tuple.
    """
    hex = hex.lstrip('#').replace("0x", "")
    int_color = int(hex.replace("0x", ""), 16)
    r = (int_color >> 16) & 0xFF
    g = (int_color >> 8) & 0xFF
    b = int_color & 0xFF
    return (r, g, b)

def hex_to_colour(hex : str) -> Colour:
    """
    Converts a hexadecimal color code to a Colour object.
    Args:
       hex (:class:`str`): The hexadecimal color code to convert.
    Returns:
       :class:`Colour`: The Colour object representing the color.
    """
    return Colour.from_rgb(*hex_to_rgb(hex))

sessions : dict[str, aiohttp.ClientSession] = {}

def getbaseurl(url : str):
    return (splitted_url:=url.split('/'))[0] + '//' + splitted_url[2]

def getsession(url : str, **kwargs):
    base_url = getbaseurl(url)
    if base_url not in sessions:
        sessions[base_url] = aiohttp.ClientSession(**kwargs)

    return sessions[base_url]


async def asyncget(
        url : str = "",
        data : str = None, 
        json : dict = None,
        headers : dict = None,
        cookies : dict = None,
        timeout : int = 60,
        max_redirects : int = 5,
        session : aiohttp.ClientSession = None,
        **session_kwargs
    ) -> tuple[str, bytes, int, str | None]:
    """
    Sends a GET request to the given URL asynchronously.

    Args:
        url (str): The URL to send the request to.
        data (dict | str | bytes, None): The payload to send in the body. Defaults to None.
        json (dict, None): JSON data to send instead of 'data'. Defaults to None.
        headers (dict, None): HTTP headers to include in the request. Defaults to None.
        cookies (dict, None): Cookies to include in the request. Defaults to None.
        timeout (int, None): The maximum time to wait for the response in seconds. Defaults to 60.
        max_redirects (int, None): The maximum number of redirects to follow. Defaults to 5.
        session (aiohttp.ClientSession, None): An existing session to reuse. Defaults to None.

    Returns:
        tuple: A tuple containing:
        \t- str: The content type of the response.
        \t- bytes: The raw content of the response.
        \t- int: The HTTP status code of the response.
        \t- str | None: The reason phrase returned by the server, or None if not provided.
    """
    session = getsession(url, **session_kwargs) if not session else session

    async with session.get(url, timeout=timeout, max_redirects=max_redirects, data=data, json=json, headers=headers, cookies=cookies) as response:
        return response.content_type, await response.content.read(), response.status, response.reason

async def asyncpost(
        url : str = "",
        data : str = None, 
        json : dict = None,
        headers : dict = None,
        cookies : dict = None,
        timeout : int = 60,
        max_redirects : int = 5,
        session : aiohttp.ClientSession = None,
        **session_kwargs
    ) -> tuple[str, bytes, int, str | None]:
    """
    Sends a POST request to the given URL asynchronously.

    Args:
        url (str): The URL to send the request to.
        data (dict | str | bytes, None): The payload to send in the body. Defaults to None.
        json (dict, None): JSON data to send instead of 'data'. Defaults to None.
        headers (dict, None): HTTP headers to include in the request. Defaults to None.
        cookies (dict, None): Cookies to include in the request. Defaults to None.
        timeout (int, None): The maximum time to wait for the response in seconds. Defaults to 60.
        max_redirects (int, None): The maximum number of redirects to follow. Defaults to 5.
        session (aiohttp.ClientSession, None): An existing session to reuse. Defaults to None.

    Returns:
        tuple: A tuple containing:
        \t- str: The content type of the response.
        \t- bytes: The raw content of the response.
        \t- int: The HTTP status code of the response.
        \t- str | None: The reason phrase returned by the server, or None if not provided.
    """
    session = getsession(url, **session_kwargs) if not session else session

    async with session.post(url, timeout=timeout, max_redirects=max_redirects, data=data, json=json, headers=headers, cookies=cookies) as response:
        return response.content_type, await response.content.read(), response.status, response.reason

# TODO: Sostituire con un metodo generico per fare una richiesta HTTP get/post/ecc.
async def asyncrequest(): pass
    

# Commons slash commands checks

def isdeveloper(*, behavior : Callable = None):
    """
    Decorator that checks if the user who is calling a slash_command is the `developer` of the bot
    if the answer is yes than it will execute the `decorated function` otherwise it will execute the `behavior` function.\n
    By default the behavior is to send a message saying that the user doesn't have permission to use this command.
    """
    def decorator(func : Callable):
        @wraps(func)
        async def wrapper(self, interaction : Interaction, *args, **kwargs):  
            if str(interaction.user.id) == DEVELOPER_ID: 
                return await func(self, interaction, *args, **kwargs)
            
            if not behavior:
                await interaction.send("Only the owner of the bot can use this command.", ephemeral=True, delete_after=5)
            else:
                await behavior(self, interaction, *args, **kwargs)
        return wrapper
    return decorator

async def isdeveloperguild(func : Callable, *, behavior : Callable = None):
    pass

async def isowner(func : Callable, *, behavior : Callable = None):
    pass