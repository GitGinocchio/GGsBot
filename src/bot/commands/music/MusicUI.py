from nextcord import Colour, Member, Message
from nextcord.ui import Button, button
from nextcord import ButtonStyle, Interaction, Emoji, PartialEmoji
from wavelink import Playlist, Search, Playable, Player
from datetime import datetime, timedelta
import traceback

from utils.abc import Page
from utils.system import getlogger
from .MusicUtils import fromseconds


logger = getlogger()

class NowPlayingPage(Page):
    def __init__(self, track : Playable):
        Page.__init__(self, timeout=0)
        self.color = Colour.green()
        self.url = track.uri
        self.title = f"**{track.title}**"
        self.set_author(name="Now Playing")
        if track.artwork: self.set_thumbnail(track.artwork)
        
        self.description = f"in `{track.album.name}`\nby *{track.author}*" if track.album.name else f'by {track.author}'
        hours, minutes, seconds, milliseconds = fromseconds(track.length / 1000)
        self.add_field(name="Duration", value=f'`{hours:02d}:{minutes:02d}:{seconds:02d}`' if hours > 0 else f'`{minutes:02d}:{seconds:02d}`', inline=False)
        if track.playlist: self.add_field(name="Playlist", value=f'`{track.playlist.name}`')

class FinishedPlayingPage(Page):
    def __init__(self, title : str, popularity : int, duration_str : str, album_name : str, album_url : str, album_img : str, artists : list[dict]):
        Page.__init__(self, timeout=0)
        self.url = album_url
        self.title = f"**{title}**"
        self.colour = Colour.green()
        self.description = f"in `{album_name}`\nby {', '.join("*" + artist['name'] + "*" for artist in artists)}"

        self.add_field(name="Duration", value=f'`{duration_str}`', inline=True)
        self.add_field(name="Popularity", value=f"`{popularity}%`", inline=True)

        self.set_thumbnail(album_img)
        self.set_author(name="Song Finished")

class NothingToPlayPage(Page):
    def __init__(self):
        Page.__init__(self, timeout=0)
        self.set_author(name="Nothing to play")
        self.description = "There is nothing in the queue to play."
        self.color = Colour.red()

class AddedToQueue(Page):
    def __init__(self, tracks : Playlist | Playable, member : Member):
        Page.__init__(self, timeout=0)
        self.color = Colour.green()
        self.title = f'**{tracks.name}**' if isinstance(tracks, Playlist) else f'**{tracks.title}**'
        self.url = tracks.url if hasattr(tracks, 'url') else tracks.uri if hasattr(tracks, 'uri') else None
        self.set_author(name="Added to queue")
        if tracks.artwork: self.set_thumbnail(tracks.artwork)

        if isinstance(tracks, Playlist):
            self.description = f'by *{tracks.author}*' if tracks.author else None

            total_duration = sum(song.length for song in tracks.tracks)
            hours, minutes, seconds, milliseconds = fromseconds(total_duration / 1000)

            self.add_field(name="Duration", value=f'`{hours:02d}:{minutes:02d}:{seconds:02d}`' if hours > 0 else f'`{minutes:02d}:{seconds:02d}`', inline=True)
            self.add_field(name="Tracks", value=f'`{num_tracks}`' if (num_tracks:=len(tracks.tracks)) < 600 else f'`{num_tracks}`\n(Not all songs are shown)', inline=True)
            self.add_field(name="Type", value=f"`{tracks.type}`", inline=True)

        elif isinstance(tracks, Playable):
            self.description = f"in `{tracks.album.name}`\nby *{tracks.author}*" if tracks.album.name else f'by {tracks.author}'
            hours, minutes, seconds, milliseconds = fromseconds(tracks.length / 1000)
            self.add_field(name="Duration", value=f'`{hours:02d}:{minutes:02d}:{seconds:02d}`' if hours > 0 else f'`{minutes:02d}:{seconds:02d}`', inline=True)
            self.add_field(name="Type", value=f"`Song`", inline=True)
        
        self.add_field(name="Added by", value=f'{member.mention}', inline=False)



class NoTracksFound(Page):
    def __init__(self, query : str):
        Page.__init__(self, timeout=0)
        self.set_author(name="No tracks found")
        self.description = f"No tracks found for query: \"{query}\""
        self.color = Colour.red()

