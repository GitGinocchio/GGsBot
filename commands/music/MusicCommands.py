from nextcord import Embed,Color,utils,channel,Permissions,Interaction
from utils.jsonfile import JsonFile
from nextcord.ext import commands
from .YoutubeExtension import *
import nextcord



class MusicCommands(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot

    #async def cog_application_command_before_invoke(self, interaction: nextcord.Interaction):
        #print(interaction)

    @nextcord.slash_command('play',"Play songs with the bot in your channel!",default_member_permissions=2147483648,dm_permission=False)
    async def play(self, interaction : nextcord.Interaction, queryurl : str = None):
        try:
            assert interaction.user.voice.channel, f'{interaction.user.mention} You have to join a voice channel first!'
            assert interaction.guild.voice_client, f'{interaction.user.mention} You have to call */join* command first!'

            if not interaction.guild.voice_client.is_playing():
                interaction.guild.voice_client.stop()
                info = await get_info_from_url(queryurl)
                interaction.guild.voice_client.play(nextcord.FFmpegOpusAudio(info['url'],executable='./bin/ffmpeg.exe'))
                await interaction.response.send_message(f"{interaction.user.mention} playing {info['title']}...")
            else:
                pass #aggiungere in coda...
        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True,delete_after=5.0)

    @nextcord.slash_command('stop',"Stop the current playing session!")
    async def stop(self, interaction : nextcord.Interaction):
        pass

    @nextcord.slash_command("join","Bring the bot on your current voice channel!",default_member_permissions=2147483648,dm_permission=False)
    async def join(self, interaction : nextcord.Interaction):
        try:
            assert interaction.user.voice, f'{interaction.user.mention} You have to join a voice channel first!'
            assert not interaction.guild.voice_client, f'{interaction.user.mention} I am currently in a voice channel!'

            await interaction.user.voice.channel.connect()
            await interaction.response.send_message(f"{interaction.user.mention} I joined your voice channel!", ephemeral=True, delete_after=2.5)

        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True,delete_after=5)
        
    @nextcord.slash_command('leave',"The bot will leave your vocal channel!",default_member_permissions=2147483648,dm_permission=False)
    async def leave(self, interaction : nextcord.Interaction):
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message(f"{interaction.user.mention} I left the voice channel!",ephemeral=True,delete_after=5)
        else:
            await interaction.response.send_message(f"{interaction.user.mention} I am not in a vocal channel!",ephemeral=True,delete_after=5)



def setup(bot : commands.Bot):
    bot.add_cog(MusicCommands(bot))