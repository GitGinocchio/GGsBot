from typing import Iterable, Callable
from nextcord.ext import commands
from utils.system import OS, ARCH
from utils.config import config
from utils.terminal import getlogger
from collections import deque
from enum import Enum
import subprocess
import nextcord
import tempfile
import asyncio
import random
import sys

logger = getlogger()

class LinkType(Enum):
    SpotifyLink = "Spotify"
    YoutubeLink = "Youtube"
    
    SpotifyPlaylistLink = "Spotify Playlist"
    YoutubePlaylistLink = "Youtube Playlist"

    UnknownLink = "Unknown"

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

class Song:
    def __init__(self, rawinfo : dict):
        self.webpage_url = rawinfo['webpage_url']
        self.channel_url = rawinfo['channel_id']
        self.thumbnail = rawinfo['thumbnail']
        self.duration = rawinfo['duration']
        self.uploader = rawinfo['uploader']
        self.channel = rawinfo['channel']
        self.title = rawinfo['title']
        self.url = rawinfo['url']
        self._raw = rawinfo

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

class SpooledTemporaryFileWithCallback(tempfile.SpooledTemporaryFile):
    def __init__(self, max_size=0, mode='w+b', suffix='', prefix='tmp', dir=None, callback:Callable=None):
        super().__init__(max_size=max_size, mode=mode, suffix=suffix, prefix=prefix, dir=dir)
        self.callback = callback

    def write(self, data):
        print('scrivendo: ', data)
        super().write(data)
        if self.callback:
            self.callback(data)

    def writelines(self, iterable : Iterable):
        super().writelines(iterable)
        print('scrivendo: ', ''.join(iterable))
        
        if self.callback:
            self.callback(iterable)

class Session:
    def __init__(self, bot : commands.Bot, guild : nextcord.Guild, owner : nextcord.User):
        self.tempfile = SpooledTemporaryFileWithCallback(1024,prefix="ffmpeg-stderr-",suffix='.log',callback=self._on_ffmpeg_error)
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
    
    def _next(self, error : Exception, lastsong : Song, interaction : nextcord.Interaction):
        """Invoked after a song is finished. Plays the next song if there is one."""

        if error: logger.error(f'Discord Stream audio Error: {error}')

        if len(self.queue) > 0:
            coro = self.playsong(interaction,lastsong if self.loop else None)
            self.task = self.bot.loop.create_task(coro)

    def _on_ffmpeg_error(self, data):
        print(data)

    async def playsong(self, interaction : nextcord.Interaction, song : Song = None):
        self.guild.voice_client.stop()

        if not song and len(self.queue) > 0:
            song : Song = self.queue[0]
        elif not song and len(self.queue) == 0:
            return
        
        with SpooledTemporaryFileWithCallback(1024,prefix="ffmpeg-stderr-",suffix='.log',callback=self._on_ffmpeg_error) as tempfile:
            source = nextcord.FFmpegOpusAudio(song.url,executable=str(config['music']['ffmpeg_path']).format(os=OS,arch=ARCH),stderr=tempfile)
            
        self.guild.voice_client.play(source,after=lambda e: self._next(e,lastsong=song,interaction=interaction))

        self.guild.voice_client.source.volume = float(self.volume) / 100.0

        await interaction.channel.send(f"{self.owner.mention} playing {song.title}...",delete_after=5.0)

        self.currentsong = song
        self.history.append(song)
        self.queue.popleft()

    async def playsong_at(self): pass

    async def skip(self, interaction : nextcord.Interaction):
        self.guild.voice_client.stop()
        self.queue.popleft()
        await self.playsong(interaction)
