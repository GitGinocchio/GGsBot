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

async def asyncget(url : str, mimetype = 'application/json') -> dict | bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            assert response.status == 200, f"Error while fetching {url}: {response.reason}"

            if mimetype == 'application/json':
                return await response.json()
            else:
                return await response.read()

async def safe_asyncget(url : str) -> tuple[str, bytes, int, str | None]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return response.content_type, await response.content.read(), response.status, response.reason