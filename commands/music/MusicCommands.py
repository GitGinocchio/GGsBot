from .YoutubeExtension import YoutubeExtension
from .SpotifyExtension import SpotifyExtension
from .MusicUtilities import *
from utils.terminal import getlogger
from nextcord.ext import commands
from utils.config import config
import nextcord
import asyncio
import sys

logger = getlogger()

class MusicCommands(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.yt = YoutubeExtension(loop=bot.loop,params=config['music']['youtube']['ytdl_params'])
        self.sp = SpotifyExtension()
        self.sessions = {}
        self.bot = bot
        #2147483648
    
    @nextcord.slash_command("music_join","Bring the bot on your current voice channel",default_member_permissions=8,dm_permission=False)
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

    @nextcord.slash_command('music_play',"Play songs with the bot in your channel",default_member_permissions=8,dm_permission=False)
    async def play(self, interaction : nextcord.Interaction, queryorurl : str = None):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            assert interaction.user.voice.channel, f'{interaction.user.mention} You have to join a voice channel first!'
            assert interaction.guild.voice_client, f'{interaction.user.mention} You have to call */join* command first!'

            session : Session = self.sessions[interaction.guild.id]

            if queryorurl:
                with self.yt as ytdl:
                    tracks = await ytdl.get_info(queryorurl)
                
                if tracks:
                    if isinstance(tracks, list):
                        await interaction.send(f"{interaction.user.mention} added {len(tracks)} songs to the queue...",ephemeral=True,delete_after=5.0)
                        session.queue.extend(tracks)
                    elif isinstance(tracks,Song):
                        await interaction.send(f"{interaction.user.mention} {tracks.title} added to the queue...",ephemeral=True,delete_after=5.0)
                        session.queue.append(tracks)
                else:
                    pass # error getting song or songs (tracks = None)

            if interaction.guild.voice_client.is_playing() and not queryorurl:
                await interaction.send(f"{interaction.user.mention} The bot is already playing music...",ephemeral=True,delete_after=5.0)
            else:
                await session.playsong(interaction)
    
        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except nextcord.errors.ClientException as e:
            logger.error(e)

    @nextcord.slash_command('music_add',"Add a song to the end of the queue",default_member_permissions=8,dm_permission=False)
    async def add(self, interaction : nextcord.Interaction, queryorurl : str):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            assert interaction.user.voice.channel, f'{interaction.user.mention} You have to join a voice channel first!'
            assert interaction.guild.voice_client, f'{interaction.user.mention} You have to call */join* command first!'

            tracks = await self.yt.get_info(queryorurl)

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

    @nextcord.slash_command('music_skip',"Skip the current playing song",default_member_permissions=8,dm_permission=False)
    async def skip(self, interaction : nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            assert interaction.user.voice.channel, f'{interaction.user.mention} You have to join a voice channel first!'
            assert interaction.guild.voice_client, f'{interaction.user.mention} I am not in a vocal channel!'
            assert interaction.guild.voice_client.is_playing(), f'{interaction.user.mention} I am not playing anything at the moment!'
            
            session : Session = self.sessions[interaction.guild.id]
            await session.skip(interaction)

            await interaction.send(f"{interaction.user.mention} I !",ephemeral=True,delete_after=5)
        
        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except nextcord.errors.ClientException as e:
            logger.fatal(e)

    @nextcord.slash_command('music_stop',"Stop the current playing session",default_member_permissions=8,dm_permission=False)
    async def stop(self, interaction : nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            assert interaction.guild.voice_client, f'{interaction.user.mention} I am not in a vocal channel!'
            assert interaction.guild.voice_client.is_playing(), f'{interaction.user.mention} I am not playing anything at the moment!'
            
            await interaction.guild.voice_client.stop()
                
            session : Session = self.sessions[interaction.guild.id]
            session.queue.popleft()

            await interaction.send(f"{interaction.user.mention} I !",ephemeral=True,delete_after=5)
        
        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except nextcord.errors.ClientException as e:
            logger.fatal(e)

    @nextcord.slash_command('music_pause',"Pause the current playing session",default_member_permissions=8,dm_permission=False)
    async def pause(self, interaction : nextcord.Interaction):
        try:
            assert interaction.guild.voice_client, f'{interaction.user.mention} I am not in a vocal channel!'
            assert interaction.guild.voice_client.is_playing(), f'{interaction.user.mention} I am not playing anything at the moment!'

            interaction.guild.voice_client.pause()

        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except Exception as e:
            logger.error(e)

    @nextcord.slash_command('music_resume',"Resume the current playing session",default_member_permissions=8,dm_permission=False)
    async def resume(self, interaction : nextcord.Interaction):
        try:
            assert interaction.guild.voice_client, f'{interaction.user.mention} I am not in a vocal channel!'
            assert interaction.guild.voice_client.is_paused(), f'{interaction.user.mention} I do not have a paused song at the moment!'

            interaction.guild.voice_client.resume()

        except AssertionError as e:
            await interaction.send(e,ephemeral=True,delete_after=5.0)
        except Exception as e:
            logger.error(e)

    @nextcord.slash_command('music_leave',"The bot will leave your vocal channel",default_member_permissions=8,dm_permission=False)
    async def leave(self, interaction : nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True,with_message=True)
            assert interaction.guild.voice_client, f'{interaction.user.mention} I am not in a vocal channel!'

            await interaction.guild.voice_client.stop()
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

    @nextcord.slash_command('music_setvolume','Set volume for the current playing session',default_member_permissions=8,dm_permission=False)
    async def setvolume(self, interaction : nextcord.Interaction, volume : float):
        pass

def setup(bot : commands.Bot):
    bot.add_cog(MusicCommands(bot))