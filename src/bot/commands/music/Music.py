from nextcord.ext import commands
from nextcord.ext.tasks import loop
from nextcord import \
    Message,         \
    Permissions,     \
    Colour,          \
    Interaction,     \
    SlashOption,     \
    VoiceClient,     \
    Client,          \
    VoiceChannel,    \
    VoiceProtocol,   \
    slash_command
from typing import Literal, cast
from wavelink import            \
    AutoPlayMode,               \
    InvalidNodeException,       \
    Playable,                   \
    Player,                     \
    Node,                       \
    NodeStatus,                 \
    Playlist,                   \
    Pool,                       \
    QueueEmpty,                 \
    Search,                     \
    NodeReadyEventPayload,      \
    PlayerUpdateEventPayload,   \
    StatsEventPayload,          \
    TrackStuckEventPayload,     \
    TrackExceptionEventPayload, \
    TrackStartEventPayload,     \
    TrackEndEventPayload,       \
    TrackSource
from datetime import datetime, timezone, timedelta
import wavelink
import traceback
import asyncio
import stat
import sys
import os

from utils.abc import Page
from utils.exceptions import GGsBotException
from utils.terminal import getlogger
from utils.system import OS, ARCH
from utils.config import config
from utils.commons import \
    Extensions,           \
    GLOBAL_INTEGRATION,   \
    GUILD_INTEGRATION,    \
    USER_INTEGRATION

from .MusicUI import      \
    NowPlayingPage,       \
    NothingToPlayPage,    \
    AddedToQueue,         \
    UserResumed,          \
    UserShuffled,         \
    UserSkipped,          \
    UserPaused,           \
    NoTracksFound,        \
    MiniPlayer

logger = getlogger()

permissions = Permissions(
    use_slash_commands=True,
    connect=True,
    speak=True,
)

class NextcordWavelinkPlayer(Player, VoiceProtocol):
    def __init__(self, client : Client, channel : VoiceChannel, nodes : list | None = None):
        Player.__init__(self, client=client, channel=channel, nodes=nodes)
        VoiceProtocol.__init__(self, client=client, channel=channel)
        self.ui : MiniPlayer | None = None

    def __repr__(self) -> str:
        return f"NextcordWavelinkPlayer(channel={self.channel})"
    
    async def disconnect(self, **kwargs):
        await Player.disconnect(self, **kwargs)
        self.cleanup()
    
    def cleanup(self):
        VoiceProtocol.cleanup(self)


