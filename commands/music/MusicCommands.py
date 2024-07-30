from .MusicApi import MusicApi
from .MusicUtilities import *
from utils.terminal import getlogger
from nextcord.ext import commands
from nextcord import Permissions
from utils.config import config
from typing import Literal
import nextcord
import asyncio
import stat
import sys
import os

logger = getlogger()

permissions = Permissions(
    use_slash_commands=True,
    connect=True,
    speak=True,
)

class MusicCommands(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.musicapi = MusicApi(bot.loop)
        self.sessions = {}
        self.bot = bot
        #2147483648

    @nextcord.slash_command("music","Listen music in discord voice channels", default_member_permissions=8,dm_permissions=False)
    async def music(self, interaction : nextcord.Interaction): pass

    @music.subcommand("join","Bring the bot on your current voice channel")
    async def join(self, interaction : nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            assert interaction.user.voice, f'{interaction.user.mention} You have to join a voice channel first!'
            assert not interaction.guild.voice_client, f'{interaction.user.mention} I am currently in a voice channel!'

            await interaction.user.voice.channel.connect()
            self.sessions[interaction.guild.id] = Session(self.bot,interaction.guild,interaction.user)
            await interaction.send(f"{interaction.user.mention} I have joined your voice channel!", ephemeral=True, delete_after=5.0)
        except AssertionError as e:
            await interaction.send(str(e),ephemeral=True,delete_after=5.0)
        except Exception as e:
            logger.error(e)

    @music.subcommand('play',"Play songs with the bot in your channel")
    async def play(self, interaction : nextcord.Interaction, queryurl : str = None, searchengine : Literal['Spotify','Youtube'] = 'Spotify'):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            assert interaction.user.voice.channel, f'{interaction.user.mention} You have to join a voice channel first!'
            assert interaction.guild.voice_client, f'{interaction.user.mention} You have to call */join* command first!'

            session : Session = self.sessions[interaction.guild.id]

            if queryurl:
                tracks = await self.musicapi.get(queryurl, searchengine)

                if tracks:
                    if isinstance(tracks, list):
                        session.queue.extend(tracks)
                        await interaction.send(f"{interaction.user.mention} added {len(tracks)} songs to the queue. Now playing {session.queue[0].title}",ephemeral=True,delete_after=5.0)
                    elif isinstance(tracks,Song):
                        await interaction.send(f"{interaction.user.mention} playing {tracks.name}",ephemeral=True,delete_after=5.0)
                        session.queue.append(tracks)
                else:
                    pass # error getting song or songs (tracks = None)

            if interaction.guild.voice_client.is_playing() and not queryurl:
                await interaction.send(f"{interaction.user.mention} The bot is already playing music",ephemeral=True,delete_after=5.0)
            else:
                await session.play()
        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)

    @music.subcommand('add',"Add a song to the end of the queue")
    async def add(self, interaction : nextcord.Interaction, queryurl : str):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            assert interaction.user.voice.channel, f'{interaction.user.mention} You have to join a voice channel first!'
            assert interaction.guild.voice_client, f'{interaction.user.mention} You have to call */join* command first!'

            tracks = await self.yt.get_info(queryurl)

            session : Session = self.sessions[interaction.guild.id]

            if tracks:
                if isinstance(tracks, list):
                    await interaction.send(f"{interaction.user.mention} added {len(tracks)} songs to the queue...",ephemeral=True,delete_after=5.0)
                    session.queue.extend(tracks)
                elif isinstance(tracks,Song):
                    await interaction.send(f"{interaction.user.mention} {tracks.title} added to the queue...",ephemeral=True,delete_after=5.0)
                    session.queue.append(tracks)
            else:
                pass # error getting song or songs (tracks = None)

        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except nextcord.errors.ClientException as e:
            logger.fatal(e)

    @music.subcommand('skip',"Skip the current playing song")
    async def skip(self, interaction : nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            assert interaction.user.voice.channel, f'{interaction.user.mention} You have to join a voice channel first!'
            assert interaction.guild.voice_client, f'{interaction.user.mention} I am not in a vocal channel!'
            assert interaction.guild.voice_client.is_playing(), f'{interaction.user.mention} I am not playing anything at the moment!'
            
            session : Session = self.sessions[interaction.guild.id]
            await session.skip()

            await interaction.send(f"{interaction.user.mention} I skipped '{session.currentsong.name}'!",ephemeral=True,delete_after=5)
        
        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except nextcord.errors.ClientException as e:
            logger.fatal(e)

    @music.subcommand('stop',"Stop the current playing session")
    async def stop(self, interaction : nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            assert interaction.guild.voice_client, f'{interaction.user.mention} I am not in a vocal channel!'
            assert interaction.guild.voice_client.is_playing(), f'{interaction.user.mention} I am not playing anything at the moment!'
            
            interaction.guild.voice_client.stop()

            await interaction.send(f"{interaction.user.mention} I !",ephemeral=True,delete_after=5)
        
        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except nextcord.errors.ClientException as e:
            logger.fatal(e)

    @music.subcommand('pause',"Pause the current playing session")
    async def pause(self, interaction : nextcord.Interaction):
        try:
            assert interaction.guild.voice_client, f'{interaction.user.mention} I am not in a vocal channel!'
            assert interaction.guild.voice_client.is_playing(), f'{interaction.user.mention} I am not playing anything at the moment!'

            interaction.guild.voice_client.pause()
            session : Session = self.sessions[interaction.guild.id]

        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except Exception as e:
            logger.error(e)
        else:
            await interaction.send(f"Paused song \'{session.currentsong.name}\'",ephemeral=True,delete_after=5.0)

    @music.subcommand('resume',"Resume the current playing session")
    async def resume(self, interaction : nextcord.Interaction):
        try:
            assert interaction.guild.voice_client, f'{interaction.user.mention} I am not in a vocal channel!'
            assert interaction.guild.voice_client.is_paused(), f'{interaction.user.mention} I do not have a paused song at the moment!'

            interaction.guild.voice_client.resume()
            session : Session = self.sessions[interaction.guild.id]

        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except Exception as e:
            logger.error(e)
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
            assert interaction.guild.voice_client, f'{interaction.user.mention} I am not in a vocal channel!'

            interaction.guild.voice_client.stop()
            await interaction.guild.voice_client.disconnect()
            
            session : Session = self.sessions[interaction.guild.id]
            session.queue.clear()
            session.history.clear()
            if session.task: session.task.cancel()
            
            del session
            
            await interaction.send(f"{interaction.user.mention} I left the voice channel!",ephemeral=True,delete_after=5)
        
        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except nextcord.errors.ClientException as e:
            logger.fatal(e)

def setup(bot : commands.Bot):
    try:
        assert os.path.exists(ffmpeg_path:=f"{config['music']['ffmpeg_path'].format(os=OS,arch=ARCH)}{'.exe' if OS == 'Windows' else ''}"), f"The extension cannot start, the ffmpeg executable at \'{ffmpeg_path}\' is missing"
        assert os.path.isfile(ffmpeg_path), f"The extension cannot start, the ffmpeg executable at \'{ffmpeg_path}\' must be an executable"
        if not (permissions:=os.stat(ffmpeg_path).st_mode) & stat.S_IXUSR:
            os.chmod(ffmpeg_path, permissions | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    except Exception as e:
        logger.critical(e)
    else:
        bot.add_cog(MusicCommands(bot))