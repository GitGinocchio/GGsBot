from typing import Iterable, Callable, TextIO, BinaryIO
from nextcord.ext import commands
from utils.system import OS, ARCH
from utils.config import config
from utils.terminal import getlogger
from collections import deque
from enum import Enum
import nextcord
import random
import time
import sys
import io

logger = getlogger()

class LinkType(Enum):
    SpotifyLink = "Spotify"
    YoutubeLink = "Youtube"
    
    SpotifyPlaylistLink = "Spotify Playlist"
    YoutubePlaylistLink = "Youtube Playlist"

    UnknownLink = "Unknown"

class Song:
    def __init__(self, rawinfo : dict):
        self.webpage_url : str = rawinfo['webpage_url']
        self.channel_url : str = rawinfo['channel_id']
        self.thumbnail : str = rawinfo['thumbnail']
        self.duration : float = rawinfo['duration']
        self.uploader : str = rawinfo['uploader']
        self.channel : str= rawinfo['channel']
        self.title : str = rawinfo['title']
        self.url : str = rawinfo['url']
        self._raw : dict = rawinfo

class History(deque):
    def __init__(self, *, songs : Iterable = [], maxlen : int = None):
        deque.__init__(self,songs,maxlen)

class Queue(deque):
    def __init__(self, *, songs : Iterable = [], maxlen : int = None):
        deque.__init__(self,songs,maxlen)

    def shuffle(self):
        random.shuffle(self)

    def move(self, origin : int, dest : int):
        self.insert(dest,self.__getitem__(origin))
        del self[origin]

class Session:
    def __init__(self, bot : commands.Bot, guild : nextcord.Guild, owner : nextcord.User):
        self.volume : float = float(config['music'].get('defaultvolume',100.0))
        self.history : History[Song] = History()
        self.queue : Queue[Song] = Queue()
        self.currentsong : Song
        self.guild = guild
        self.owner = owner
        self.bot = bot
        self.loop = False
        self.cycle = False
        self.task = None
    
    def _next(self, error : Exception, lastsong : Song, start_time : float = time.time()):
        """Invoked after a song is finished. Plays the next song if there is one."""

        if error: logger.error(f'Discord Stream audio Error: {error}')

        h,m,s = 0,0,0
        if (ptime:=time.time() - start_time) >= lastsong.duration:
            self.history.append(lastsong)
            self.queue.popleft()
        else:
            h,m,s = convert_seconds(ptime)
            print('Non e\' stata riprodotta fino alla fine!')
        
        coro = self.playsong(lastsong if self.loop else None,h=h,m=m,s=s)
        self.task = self.bot.loop.create_task(coro)

    async def playsong(self, song : Song = None, *, h : int = 0, m : int = 0, s : int = 0):
        self.guild.voice_client.stop()

        if not song and len(self.queue) > 0:
            song = self.queue[0]
        elif not song and len(self.queue) == 0:
            return

        source = nextcord.FFmpegPCMAudio(
            source=song.url,
            executable=str(config['music']['ffmpeg_path']).format(os=OS,arch=ARCH),
            before_options=f'-ss {h}:{m}:{s}.000'
            )
        
        start_time = time.time() if sum([h,m,s]) == 0 else convert_time(h,m,s)
        self.guild.voice_client.play(source,after=lambda e: self._next(e,lastsong=song,start_time=start_time))
        self.guild.voice_client.source = nextcord.PCMVolumeTransformer(source)
        self.guild.voice_client.source.volume = float(self.volume) / 100.0

        self.currentsong = song

    async def playsong_at(self): pass

    async def skip(self, interaction : nextcord.Interaction):
        self.guild.voice_client.stop()
        self.queue.popleft()
        await self.playsong(interaction)

def get_url_type(url : str) -> LinkType:

    if "https://www.youtu" in url or "https://youtu.be" in url:
        return LinkType.YoutubeLink
    elif ("https://www.youtu" in url or "https://youtu.be" in url) and "&list=":
        return LinkType.YoutubePlaylistLink

    elif "https://open.spotify.com/track" in url:
        return LinkType.SpotifyLink
    elif "https://open.spotify.com/playlist" in url or "https://open.spotify.com/album" in url:
        return LinkType.SpotifyPlaylistLink

    return LinkType.UnknownLink

def convert_seconds(s : float):
    """convert from a given time in seconds to an hours, minutes and seconds format"""
    return s // 3600, (s % 3600) // 60, s % 60

def convert_time(h : float, m : float, s : float):
    """convert from a given hours, minutes and seconds format to a seconds format"""
    return h * 3600 + m * 60 + s