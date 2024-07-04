from utils.config import config
from .MusicUtilities import *
import yt_dlp
import spotipy
import asyncio

class YoutubeExtension(yt_dlp.YoutubeDL):
    def __init__(self, *, loop : asyncio.AbstractEventLoop, params : dict):
        super().__init__(params)
        self.loop = loop
        
    async def assignDownloadUrl(self, songs : list[Song]):
        for song in songs:
            query = f"{song.name}{',' + song.album_name if song.album_type == 'album' else ''}, by {', '.join(artist['name'] for artist in song.artists)}"

            data : dict = await self.loop.run_in_executor(None, lambda: self.extract_info(f'ytsearch: {query}', download=False))
        
            if not data: continue
            if not 'entries' in data or data['_type'] != 'playlist': 
                song.url = str(data['url'])
                song.duration = float[data['duration_ms']]
            else: 
                song.url = str(data['entries'][0]['url'])
                song.duration = float(data['entries'][0]['duration'])

    async def get(self, queryurl : str):
        url_type = urltype(queryurl)

        if url_type == UrlType.YoutubeSong or url_type == UrlType.YoutubePlaylist:
            url = queryurl
        elif url_type == UrlType.Query:
            url = f'ytsearch: {queryurl}'
        else:
            raise ValueError(f'Invalid link type {type(url_type)}...')

        data = await self.loop.run_in_executor(None, lambda: self.extract_info(url, download=False))

        if not data: return None
        if not 'entries' in data or data['_type'] != 'playlist': return Song(data)
        elif 'entries' in data and len(data['entries']) == 1: return Song(data['entries'][0])

        tracks = [Song(entrie) for entrie in data['entries'] if 'url' in entrie]

        return tracks
    
class SpotifyExtension(spotipy.Spotify):
    def __init__(self,*, loop : asyncio.AbstractEventLoop, auth : dict, params : dict):
        self.auth = spotipy.SpotifyClientCredentials(**auth)
        super().__init__(client_credentials_manager=self.auth,**params)
        self.loop = loop

    def getPlaylist(self, url : str):
        assert urltype(url) == UrlType.SpotifyPlaylist, 'Invalid url type!'

        total = self.playlist(url)['tracks']['total']

        for i in range(0,(total // 100)+1,1):
            for track in self.playlist_tracks(url,offset=100*i)['items']:
                song = Song(track['track'])
                yield song

    def getAlbum(self, url : str):
        assert urltype(url) == UrlType.SpotifyAlbum, 'Invalid url type!'

        total = self.album(url)['tracks']['total']
        
        for i in range(0,(total // 50)+1,1):
            for track in self.album_tracks(url,offset=50*i)['items']:
                song = Song(track)
                yield song

    def getSearch(self, query : str):
        assert urltype(query) == UrlType.Query, 'Invalid url type!'
        return Song(self.search(query,1,type='track')['tracks']['items'][0])

    def getTrack(self, url : str) -> Song:
        assert urltype(url) == UrlType.SpotifySong, 'Invalid url type!'
        return Song(self.track(url))
