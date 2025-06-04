from typing import Any, Callable, Coroutine
from nextcord import Colour, HTTPException, Member, Message
from nextcord.ui import Button, button, Modal, TextInput, Select
from nextcord import ButtonStyle, Interaction, Emoji, PartialEmoji, TextInputStyle
from wavelink import LavalinkLoadException, Playlist, Search, Playable, Player, TrackSource, QueueMode, AutoPlayMode
from datetime import datetime, timedelta, timezone
import traceback
import asyncio

from utils.abc import Page
from utils.exceptions import GGsBotException
from utils.system import getlogger
from utils.emojis import *
from .MusicUtils import fromseconds, isurl


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

class AddModal(Modal):
    def __init__(self, on_query_callback : Coroutine[Any, Any, None]):
        Modal.__init__(self, "Add a track to the queue")
        self.on_query_callback = on_query_callback

        self.query = TextInput(
            label="Add tracks, playlists and albums to the queue",
            placeholder="Name and URls are allowed",
            style=TextInputStyle.short,
            required=True
        )

        self.searchengine = TextInput(
            label="Search engine for queries",
            placeholder="YouTube, YouTubeMusic, SoundCloud or Spotify",
            style=TextInputStyle.short,
            default_value="Spotify",
            required=True,
            row=1
        )

        self.query.callback = self.callback

        self.add_item(self.query)
        self.add_item(self.searchengine)

    async def callback(self, interaction: Interaction):
        try:
            asyncio.create_task(self.on_query_callback(interaction, self.query.value.strip(), self.searchengine.value.strip()))
        except Exception as e:
            logger.error(traceback.format_exc())

