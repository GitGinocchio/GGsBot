from .MusicUtilities import Song
import yt_dlp as youtube_dl
from urllib import parse
import asyncio

class YoutubeExtension(youtube_dl.YoutubeDL):
    def __init__(self, *, loop : asyncio.AbstractEventLoop, params : dict):
        super().__init__(params)
        self.loop = loop
    
    def isvalid(self, url : str):
        #https://www.youtube.com/watch?v=XXYlFuWEuKI
        #https://www.youtube.com/watch?v=XXYlFuWEuKI&list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj
        parsed = parse.urlparse(url)
        if 'youtube.com' in parsed.netloc and parsed.path == '/watch':
            return True
        else:
            return False

    async def get_info(self, queryorurl : str):
        if self.isvalid(queryorurl): url = queryorurl
        else: url = f'ytsearch: {queryorurl}'

        data = await self.loop.run_in_executor(None, lambda: self.extract_info(url, download=False))

        if not data: return None

        if not 'entries' in data: return Song(data)

        tracks = [Song(entrie) for entrie in data['entries'] if 'url' in entrie]

        return tracks