from typing import Iterable
from nextcord.ext import commands
from nextcord import Colour
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from collections import deque
from functools import partial
from enum import Enum
import traceback
import nextcord
import asyncio
import random
import time
import sys

from utils.terminal import getlogger, stream as logger_stream
from utils.classes import BytesIOFFmpegPCMAudio
from utils.system import OS, ARCH
from utils.config import config
from utils.abc import Page

from .MusicUI import FinishedPlayingPage, NothingToPlayPage, NowPlayingPage

logger = getlogger()

class UrlType(Enum):
    YoutubeSong = "YoutubeSong"
    YoutubePlaylist = "YoutubePlaylist"

    SpotifySong = "SpotifySong"
    SpotifyPlaylist = "SpotifyPlaylist"
    SpotifyAlbum = "SpotifyAlbum"

    Query = "Query"
    Unknown = "Unknown"

def urltype(url : str) -> UrlType:
    """From a given url return the corresponding UrlType"""
    parsed = urlparse(url)

    if parsed.netloc == 'www.youtube.com' and parsed.path == 'watch':
        if 'list=' in parsed.params:
            return UrlType.YoutubePlaylist
        elif 'v=' in parsed.params:
            return UrlType.YoutubeSong
        else:
            return UrlType.Unknown
    elif parsed.netloc == 'open.spotify.com':
        if 'track' in parsed.path:
            return UrlType.SpotifySong
        elif 'playlist' in parsed.path:
            return UrlType.SpotifyPlaylist
        elif 'album' in parsed.path:
            return UrlType.SpotifyAlbum
        else:
            return UrlType.Unknown
    
    elif 'https' in parsed.scheme or 'http' in parsed.scheme:
        return UrlType.Unknown

    return UrlType.Query

def fromseconds(s : float):
    """convert from a given time in seconds to an hours, minutes, seconds and milliseconds format"""
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    seconds = int(s % 60)
    milliseconds = int((s % 1) * 1000)
    return (hours, minutes, seconds, milliseconds)

def fromformat(time: tuple[int, int, int, int]):
    """Convert from a given hours, minutes, seconds and milliseconds format to a seconds format."""
    return time[0] * 3600 + time[1] * 60 + time[2] + time[3] / 1000