class MiniPlayer(Page):
    def __init__(self, player : Player, message : Message):
        Page.__init__(self, timeout=None)
        self.message = message
        self.set_author(name="Now Playing")
        self.title = "No track playing"
        self.description = "Add a track to the queue to see it here."
        self.color = Colour.green()
        self.player = player
        self.last_update : datetime = datetime.now(timezone.utc)

        self.last_shuffle : datetime = None

        # First row

        self.shuffle_button = Button(style=ButtonStyle.grey, label="Shuffle", emoji=shuffle, row=0, disabled=True)
        self.shuffle_button.callback = self.on_shuffle

        self.repeat_button = Button(style=ButtonStyle.grey, label="Loop [off]", emoji=repeat, row=0, disabled=True)
        self.repeat_button.callback = self.on_repeat

        self.autoqueue_button = Button(style=ButtonStyle.grey, label="Autoqueue [disabled]", emoji=autoqueue_disabled, row=0, disabled=True)
        self.autoqueue_button.callback = self.on_autoqueue

        # Second row

        self.add_button = Button(style=ButtonStyle.grey, label="Add", emoji=queue_add, row=1, disabled=False)
        self.add_button.callback = self.on_add

        # Third row

        self.back_button = Button(style=ButtonStyle.grey, label="Back", emoji=skip_back, row=2, disabled=True)
        self.back_button.callback = self.on_back
        
        self.playpause_button = Button(style=ButtonStyle.grey, label="Play", emoji=play, row=2, disabled=True)
        self.playpause_button.callback = self.on_play
        
        self.next_button = Button(style=ButtonStyle.grey, label="Next", emoji=skip_forward, row=2, disabled=True)
        self.next_button.callback = self.on_next

        self.add_item(self.shuffle_button)
        self.add_item(self.repeat_button)
        self.add_item(self.autoqueue_button)

        self.add_item(self.add_button)

        self.add_item(self.back_button)
        self.add_item(self.playpause_button)
        self.add_item(self.next_button)

    def _get_progress_bar(self, position: int, length: int, size: int = 10) -> str:
        progress_ratio = position / length
        filled_blocks = round(progress_ratio * size)
        empty_blocks = size - filled_blocks
        return str(progress_bar_green) * filled_blocks + str(progress_bar_black) * empty_blocks

    async def update_track(self, finished : bool = False):
        try:
            now = datetime.now(timezone.utc)
            
            #if self.last_update > now - timedelta(seconds=10):
                #logger.debug(f'Cannot update track because it was updated within the last 10 seconds.')
                #return

            self.last_update = datetime.now(timezone.utc)

            track = self.player.current

            self.back_button.disabled = not track
            self.playpause_button.disabled = not track
            self.next_button.disabled = not track
            self.repeat_button.disabled = not track
            self.autoqueue_button.disabled = not track

            if (self.last_shuffle and self.last_shuffle < now - timedelta(minutes=1)) or not self.last_shuffle:
                self.shuffle_button.disabled = not track
            
            self.playpause_button.label = "Pause" if track and self.player.playing else "Play"
            self.playpause_button.emoji = pause if track and self.player.playing else play

            if not track or finished:
                self.url = None
                self.title = "No track playing"
                self.description = "Add a track to the queue to see it here."
                self.set_thumbnail(None)
                await self.message.edit(embed=self, view=self)
                return
            
            end_h, end_m, end_s, end_ms = fromseconds(track.length / 1000)
            pos_h, pos_m, pos_s, pos_ms = fromseconds(self.player.position / 1000)

            end_str = f'`{end_h:02d}:{end_m:02d}:{end_s:02d}`' if end_h > 0 else f'`{end_m:02d}:{end_s:02d}`'
            pos_str = f'`{pos_h:02d}:{pos_m:02d}:{pos_s:02d}`' if pos_h > 0 else f'`{pos_m:02d}:{pos_s:02d}`'

            self.url = track.uri
            self.title = f"**{track.title}**"
            self.description =  f"in `{track.album.name}`\nby *{track.author}*" if track.album.name else f'by {track.author}'
            self.description += "\n\n" + f'{pos_str}' + self._get_progress_bar(self.player.position,track.length, 15) + f'{end_str}'

            track_string = lambda track: f'1. [**{track.title if len(track.title) < 40 else track.title[:37] + '...'}**]({track.uri}) by *{track.author}*'

            self.description += f"\n### Queue ({len(self.player.queue)} tracks):\n"
            self.description += '\n'.join([track_string(track) for track in self.player.queue[0:5]]) \
                                if len(self.player.queue) > 0 \
                                else '-# There are no other tracks in the queue'
            self.description += f"\n### History ({max(len(self.player.queue.history) - 1, 0)} tracks):\n"
            self.description += '\n'.join([track_string(track) for track in self.player.queue.history[-2:-7:-1]]) \
                                if len(self.player.queue.history) - 1 > 0 \
                                else '-# There are no tracks in the history'
            
            if track.artwork: self.set_thumbnail(url=track.artwork)

            await self.message.edit(embed=self, view=self)
        except HTTPException as e:
            if e.code == 30046:
                await self.message.delete()
                self.message = await self.message.channel.send(embed=self, view=self)
        except Exception as e:
            logger.error(traceback.format_exc())

    async def on_query(self, interaction : Interaction, query : str, searchengine : str):
        try:
            if searchengine in ['Youtube', 'YouTubeMusic', 'SoundCloud']:
                searchengine = TrackSource[searchengine]
            elif searchengine == "Spotify":
                searchengine = "spsearch:"
            else:
                error = GGsBotException(
                    title="Invalid Search Engine",
                    description=f"{searchengine} is not a valid search engine.",
                    suggestions=f"Please use one of the following: {','.join(source.name for source in TrackSource) + ',Spotify'}"
                )

                await interaction.followup.send(embed=error.asEmbed(), ephemeral=True)
                return

            tracks : Playlist | list[Playable] = await Playable.search(query, source=searchengine)

            if isinstance(tracks, list) and len(tracks) == 0:
                await interaction.followup.send(embed=NoTracksFound(query), delete_after=5, ephemeral=True)
                return
            elif isinstance(tracks, list):
                for track in tracks:
                    track.extras = { 'requestor_id' : interaction.user.id }
            elif isinstance(tracks, Playable):
                tracks.extras = { 'requestor_id' : interaction.user.id }

            await self.player.queue.put_wait(tracks)

            if not self.player.playing:
                await self.player.pause(False)
                next_song = self.player.queue.get()
                await self.player.play(next_song, volume=30)

            if isinstance(tracks, Playlist):
                embed = AddedToQueue(tracks, interaction.user)
            else:
                embed = AddedToQueue(tracks[0], interaction.user)

            await interaction.followup.send(embed=embed, delete_after=5, ephemeral=True)
        except LavalinkLoadException as e:
            await interaction.followup.send(embed=GGsBotException.formatException(e).asEmbed(), ephemeral=True)
        except Exception as e:
            logger.error(traceback.format_exc())

    # First row

    async def on_add(self, interaction : Interaction):
        try:
            modal = AddModal(self.on_query)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(traceback.format_exc())

    # Second row

    async def on_shuffle(self, interaction : Interaction):
        try:
            self.player.queue.shuffle()

            self.shuffle_button.disabled = True
            self.last_shuffle = datetime.now(timezone.utc)

            await self.message.edit(embed=self, view=self)

            page = UserShuffled(interaction.user)

            await interaction.response.send_message(embed=page, view=page, ephemeral=True, delete_after=5)
        except Exception as e:
            logger.error(traceback.format_exc())

    async def on_repeat(self, interaction : Interaction):
        try:
            if self.player.queue.mode == QueueMode.normal:
                self.player.queue.mode = QueueMode.loop
                self.repeat_button.emoji = infinity
                self.repeat_button.label = "Loop [song]"
            elif self.player.queue.mode == QueueMode.loop:
                self.player.queue.mode = QueueMode.loop_all
                self.repeat_button.emoji = repeat_enabled
                self.repeat_button.label = "Loop [queue]"
            else:
                self.player.queue.mode = QueueMode.normal
                self.repeat_button.emoji = repeat
                self.repeat_button.label = "Loop [off]"

            await self.message.edit(embed=self, view=self)
        except Exception as e:
            logger.error(traceback.format_exc())

    async def on_autoqueue(self, interaction : Interaction):
        try:
            if self.player.autoplay == AutoPlayMode.disabled:
                self.player.autoplay = AutoPlayMode.enabled
                self.autoqueue_button.emoji = autoqueue
                self.autoqueue_button.label = "Autoqueue [enabled]"
            elif self.player.autoplay == AutoPlayMode.enabled:
                self.player.autoplay = AutoPlayMode.disabled
                self.autoqueue_button.emoji = autoqueue_disabled
                self.autoqueue_button.label = "Autoqueue [disabled]"

            await self.message.edit(embed=self, view=self)
        except Exception as e:
            logger.error(traceback.format_exc())

    # Third row

    async def on_back(self, interaction : Interaction):
        try:
            if not self.player.queue.history: return
            if (len_history:=len(self.player.queue.history)) == 0: return

            next_song = self.player.queue.history.get_at(-2 if len_history >= 2 else -1)
            self.player.queue.put_at(0, next_song)
            if self.player.current: self.player.queue.put_at(1, self.player.current)
            await self.player.skip()
        except Exception as e:
            logger.error(traceback.format_exc())

    async def on_play(self, interaction : Interaction):
        try:
            if self.playpause_button.label == "Play":
               self.playpause_button.label = "Pause"
               self.playpause_button.emoji = pause
            else:
                self.playpause_button.label = "Play"
                self.playpause_button.emoji = play

            await self.player.pause(not self.player.paused)
            await self.message.edit(embed=self, view=self)
        except Exception as e:
            logger.error(traceback.format_exc())

    async def on_next(self, interaction : Interaction):
        try:
            await self.player.skip()
        except Exception as e:
            logger.error(traceback.format_exc())
