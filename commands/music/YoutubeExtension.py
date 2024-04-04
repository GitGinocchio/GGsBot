from urllib import parse
import youtube_dl
import asyncio


class YoutubeExtension(youtube_dl.YoutubeDL):
    def __init__(self, *, loop : asyncio.AbstractEventLoop, params : dict):
        super().__init__(params)
        self.loop = loop
    
    def isvalid(self, url : str):
        parsed = parse.urlparse(url)
        if 'youtube.com' in parsed.netloc and parsed.path == '/watch':
            return True
        else:
            return False
    
    async def get_info(self, queryorurl : str):
        if self.isvalid(queryorurl): url = queryorurl
        else: url = f'ytsearch: {queryorurl}'

        data = await self.loop.run_in_executor(None, lambda: self.extract_info(url, download=False))
        
        #print(data.keys())

        return data