class UserResumed(Page):
    def __init__(self, user : Member):
        Page.__init__(self, timeout=0)
        self.set_author(name="Resumed")
        self.description = f"{user.mention} resumed the current song."
        self.color = Colour.green()

class UserSkipped(Page):
    def __init__(self, user : Member, skipped : Playable | Playlist):
        Page.__init__(self, timeout=0)
        self.set_author(name="Skipped")
        if isinstance(skipped, Playable):
            self.description = f"{user.mention} skipped the current playing song `{skipped.title}`."
        else:
            self.description = f"{user.mention} skipped the current playing playlist `{skipped.name}`."
        self.color = Colour.yellow()

class UserShuffled(Page):
    def __init__(self, user : Member):
        Page.__init__(self, timeout=0)
        self.set_author(name="Shuffled")
        self.description = f"{user.mention} shuffled the queue."
        self.color = Colour.green()

class UserPaused(Page):
    def __init__(self, user : Member):
        Page.__init__(self, timeout=0)
        self.set_author(name="Paused")
        self.description = f"{user.mention} paused the current playing song."
        self.color = Colour.yellow()


#<:progress_bar_black:1358794186480156729>
#<:progrees_bar_green:1358794140028113089>
progress_bar_black = PartialEmoji(name="progress_bar_black",id=1358794186480156729)
progress_bar_green = PartialEmoji(name="progress_bar_green", id=1358794140028113089)

class MiniPlayer(Page):
    def __init__(self, player : Player, message : Message):
        Page.__init__(self, timeout=None)
        self.message = message
        self.set_author(name="Now Playing")
        self.title = "No track playing"
        self.description = "Add a track to the queue to see it here."
        self.color = Colour.green()
        self.player = player

    def _get_progress_bar(self, position: int, length: int, size: int = 10) -> str:
        progress_ratio = position / length
        filled_blocks = round(progress_ratio * size)
        empty_blocks = size - filled_blocks
        return str(progress_bar_green) * filled_blocks + str(progress_bar_black) * empty_blocks

    async def update_track(self):
        track = self.player.current

        if not track:
            self.title = "No track playing"
            self.description = "Add a track to the queue to see it here."
            return
        
        end_h, end_m, end_s, end_ms = fromseconds(track.length / 1000)
        pos_h, pos_m, pos_s, pos_ms = fromseconds(self.player.position / 1000)

        end_str = f'`{end_h:02d}:{end_m:02d}:{end_s:02d}`' if end_h > 0 else f'`{end_m:02d}:{end_s:02d}`'
        pos_str = f'`{pos_h:02d}:{pos_m:02d}:{pos_s:02d}`' if pos_h > 0 else f'`{pos_m:02d}:{pos_s:02d}`'

        self.title = f"**{track.title}**"
        self.description =  f"in `{track.album.name}`\nby *{track.author}*" if track.album.name else f'by {track.author}'
        self.description += "\n\n" + f'{pos_str}' + self._get_progress_bar(self.player.position,track.length, 15) + f'{end_str}'
        if track.artwork: self.set_thumbnail(url=track.artwork)

        await self.message.edit(embed=self, view=self)

    @button(label="Back", emoji='⏮️', row=0, style=ButtonStyle.gray)
    async def on_back(self, button : Button, interaction : Interaction):
        try:
            if not self.player.queue.history: return
            if len(self.player.queue.history) == 0: return

            next_song = self.player.queue.history.get()
            await self.player.queue.put_at(0, next_song)
            await self.player.skip()
        except Exception as e:
            logger.error(traceback.format_exc())

    @button(label="Play/Pause", emoji='⏯️', row=0, style=ButtonStyle.green)
    async def on_play(self, button : Button, interaction : Interaction):
        try:
            await self.player.pause(not self.player.paused)
        except Exception as e:
            logger.error(traceback.format_exc())

    @button(label="Next", emoji='⏭️', row=0, style=ButtonStyle.gray)
    async def on_next(self, button : Button, interaction : Interaction):
        try:
            await self.player.skip()
        except Exception as e:
            logger.error(traceback.format_exc())

    @button(label="Shuffle", emoji='🔀', row=1, style=ButtonStyle.gray)
    async def on_shuffle(self, button : Button, interaction : Interaction):
        pass