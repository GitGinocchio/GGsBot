from nextcord import Colour, Member
from nextcord.ui import Button, button
from nextcord import ButtonStyle, Interaction
from wavelink import Playlist, Search, Playable
from datetime import datetime, timedelta

from utils.abc import Page
from .MusicUtils import fromseconds

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



class MiniPlayer(Page):
    def __init__(self):
        Page.__init__(self, timeout=None)

    @button(label="Play/Pause", emoji=":play_pause:", style=ButtonStyle.primary)
    async def on_play(self, button : Button, interaction : Interaction):
        pass

    @button(label="Back", emoji=":track_previous:", style=ButtonStyle.primary)
    async def on_back(self, button : Button, interaction : Interaction):
        pass

    @button(label="Next", emoji=":track_next:", style=ButtonStyle.primary)
    async def on_back(self, button : Button, interaction : Interaction):
        pass