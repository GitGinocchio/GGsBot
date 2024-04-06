from .MusicUtilities import *
import yt_dlp as youtube_dl
from urllib import parse
import asyncio

class YoutubeExtension(youtube_dl.YoutubeDL):
    def __init__(self, *, loop : asyncio.AbstractEventLoop, params : dict):
        super().__init__(params)
        self.loop = loop

    async def get_info(self, queryorurl : str):
        url_type = get_url_type(queryorurl)

        if url_type == LinkType.YoutubeLink or url_type == LinkType.YoutubePlaylistLink:
            url = queryorurl
        else:
            url = f'ytsearch: {queryorurl}'

        data = await self.loop.run_in_executor(None, lambda: self.extract_info(url, download=False))

        if not data: return None

        if not 'entries' in data: 
            print("download url: ", data.get('url'))
            return Song(data)

        tracks = [Song(entrie) for entrie in data['entries'] if 'url' in entrie]

        return tracks