song_content_sample = {
    'album': {
        'album_type': 'album', 
        'artists': [
            {'external_urls': { 'spotify': 'https://open.spotify.com/artist/0QJIPDAEDILuo8AIq3pMuU' }, 
            'href': 'https://api.spotify.com/v1/artists/0QJIPDAEDILuo8AIq3pMuU', 
            'id': '0QJIPDAEDILuo8AIq3pMuU', 
            'name': 'M.I.A.', 
            'type': 'artist', 
            'uri': 'spotify:artist:0QJIPDAEDILuo8AIq3pMuU'}
        ], 
        'available_markets': ['AR', 'AU', 'AT', 'BE', 'BO', 'BR', 'BG', 'CA', 'CL', 'CO', 'CR', 'CY', 'CZ', 'DK', 'DO', 'DE', 'EC', 'EE', 'SV', 'FI', 'FR', 'GR', 'GT', 'HN', 'HK', 'HU', 'IS', 'IE', 'IT', 'LV', 'LT', 'LU', 'MY', 'MT', 'MX', 'NL', 'NZ', 'NI', 'NO', 'PA', 'PY', 'PE', 'PH', 'PL', 'PT', 'SG', 'SK', 'ES', 'SE', 'CH', 'TW', 'TR', 'UY', 'US', 'GB', 'AD', 'LI', 'MC', 'ID', 'JP', 'TH', 'VN', 'RO', 'IL', 'ZA', 'PS', 'IN', 'BY', 'KZ', 'MD', 'UA', 'AL', 'BA', 'HR', 'ME', 'MK', 'RS', 'SI', 'KR', 'PK', 'LK', 'GH', 'KE', 'NG', 'TZ', 'UG', 'AG', 'AM', 'BS', 'BB', 'BZ', 'BT', 'BW', 'BF', 'CV', 'CW', 'DM', 'FJ', 'GM', 'GD', 'GW', 'GY', 'JM', 'KI', 'LS', 'LR', 'MW', 'MV', 'ML', 'MH', 'FM', 'NA', 'NR', 'NE', 'PW', 'PG', 'WS', 'ST', 'SN', 'SC', 'SL', 'SB', 'KN', 'LC', 'VC', 'SR', 'TL', 'TO', 'TT', 'TV', 'AZ', 'BN', 'BI', 'KH', 'CM', 'TD', 'KM', 'GQ', 'SZ', 'GA', 'GN', 'KG', 'LA', 'MO', 'MR', 'MN', 'NP', 'RW', 'TG', 'UZ', 'ZW', 'BJ', 'MG', 'MU', 'MZ', 'AO', 'CI', 'DJ', 'ZM', 'CD', 'CG', 'TJ', 'VE', 'XK'], 'external_urls': {'spotify': 'https://open.spotify.com/album/3dAxXNscIj0p53lBMEziYR'}, 'href': 'https://api.spotify.com/v1/albums/3dAxXNscIj0p53lBMEziYR', 'id': '3dAxXNscIj0p53lBMEziYR', 'images': [{'url': 'https://i.scdn.co/image/ab67616d0000b2733d6fa293f49903ed38fbe0de', 'width': 640, 'height': 640}, {'url': 'https://i.scdn.co/image/ab67616d00001e023d6fa293f49903ed38fbe0de', 'width': 300, 'height': 300}, {'url': 'https://i.scdn.co/image/ab67616d000048513d6fa293f49903ed38fbe0de', 'width': 64, 'height': 64}], 'name': 'Matangi', 'release_date': '2013-01-01', 'release_date_precision': 'day', 'total_tracks': 15, 'type': 'album', 'uri': 'spotify:album:3dAxXNscIj0p53lBMEziYR'}, 'artists': [{'external_urls': {'spotify': 'https://open.spotify.com/artist/0QJIPDAEDILuo8AIq3pMuU'}, 'href': 'https://api.spotify.com/v1/artists/0QJIPDAEDILuo8AIq3pMuU', 'id': '0QJIPDAEDILuo8AIq3pMuU', 'name': 'M.I.A.', 'type': 'artist', 'uri': 'spotify:artist:0QJIPDAEDILuo8AIq3pMuU'}], 'available_markets': ['AR', 'AU', 'AT', 'BE', 'BO', 'BR', 'BG', 'CA', 'CL', 'CO', 'CR', 'CY', 'CZ', 'DK', 'DO', 'DE', 'EC', 'EE', 'SV', 'FI', 'FR', 'GR', 'GT', 'HN', 'HK', 'HU', 'IS', 'IE', 'IT', 'LV', 'LT', 'LU', 'MY', 'MT', 'MX', 'NL', 'NZ', 'NI', 'NO', 'PA', 'PY', 'PE', 'PH', 'PL', 'PT', 'SG', 'SK', 'ES', 'SE', 'CH', 'TW', 'TR', 'UY', 'US', 'GB', 'AD', 'LI', 'MC', 'ID', 'JP', 'TH', 'VN', 'RO', 'IL', 'ZA', 'PS', 'IN', 'BY', 'KZ', 'MD', 'UA', 'AL', 'BA', 'HR', 'ME', 'MK', 'RS', 'SI', 'KR', 'PK', 'LK', 'GH', 'KE', 'NG', 'TZ', 'UG', 'AG', 'AM', 'BS', 'BB', 'BZ', 'BT', 'BW', 'BF', 'CV', 'CW', 'DM', 'FJ', 'GM', 'GD', 'GW', 'GY', 'JM', 'KI', 'LS', 'LR', 'MW', 'MV', 'ML', 'MH', 'FM', 'NA', 'NR', 'NE', 'PW', 'PG', 'WS', 'ST', 'SN', 'SC', 'SL', 'SB', 'KN', 'LC', 'VC', 'SR', 'TL', 'TO', 'TT', 'TV', 'AZ', 'BN', 'BI', 'KH', 'CM', 'TD', 'KM', 'GQ', 'SZ', 'GA', 'GN', 'KG', 'LA', 'MO', 'MR', 'MN', 'NP', 'RW', 'TG', 'UZ', 'ZW', 'BJ', 'MG', 'MU', 'MZ', 'AO', 'CI', 'DJ', 'ZM', 'CD', 'CG', 'TJ', 'VE', 'XK'], 
        'disc_number': 1, 
        'duration_ms': 227520, 
        'explicit': False, 
        'external_ids': {'isrc': 'USUG11200143'}, 
        'external_urls': {'spotify': 'https://open.spotify.com/track/6nzXkCBOhb2mxctNihOqbb'}, 
        'href': 'https://api.spotify.com/v1/tracks/6nzXkCBOhb2mxctNihOqbb', 
        'id': '6nzXkCBOhb2mxctNihOqbb', 
        'is_local': False, 
        'name': 'Bad Girls', 
        'popularity': 74, 
        'preview_url': None,
        'track_number': 8, 
        'type': 'track', 
        'uri': 'spotify:track:6nzXkCBOhb2mxctNihOqbb'
}

