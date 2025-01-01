from enum import StrEnum
import aiohttp

class Extensions(StrEnum):
    AICHATBOT = 'aichatbot'
    GREETINGS = 'greetings'
    CHEAPGAMES = 'cheapgames'
    VALQUIZ = 'valquiz'
    STAFF = 'staff'
    TEMPVC = 'tempvc'
    VERIFY = 'verify'

async def asyncget(url : str, timeout : int = 60, max_redirects : int = 5) -> tuple[str, bytes, int, str | None]:
    """
    Fetches the content from the given URL asynchronously.

    Args:
        url (:class:`str`): The URL to fetch the content from.
        timeout (:class:`int`, optional): The maximum time to wait for the response in seconds. Defaults to 60.
        max_redirects (:class:`int`, optional): The maximum number of redirects to follow. Defaults to 5.

    Returns:
        :class:`tuple`: A tuple containing:\n
            \t- str: The content type of the response.
            \t- bytes: The raw content of the response.
            \t- int: The HTTP status code of the response.
            \t- str | None: The reason phrase returned by the server, or None if not provided.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout, max_redirects=max_redirects) as response:
            return response.content_type, await response.content.read(), response.status, response.reason