from typing import Iterable
from nextcord.ext import commands
from nextcord import Colour
from dataclasses import dataclass, field, fields
from urllib.parse import urlparse
from collections import deque
from enum import Enum
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

@dataclass
class Song:
    """
    Class representing a Song object

    :param: data (dict): 
        Song information from Spotify

    :param: url (str):
        Song file url from A Third-Party source (not Spotify)
    
    """
    data: dict = field(default_factory=dict,repr=False)
    url : str = field(default_factory=str,init=False)
    duration : float = field(default_factory=float,init=False)
    name : str = field(default_factory=str,init=False)
    album_type : str = field(default_factory=str,init=False,repr=False)
    album_name : str = field(default_factory=str,init=False,repr=False)
    album_url : str = field(default_factory=str,init=False,repr=False)
    album_release : str = field(default_factory=str,init=False,repr=False)
    artists : list = field(default_factory=list,init=False,repr=False)
    explicit : bool = field(default_factory=bool,init=False)
    popularity : int = field(default_factory=int,init=False)
    preview_url : str = field(default_factory=str,init=False)

    def __post_init__(self):
        for field_info in fields(self):
            if field_info.init: continue  # Skip 'data' and other fields that should not be initialized from raw
            setattr(self, field_info.name, self.data.get(field_info.name))

        self.album_name = self.data.get('album', {}).get('name', None)
        self.album_type = self.data.get('album', {}).get('album_type', None)
        self.album_url = self.data.get('album', {}).get('external_urls', {}).get('spotify', None)
        self.album_release = self.data.get('album', {}).get('release_date', None)

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
            queue = Queue(songs=self)
            queue.extend(other)
            return queue
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

        if error: logger.error(f'Discord Stream audio Error: {error}')

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

            page = Page(
                colour=Colour.green(),
                title=f"Finished playing {lastsong.name}",
                description=f"Finished playing {lastsong.name} by {','.join(lastsong.artists)}"
            )

            await self.channel.send(embed=page)

        coro = self.play(lastsong if self.loop else None,st=ftime, attempts=attempts+1)

        self.task = await asyncio.create_task(coro)


    async def play(self, song : Song = None, *, st : tuple = (0,0,0,0), attempts : int = 1):
        self.guild.voice_client.stop() # Assicuriamo che non ci sia altro in riproduzione

        if not song and len(self.queue) > 0:
            song = self.queue[0] # Se non e' stata specificata una canzone prende la successiva nella coda
        elif not song and len(self.queue) == 0: 
            page = Page(
                title="Nothing to play",
                description="There is nothing in the queue to play",
                colour=Colour.green()
            )
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
        
        self.guild.voice_client.play(source,after=lambda e: self.bot.loop.run_in_executor(None, self._next(e,lastsong=song,stime=stime,attempts=attempts)))

        page = Page(
            title="Now Playing",
            description=f"Now playing {song.name} by {', '.join(song.artists)}",
            colour=Colour.green()
        )

        await self.channel.send(embed=page)

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

        self.task = await asyncio.create_task(coro)
