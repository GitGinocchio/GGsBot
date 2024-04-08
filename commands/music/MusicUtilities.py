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

def fromseconds(s : float):
    """convert from a given time in seconds to an hours, minutes and seconds format"""
    return (int(s//3600),int((s%3600)//60),int(s%60))

def fromformat(time : tuple[int,int,int]):
    """convert from a given hours, minutes and seconds format to a seconds format"""
    return time[0] * 3600 + time[1] * 60 + time[2]

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
    
    def _next(self, error : Exception, lastsong : Song, stime : float, attempts : int = 0):
        """Invoked after a song is finished. Plays the next song if there is one."""

        if error: logger.error(f'Discord Stream audio Error: {error}')

        # Se il tempo di riproduzione e' minore della durata della canzone e i tentativi di riproduzione sono meno di un tot
        if (ptime:=time.time() - stime < lastsong.duration or error) and attempts < config['music']['attempts']:
            # Riproduci la canzone da dove si era interrotta
            print('Non e\' stata riprodotta fino alla fine')
            ftime = fromseconds(ptime)
        else:
            # Altrimenti toglila dalla queue
            ftime = (0,0,0)
            self.history.append(lastsong)
            self.queue.popleft()
        
        coro = self.play(lastsong if self.loop else None,st=ftime, attempts=attempts+1)
        self.task = self.bot.loop.create_task(coro)

    async def play(self, song : Song = None, *, st : tuple = (0,0,0), attempts : int = 0):
        self.guild.voice_client.stop() # Assicuriamo che non ci sia altro in riproduzione

        if not song and len(self.queue) > 0:
            song = self.queue[0] # Se non e' stata specificata una canzone prende la successiva nella coda
        elif not song and len(self.queue) == 0: 
            return  # Se non e' stata specificata una canzone e la coda e vuota allora non c'e' nulla da riprodurre
        
        source = nextcord.FFmpegPCMAudio(
            source=song.url,
            executable=str(config['music']['ffmpeg_path']).format(os=OS,arch=ARCH),
            before_options=f'-ss {st[0]}:{st[1]}:{st[2]}.000'
            )
        
        stime = time.time() if sum(st) == 0 else fromformat(st)
        
        self.guild.voice_client.play(source,after=lambda e: self._next(e,lastsong=song,start_time=stime,attempts=attempts))
        
        self.guild.voice_client.source = nextcord.PCMVolumeTransformer(source)
        self.guild.voice_client.source.volume = float(self.volume) / 100.0

        self.currentsong = song

    async def skip(self):
        self.guild.voice_client.stop()
        self.queue.popleft()
        await self.play()

    async def replay(self):
        self.guild.voice_client.stop()

        if self.guild.voice_client.is_playing():
            await self.play()
        else:
            song = self.history[0]
            await self.play(song)
