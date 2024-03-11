from urllib import parse
import youtube_dl
import asyncio


ytapi = youtube_dl.YoutubeDL({'format': 'bestaudio','quiet': True,"postprocessor" : {'key' : "FFmpegExtractAudio","preferredcodec" : "mp3","preferredquality" : "192"}})
loop = asyncio.get_event_loop()


def isvalid_youtube_url(url):
        fragments = parse.urlparse(url)
        print(fragments)
        return True if parse.urlparse(url).netloc.startswith('youtu.be') else False

async def get_info_from_url(url : str):
    with ytapi as api:
        return await loop.run_in_executor(None, lambda: api.extract_info(url, download=False))
    
async def get_info_from_query(query : str):
    with ytapi as api:
        return await loop.run_in_executor(None, lambda: api.extract_info(f"ytsearch:{query}", download=False))