@dataclass
class Song:
    """
    Class representing a Song object

    :param: data (dict): 
        Song information from Spotify or a Third-Party source

    :param: url (str):
        Song file url from a Third-Party source (not Spotify)
    """

    raw: dict = field(default_factory=dict,repr=False)
    """Raw data obtained from Spotify or a Third-Party source"""
    url : str = field(default_factory=str,init=False, repr=False)
    """The song file url obatined from a Third-Party source (not Spotify)"""
    uri : str = field(default_factory=str,init=False, repr=False)
    """The Spotify song URI"""
    duration : float = field(default_factory=float,init=False, repr=False)
    """The song duration in seconds"""
    duration_str : str = field(default_factory=str,init=False, repr=True)
    """The song duration in seconds as a string"""
    name : str = field(default_factory=str,init=False, repr=True)
    """The song name"""
    id : str = field(default_factory=str, init=False, repr=True)
    """The Spotify song ID"""
    album_type : str = field(default_factory=str,init=False,repr=False)
    """The song album type (e.g., album, single)"""
    album_name : str = field(default_factory=str,init=False,repr=True)
    """The song album name"""
    album_url : str = field(default_factory=str,init=False,repr=False)
    """The song album URL"""
    album_img64px : str = field(default_factory=str, init=False, repr=False)
    """The song album image URL (64px)"""
    album_img300px : str = field(default_factory=str, init=False, repr=False)
    """The song album image URL (300x)"""
    album_release : str = field(default_factory=str,init=False,repr=True)
    """The song album release date"""
    artists : list[dict] = field(default_factory=list,init=False,repr=False)
    """A list of dictionary containing artist information"""
    explicit : bool = field(default_factory=bool,init=False)
    """Whether the song is explicit"""
    popularity : int = field(default_factory=int,init=False, repr=True)
    """The song's popularity on Spotify expressed as a number between 0 and 100"""
    preview_url : str = field(default_factory=str,init=False)
    """The song's preview URL if available"""

    def __post_init__(self):
        for field_info in fields(self):
            if field_info.init: continue  # Skip 'raw' and other fields that should not be initialized from raw
            setattr(self, field_info.name, self.raw.get(field_info.name))

        album = self.raw.get('album', {})
        images = album.get('images', [])

        self.album_name = album.get('name', None)
        self.album_type = album.get('album_type', None)
        self.album_url = album.get('external_urls', {}).get('spotify', None)
        self.album_img300px = str(images[0]['url']) if len(images) > 0 else None
        self.album_img64px = str(images[1]['url']) if len(images) > 0 else None
        self.album_release = album.get('release_date', None)
        
        self.duration = float(self.raw.get('duration_ms', 0))
        self.duration_str = datetime.fromtimestamp(self.duration / 1000).strftime('%M:%S')

class Playlist:
    pass

class History(deque):
    """Subclass of deque for playing history"""
    def __init__(self, *, songs : Iterable = [], maxlen : int = None):
        deque.__init__(self,songs,maxlen)