class Music(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.mini_players : dict[int, MiniPlayer] = {}
        self.bot = bot

    # Events

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.wait_until_ready()
        
        try:
            logger.debug("Connecting to Lavalink nodes")
            nodes_dict : list[dict] = config['music']['lavalink'].get('nodes', [])
            nodes :list[Node] = []
            for node in nodes_dict:
                uri = uri if (uri:=node.get('uri', None)) is not None else node.get('host', None)
                port = node.get('port', None)
                id = node.get('identifier', None)
                password = node.get('password', None)
                secure = node.get('secure', False)

                node = Node(
                    uri=f"{'https' if secure else 'http'}://{uri}:{port}" if port else uri, 
                    identifier=id, 
                    password=password, 
                    retries=3
                )
                nodes.append(node)
                break

            await Pool.connect(nodes=nodes, client=self.bot, cache_capacity=100)
        except Exception as e:
            logger.error(traceback.format_exc())
        
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: NodeReadyEventPayload) -> None:
        logger.debug(f"Wavelink Node connected: {payload.node} | Resumed: {payload.resumed}")
    
    @commands.Cog.listener()
    async def on_wavelink_node_disconnected(self, payload) -> None:
        logger.debug(f"Node disconnected {payload}")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: TrackStartEventPayload):
        logger.debug(f"Track {payload.track} ({payload.original}) started in player {payload.player}")
        if not payload.player: return
        if not hasattr(payload.player, 'ui'): return

        await payload.player.channel.edit(status=f'Listening music with GGsBot')

        ui : MiniPlayer = payload.player.ui
        await ui.update_track()

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: TrackEndEventPayload):
        logger.debug(f"Track {payload.track} ({payload.original}) ended in player {payload.player} with reason {payload.reason}")
        player : NextcordWavelinkPlayer = cast(NextcordWavelinkPlayer, payload.player)

        if not player or not player.ui: return

        try:
            next_song = player.queue.get()
        except QueueEmpty as e: 
            await player.ui.update_track(finished=True)
            return
        else:
            await player.play(next_song, volume=30)

        await player.ui.update_track()

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player : NextcordWavelinkPlayer) -> None:
        logger.debug(f"player {player} is inactive")

        try:
            await player.stop()
        except Exception as e:
            logger.error(traceback.format_exc())

        try:
            await player.disconnect()
        except Exception as e:
            logger.error(traceback.format_exc())

    @commands.Cog.listener()
    async def on_wavelink_stats_update(self, payload: StatsEventPayload) -> None:
        pass
        #logger.debug(f"{payload.cpu.cores} cores, {payload.cpu.lavalink_load}% lavalink load, {payload.cpu.system_load}% system load")

    @commands.Cog.listener()
    async def on_wavelink_player_update(self, payload: PlayerUpdateEventPayload) -> None:
        #logger.debug(f"Player {payload.player} updated (ping: {payload.ping}, time: {payload.time}, position: {payload.position}, connected: {payload.connected})")
        player : NextcordWavelinkPlayer = cast(NextcordWavelinkPlayer, payload.player)
        if not player: return

        if not player.playing: return
        
        if not player.ui: 
            logger.debug(f'Player {payload.player} has no attribute ui, maybe it was not initialized yet?')
            return
        
        now = datetime.now(timezone.utc)
        
        if player.ui.last_update > now - timedelta(seconds=10):
            #logger.debug(f'Cannot update track because it was updated within the last 10 seconds.')
            return

        await player.ui.update_track()

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: TrackExceptionEventPayload) -> None:
        logger.debug(f"Track {payload.track} failed to play in player {payload.player} with error:\n{payload.exception}")

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, payload: TrackStuckEventPayload) -> None:
        logger.debug(f"Track {payload.track} is stuck for {payload.threshold}ms in player {payload.player}")

    # Playback Commands

    @slash_command("music","Listen music in discord voice channels", default_member_permissions=8, integration_types=GUILD_INTEGRATION)
    async def music(self, interaction : Interaction): pass

    @music.subcommand("join","Bring the bot on your current voice channel to play music (not the same as `/tts join`)")
    async def join(self, 
            interaction : Interaction, 
            autoplay = SlashOption(
                description="Set autoplay mode (default: enabled)", 
                default=str(AutoPlayMode.enabled.value), 
                choices={'enabled' : str(AutoPlayMode.enabled.value), 'disabled' : str(AutoPlayMode.disabled.value), 'partial' : str(AutoPlayMode.partial.value)},
            )
        ):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)

            if not interaction.user.voice:
                raise GGsBotException(
                    title="You are not in a voice channel!",
                    description=f'You have to join a voice channel first!',
                    suggestions="Join a voice channel and try again."
                )
            elif interaction.guild.voice_client:
                raise GGsBotException(
                    title="I am already in a voice channel!",
                    description=f'I am currently in a voice channel!',
                    suggestions="Call `/music leave` command first and try again."
                )
            
            player : NextcordWavelinkPlayer = await interaction.user.voice.channel.connect(cls=NextcordWavelinkPlayer)
            player.autoplay = AutoPlayMode(value=int(autoplay))
            
            await interaction.delete_original_message()

            message = await player.channel.send(content="Mini player is loading...")

            ui = MiniPlayer(player, message)
            player.ui = ui

            self.mini_players[interaction.guild.id] = ui

            await message.edit(content=None, embed=ui, view=ui)
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except InvalidNodeException as e:
            error = GGsBotException(
                title="No nodes available",
                description=str(e),
                suggestions="Try again later or contact a moderator."
            )

            await interaction.followup.send(embed=error.asEmbed(), ephemeral=True)
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('play',"Play songs with the bot in your channel")
    async def play(self, 
            interaction : Interaction, 
            queryurl : str = SlashOption("queryurl", "Query or URL of the song or playlist you want to play", required=True),
            searchengine = SlashOption(
                description="Search engine to use for the query (default: Youtube)", 
                choices={"Youtube" : str(TrackSource.YouTube.value),"Youtube Music" : str(TrackSource.YouTubeMusic.value),"Soundcloud" : str(TrackSource.SoundCloud.value), "Spotify" : "spsearch"},
                default=str(TrackSource.YouTube.value)
            ),
            shuffle : bool = SlashOption(
                description="Shuffle the queue after adding the song/s (default: false)", 
                default=False
            ),
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            if not interaction.user.voice:
                raise GGsBotException(
                    title="You are not in a voice channel!",
                    description=f'You have to join a voice channel first!',
                    suggestions="Join a voice channel and try again."
                )
            elif not interaction.guild.voice_client:
                raise GGsBotException(
                    title="I am not in a voice channel!",
                    description=f'I am not in a voice channel!',
                    suggestions="Call `/music join` command first and try again."
                )

            player = cast(NextcordWavelinkPlayer, interaction.guild.voice_client)

            tracks: Search = await Playable.search(queryurl, source=searchengine)

            if not tracks:
                page = NoTracksFound(queryurl)
                await interaction.followup.send(embed=page, ephemeral=True)
                return

            await player.queue.put_wait(tracks)
            if shuffle: player.queue.shuffle()

            if isinstance(tracks, Playlist):
                page = AddedToQueue(tracks, interaction.user)
            else:
                page = AddedToQueue(tracks[0], interaction.user)

            await interaction.delete_original_message()
            await interaction.channel.send(embed=page)

            if not player.playing:
                if player.paused: await player.pause(False)
                await player.play(player.queue.get(), volume=30)
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('add',"Add songs to the end of the queue")
    async def add(self, 
            interaction : Interaction, 
            queryurl : str = SlashOption("queryurl", "Query or URL of the song or playlist you want to add", required=True),
            searchengine = SlashOption(
                description="Search engine to use for the query (default: Youtube)", 
                choices={"Youtube" : str(TrackSource.YouTube.value),"Youtube Music" : str(TrackSource.YouTubeMusic.value),"Soundcloud" : str(TrackSource.SoundCloud.value), "Spotify" : "spsearch"},
                default=str(TrackSource.YouTube.value)
            ),
            shuffle : bool = SlashOption(
                description="Shuffle the queue after adding the song/s (default: false)", 
                default=False
            ),
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            if not interaction.user.voice:
                raise GGsBotException(
                    title="You are not in a voice channel!",
                    description=f'You have to join a voice channel first!',
                    suggestions="Join a voice channel and try again."
                )
            elif not interaction.guild.voice_client:
                raise GGsBotException(
                    title="I am not in a voice channel!",
                    description=f'I am not in a voice channel!',
                    suggestions="Call `/music join` command first and try again."
                )

            player = cast(NextcordWavelinkPlayer, interaction.guild.voice_client)
            tracks : Search = await Playable.search(queryurl, source=searchengine)
            await player.queue.put_wait(tracks)
            if shuffle: player.queue.shuffle()

            if isinstance(tracks, Playlist):
                page = AddedToQueue(tracks, interaction.user)
            else:
                page = AddedToQueue(tracks[0], interaction.user)

            await interaction.delete_original_message()
            await interaction.channel.send(embed=page)

            if not player.playing:
                if player.paused: await player.pause(False)
                next_song = player.queue.get()
                await player.play(next_song, volume=30)
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('skip',"Skip the current playing song")
    async def skip(self, 
            interaction : Interaction,
            playlist : bool = SlashOption(
                description="Whether to skip the current playing playlist if any (default: false)", 
                default=False
            ),
        ):
        try:
            await interaction.response.defer(ephemeral=True)
            
            if not interaction.user.voice:
                raise GGsBotException(
                    title="You are not in a voice channel!",
                    description=f'You have to join a voice channel first!',
                    suggestions="Join a voice channel and try again."
                )
            elif not interaction.guild.voice_client:
                raise GGsBotException(
                    title="I am not in a voice channel!",
                    description=f'I am not in a voice channel!',
                    suggestions="Call `/music join` command first and try again."
                )

            player = cast(NextcordWavelinkPlayer, interaction.guild.voice_client)

            current = player.current

            if player.paused:
                raise GGsBotException(
                    title="I am not playing anything at the moment!",
                    description=f'{interaction.user.mention} I am not playing anything at the moment!',
                    suggestions="Call `/music play` or `/music resume` command first and try again."
                )
            
            if playlist and current and current.playlist:
                for track in set(filter(lambda track: track.playlist == current.playlist, player.queue)):
                    player.queue.remove(track, None)

            await interaction.delete_original_message()
            page = UserSkipped(interaction.user, current.playlist if playlist and current.playlist else current)
            await player.channel.send(embed=page)

            await player.skip()
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('shuffle', "Shuffle the queue")
    async def shuffle(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            if not interaction.user.voice:
                raise GGsBotException(
                    title="You are not in a voice channel!",
                    description=f'You have to join a voice channel first!',
                    suggestions="Join a voice channel and try again."
                )
            elif not interaction.guild.voice_client:
                raise GGsBotException(
                    title="I am not in a voice channel!",
                    description=f'I am not in a voice channel!',
                    suggestions="Call `/music join` command first and try again."
                )

            player : Player = cast(NextcordWavelinkPlayer, interaction.guild.voice_client)
            player.queue.shuffle()

            await interaction.delete_original_message()
            await player.channel.send(embed=UserShuffled(interaction.user))
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('pause',"Pause the current playing song")
    async def pause(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            if not interaction.user.voice:
                raise GGsBotException(
                    title="You are not in a voice channel!",
                    description=f'{interaction.user.mention} You have to join a voice channel first!',
                    suggestions="Join a voice channel and try again."
                )
            
            if not interaction.guild.voice_client:
                raise GGsBotException(
                    title="I am not in a voice channel!",
                    description=f'{interaction.user.mention} I am not in a voice channel!',
                    suggestions="Call `/music join` command first and try again."
                )
            elif not interaction.guild.voice_client.is_playing():
                raise GGsBotException(
                    title="I am not playing anything at the moment!",
                    description=f'{interaction.user.mention} I am not playing anything at the moment!',
                    suggestions="Call `/music play` or `/music resume` command first and try again."
                )
            
            player : Player = cast(NextcordWavelinkPlayer, interaction.guild.voice_client)
            
            await player.pause(True)

            await interaction.delete_original_message()
            await player.channel.send(embed=UserPaused(interaction.user))
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())
    
    @music.subcommand('resume',"Resume the current playing song")
    async def resume(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            if not interaction.user.voice:
                raise GGsBotException(
                    title="You are not in a voice channel!",
                    description=f'{interaction.user.mention} You have to join a voice channel first!',
                    suggestions="Join a voice channel and try again."
                )
            elif not interaction.guild.voice_client:
                raise GGsBotException(
                    title="I am not in a voice channel!",
                    description=f'{interaction.user.mention} I am not in a voice channel!',
                    suggestions="Call `/music join` command first and try again."
                )
        
            player : Player = cast(NextcordWavelinkPlayer, interaction.guild.voice_client)
            
            if not player.paused:
                raise GGsBotException(
                    title="I am already playing something at the moment!",
                    description=f'{interaction.user.mention} I am already playing something at the moment!',
                    suggestions="Call `/music pause` command first and try again."
                )
            
            player : Player = cast(NextcordWavelinkPlayer, interaction.guild.voice_client)
            await player.pause(False)

            await interaction.delete_original_message()
            await player.channel.send(embed=UserResumed(interaction.user))
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('leave', "The bot will leave your vocal channel")
    async def leave(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            if not interaction.user.voice:
                raise GGsBotException(
                    title="You are not in a voice channel!",
                    description=f'{interaction.user.mention} You have to join a voice channel first!',
                    suggestions="Join a voice channel and try again."
                )
            elif not interaction.guild.voice_client:
                raise GGsBotException(
                    title="I am not in a voice channel!",
                    description=f'{interaction.user.mention} I am not in a voice channel!',
                    suggestions="Call `/music join` command first and try again."
                )

            player : Player = cast(NextcordWavelinkPlayer, interaction.guild.voice_client)
            await player.disconnect()

            await interaction.delete_original_message()
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    """
    # Music Set commands

    @music.subcommand("set", "Set the bot's music settings")
    async def set(self, interaction : Interaction): pass

    # Music effects commands

    @music.subcommand("effects", "Apply effects to the audio")
    async def effects(self, interaction : Interaction): pass
    """

def setup(bot : commands.Bot):
    if not os.path.exists(ffmpeg_path:=f"{config['paths']['bin'].format(os=OS,arch=ARCH)}/ffmpeg{'.exe' if OS == 'Windows' else ''}"):
        raise FileNotFoundError(f"The extension cannot start, the ffmpeg executable at \'{ffmpeg_path}\' is missing")
    if not os.path.isfile(ffmpeg_path):
        raise FileNotFoundError(f"The extension cannot start, the ffmpeg executable at \'{ffmpeg_path}\' must be an executable")

    if not (permissions:=os.stat(ffmpeg_path).st_mode) & stat.S_IXUSR:
        os.chmod(ffmpeg_path, permissions | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    
    bot.add_cog(Music(bot))