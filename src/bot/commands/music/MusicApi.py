from utils.config import config
from .MusicUtilities import *
from .MusicServices import YoutubeExtension,\
                           SpotifyExtension
import asyncio
import os



class MusicApi:
    def __init__(self, loop : asyncio.AbstractEventLoop):
        self.yt = YoutubeExtension(loop=loop,params=config['music']['youtube']['ytdl_params'])
        self.sp = SpotifyExtension(loop=loop,auth={'client_id' : os.environ['SPOTIFY_CLIENT_ID'],'client_secret' : os.environ['SPOTIFY_CLIENT_SECRET']},params=config['music']['spotify']['params'])

    async def get(self, queryurl : str, searchengine : str):

        match urltype(queryurl):
            case UrlType.SpotifySong:
                song = self.sp.getTrack(queryurl)
                await self.yt.assignDownloadUrl([song])
                return song

            case UrlType.SpotifyPlaylist:
                playlist = self.sp.getPlaylist(queryurl)
                await self.yt.assignDownloadUrl(playlist)
                return playlist
            
            case UrlType.SpotifyAlbum:
                album = self.sp.getAlbum(queryurl)
                await self.yt.assignDownloadUrl(album)
                return album

            case UrlType.YoutubeSong | UrlType.YoutubePlaylist:
                song = await self.yt.get(queryurl)
                return song
            
            case UrlType.Query:
                if searchengine == 'Youtube':
                    song = await self.yt.get(queryurl)
                else:
                    song = self.sp.getSearch(queryurl)
                    await self.yt.assignDownloadUrl([song])
                return song

            case UrlType.Unknown:
                return None