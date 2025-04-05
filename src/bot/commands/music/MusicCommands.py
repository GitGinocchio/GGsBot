from nextcord.ext import commands
from nextcord import Permissions, Colour, SlashOption
from typing import Literal
import traceback
import asyncio
import stat
import sys
import os

from utils.abc import Page
from utils.exceptions import GGsBotException
from utils.terminal import getlogger
from utils.config import config
from utils.commons import \
    Extensions,           \
    GLOBAL_INTEGRATION,   \
    GUILD_INTEGRATION,    \
    USER_INTEGRATION

from .MusicApi import MusicApi
from .MusicUtilities import *

logger = getlogger()

permissions = Permissions(
    use_slash_commands=True,
    connect=True,
    speak=True,
)

class MusicCommands(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.musicapi = MusicApi(bot.loop)
        self.sessions : dict[int, Session] = {}
        self.bot = bot

    @nextcord.slash_command("music","Listen music in discord voice channels", default_member_permissions=8, integration_types=GUILD_INTEGRATION)
    async def music(self, interaction : nextcord.Interaction): pass

    @music.subcommand("join","Bring the bot on your current voice channel to play music (not the same as `/tts join`)")
    async def join(self, interaction : nextcord.Interaction):
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

            await interaction.user.voice.channel.connect()
            
            self.sessions[interaction.guild.id] = Session(self.bot,interaction.guild,interaction.user)

            page = Page(
                colour=Colour.green(),
                title="Connected!",
                description=f"I have successfully joined your voice channel!"
            )
            
            await interaction.followup.send(embed=page, ephemeral=True)
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('play',"Play songs with the bot in your channel")
    async def play(self, 
            interaction : nextcord.Interaction, 
            queryurl : str = SlashOption("queryurl", "Query or URL of the song or playlist you want to play", required=True), 
            searchengine : Literal['Spotify','Youtube'] = SlashOption("searchengine", "Search engine to use for the query", choices=['Spotify','Youtube'], default='Spotify')
        ):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)

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

            session : Session = self.sessions[interaction.guild.id]

            if queryurl:
                tracks = await self.musicapi.get(queryurl, searchengine)

                if tracks:
                    if isinstance(tracks, list):
                        session.queue.extend(tracks)
                        await interaction.send(f"{interaction.user.mention} added {len(tracks)} songs to the queue. Now playing {session.queue[0].title}",ephemeral=True)
                    elif isinstance(tracks,Song):
                        await interaction.send(f"{interaction.user.mention} playing {tracks.name}",ephemeral=True)
                        session.queue.append(tracks)
                else:
                    pass # error getting song or songs (tracks = None)

            if interaction.guild.voice_client.is_playing() and not queryurl:
                await interaction.send(f"{interaction.user.mention} The bot is already playing music",ephemeral=True)
            else:
                await session.play()
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('add',"Add a song to the end of the queue")
    async def add(self, 
            interaction : nextcord.Interaction, 
            queryurl : str = SlashOption("queryurl", "Query or URL of the song or playlist you want to add", required=True), 
            searchengine : Literal['Spotify','Youtube'] = SlashOption("searchengine", "Search engine to use for the query", choices=['Spotify','Youtube'], default='Spotify')
        ):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)

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
            
            tracks = await self.musicapi.get(queryurl, searchengine)

            session : Session = self.sessions[interaction.guild.id]

            if tracks:
                if isinstance(tracks, list):
                    await interaction.send(f"{interaction.user.mention} added {len(tracks)} songs to the queue...",ephemeral=True,delete_after=5.0)
                    session.queue.extend(tracks)
                elif isinstance(tracks,Song):
                    await interaction.send(f"{interaction.user.mention} {tracks.name} added to the queue...",ephemeral=True,delete_after=5.0)
                    session.queue.append(tracks)
            else:
                pass # error getting song or songs (tracks = None)

        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('skip',"Skip the current playing song")
    async def skip(self, interaction : nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)

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
            elif not interaction.guild.voice_client.is_playing():
                raise GGsBotException(
                    title="I am not playing anything at the moment!",
                    description=f'{interaction.user.mention} I am not playing anything at the moment!',
                    suggestions="Call `/music play` command first and try again."
                )
            
            session : Session = self.sessions[interaction.guild.id]
            await session.skip()

            await interaction.send(f"{interaction.user.mention} I skipped '{session.currentsong.name}'!",ephemeral=True)
        
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('stop',"Stop the current playing session")
    async def stop(self, interaction : nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            
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
            elif not interaction.guild.voice_client.is_playing():
                raise GGsBotException(
                    title="I am not playing anything at the moment!",
                    description=f'{interaction.user.mention} I am not playing anything at the moment!',
                    suggestions="Call `/music play` command first and try again."
                )
            
            interaction.guild.voice_client.stop()

            await interaction.send(f"{interaction.user.mention} I have stopped the music.",ephemeral=True,delete_after=5)
        
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

    @music.subcommand('pause',"Pause the current playing session")
    async def pause(self, interaction : nextcord.Interaction):
        try:
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
            elif not interaction.guild.voice_client.is_playing():
                raise GGsBotException(
                    title="I am not playing anything at the moment!",
                    description=f'{interaction.user.mention} I am not playing anything at the moment!',
                    suggestions="Call `/music play` command first and try again."
                )
            
            interaction.guild.voice_client.pause()
            session : Session = self.sessions[interaction.guild.id]

        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())
        else:
            await interaction.send(f"Paused song \'{session.currentsong.name}\'",ephemeral=True,delete_after=5.0)

    @music.subcommand('resume',"Resume the current playing session")
    async def resume(self, interaction : nextcord.Interaction):
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
            elif not interaction.guild.voice_client.is_playing():
                raise GGsBotException(
                    title="I am not playing anything at the moment!",
                    description=f'{interaction.user.mention} I am not playing anything at the moment!',
                    suggestions="Call `/music play` command first and try again."
                )
            
            interaction.guild.voice_client.resume()
            session : Session = self.sessions[interaction.guild.id]

        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())
        else:
            await interaction.send(f"Resume playing \'{session.currentsong.name}\'",ephemeral=True,delete_after=5.0)

    @music.subcommand('replay',"Replay the last song played in the history")
    async def replay(self, interaction : nextcord.Interaction):
        pass

    @music.subcommand('setvolume','Set volume for the current playing session')
    async def setvolume(self, interaction : nextcord.Interaction, volume : float):
        pass

    @music.subcommand('leave',"The bot will leave your vocal channel")
    async def leave(self, interaction : nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)

            if not interaction.guild.voice_client:
                raise GGsBotException(
                    title="I am not in a voice channel!",
                    description=f'{interaction.user.mention} I am not in a voice channel!',
                    suggestions="Call `/music join` command first and try again."
                )

            interaction.guild.voice_client.stop()
            await interaction.guild.voice_client.disconnect()
            
            session : Session = self.sessions[interaction.guild.id]
            session.queue.clear()
            session.history.clear()
            if session.task: session.task.cancel()
            
            del session
            
            await interaction.send(f"{interaction.user.mention} I left the voice channel!",ephemeral=True,delete_after=5)
        
        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except Exception as e:
            logger.error(traceback.format_exc())

def setup(bot : commands.Bot):
    if not os.path.exists(ffmpeg_path:=f"{config['paths']['bin'].format(os=OS,arch=ARCH)}/ffmpeg{'.exe' if OS == 'Windows' else ''}"):
        raise FileNotFoundError(f"The extension cannot start, the ffmpeg executable at \'{ffmpeg_path}\' is missing")
    if not os.path.isfile(ffmpeg_path):
        raise FileNotFoundError(f"The extension cannot start, the ffmpeg executable at \'{ffmpeg_path}\' must be an executable")

    if not (permissions:=os.stat(ffmpeg_path).st_mode) & stat.S_IXUSR:
        os.chmod(ffmpeg_path, permissions | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    
    bot.add_cog(MusicCommands(bot))