class Queue(deque):
    """Subclass of deque for a music queue with shuffle"""
    def __init__(self, *, songs : Iterable = [], maxlen : int = None):
        deque.__init__(self,songs,maxlen)

    def __add__(self, other):
        if isinstance(other, deque):
            self.extend(other)
            return self
        return NotImplemented

    def shuffle(self):
        random.shuffle(self)

    def move(self, origin : int, dest : int):
        self.insert(dest,self.__getitem__(origin))
        del self[origin]

class Session:
    """Guild music playing session"""
    def __init__(self, bot : commands.Bot, guild : nextcord.Guild, owner : nextcord.User):
        self.volume : float = float(config['music'].get('defaultvolume',100.0))
        self.history : History[Song] = History()
        self.queue : Queue[Song] = Queue()
        self.currentsong : Song
        self.totaltime = 0.0
        self.guild = guild
        self.channel : nextcord.VoiceChannel = guild.voice_client.channel
        self.owner = owner
        self.bot = bot
        self.loop = False
        self.cycle = False
        self.task : asyncio.Task | None = None
    
    async def _next(self, error : Exception, lastsong : Song, stime : float, attempts : int = 1):
        """Invoked after a song is finished. Plays the next song if there is one."""
        logger.debug(f"Song {lastsong} finished. attempts: {attempts}, start time: {stime}")

        if error: logger.error(traceback.format_exc())

        # Se il tempo di riproduzione e' minore della durata della canzone e i tentativi di riproduzione non sono finiti
        if (((ptime:=time.time() - stime + 3) < lastsong.duration) or error) and attempts < config['music']['attempts']:
            # Riproduci la canzone da dove si era interrotta
            logger.error(f"""The song \'{lastsong.name}\' was not played until the end""")
            logger.error(f"Playback time: {ptime}, Song Duration: {lastsong.duration}")
            logger.error(f"Playback attempts made: {attempts}/{config['music']['attempts']}")
            ftime = fromseconds(ptime)
        else:
            # Altrimenti toglila dalla queue
            ftime = (0,0,0,0)
            self.totaltime+=ptime
            self.history.append(lastsong)
            if len(self.queue) > 0: self.queue.popleft()

            page = FinishedPlayingPage(
                lastsong.name, 
                lastsong.popularity, 
                lastsong.duration_str,
                lastsong.album_name,
                lastsong.album_url,
                lastsong.album_img64px,
                lastsong.artists
            )

            #await self.channel.send(embed=page)"

        coro = self.play(lastsong if self.loop else None,st=ftime, attempts=attempts+1)
        self.task = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

    async def play(self, song : Song = None, *, st : tuple = (0,0,0,0), attempts : int = 1):
        self.guild.voice_client.stop() # Assicuriamo che non ci sia altro in riproduzione

        if not song and len(self.queue) > 0:
            song = self.queue[0] # Se non e' stata specificata una canzone prende la successiva nella coda
        elif not song and len(self.queue) == 0:
            page = NothingToPlayPage()
            await self.channel.send(embed=page)
            return  # Se non e' stata specificata una canzone e la coda e vuota allora non c'e' nulla da riprodurre

        source = BytesIOFFmpegPCMAudio(
            source=song.url,
            stderr=sys.stdout,
            executable=f"{config['paths']['bin'].format(os=OS,arch=ARCH)}ffmpeg",
            before_options=f'-ss {st[0]}:{st[1]}:{st[2]}.{st[3]}',
        )
        
        stime = time.time() if sum(st) == 0 else fromformat(st)

        source = nextcord.PCMVolumeTransformer(source, self.volume / 100.0)
        
        self.guild.voice_client.play(
            source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self._next(e, lastsong=song, stime=stime, attempts=attempts), 
                self.bot.loop
            )
        )

        page = NowPlayingPage(
            song.name, 
            song.popularity,
            song.duration_str,
            song.album_name,
            song.album_url,
            song.album_img64px,
            song.artists
        )

        await self.channel.send(embed=page, view=page)

        self.currentsong = song

    async def skip(self):
        self.guild.voice_client.stop()
        if len(self.queue) > 0: self.queue.popleft()
        #await self.play()

    async def replay(self):
        self.guild.voice_client.stop()

        if self.guild.voice_client.is_playing():
            coro = self.play()
        else:
            coro = self.play(self.history[-1])

        self.task = asyncio.create_task(coro)
