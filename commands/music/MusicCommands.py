from nextcord import Embed,Color,utils,channel,Permissions,Interaction
from .YoutubeExtension import YoutubeExtension
from utils.terminal import getlogger
from nextcord.ext import commands
from utils.config import config
from utils.system import OS,ARCH
import nextcord
import sys

logger = getlogger()

class MusicCommands(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.yt = YoutubeExtension(loop=bot.loop,params=config['music']['youtube']['ytdl_params'])
        self.queue = []
        self.bot = bot

    #2147483648
        
    @nextcord.slash_command('music_play',"Play songs with the bot in your channel!",default_member_permissions=8,dm_permission=False)
    async def play(self, interaction : nextcord.Interaction, queryorurl : str = None):
        try:
            assert interaction.user.voice.channel, f'{interaction.user.mention} You have to join a voice channel first!'
            assert interaction.guild.voice_client, f'{interaction.user.mention} You have to call */join* command first!'

            if not interaction.guild.voice_client.is_playing():
                interaction.guild.voice_client.stop()
                info = await self.yt.get_info(queryorurl)
                source = nextcord.FFmpegPCMAudio(info['url'],executable=str(config['music']['ffmpeg_path']).format(os=OS,arch=ARCH),stderr=sys.stderr)
                interaction.guild.voice_client.play(nextcord.PCMVolumeTransformer(source, config['music']['defaultvolume']))
                await interaction.response.send_message(f"{interaction.user.mention} playing {info['title']}...",ephemeral=True,delete_after=5.0)
            else:
                await interaction.response.send_message(f"{interaction.user.mention} added {info['title']} to queue...",ephemeral=True,delete_after=5.0)
                pass #aggiungere in coda...
        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True,delete_after=5.0)

    @nextcord.slash_command('music_volume','Set volume for current stream',default_member_permissions=8,dm_permission=False)
    async def volume(self, interaction : nextcord.Interaction, volume : float = config['music']['defaultvolume']):
        pass

    @nextcord.slash_command('music_skip',"wdawd",default_member_permissions=8,dm_permission=False)
    async def skip(self, interaction : nextcord.Interaction):
        pass

    @nextcord.slash_command('music_stop',"Stop the current playing session!",default_member_permissions=8,dm_permission=False)
    async def stop(self, interaction : nextcord.Interaction):
        pass

    @nextcord.slash_command("music_join","Bring the bot on your current voice channel!",default_member_permissions=8,dm_permission=False)
    async def join(self, interaction : nextcord.Interaction):
        try:
            assert interaction.user.voice, f'{interaction.user.mention} You have to join a voice channel first!'
            assert not interaction.guild.voice_client, f'{interaction.user.mention} I am currently in a voice channel!'

            await interaction.user.voice.channel.connect()
            await interaction.response.send_message(f"{interaction.user.mention} I joined your voice channel!", ephemeral=True, delete_after=5.0)

        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True,delete_after=5.0)
        
    @nextcord.slash_command('music_leave',"The bot will leave your vocal channel!",default_member_permissions=8,dm_permission=False)
    async def leave(self, interaction : nextcord.Interaction):
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message(f"{interaction.user.mention} I left the voice channel!",ephemeral=True,delete_after=5)
        else:
            await interaction.response.send_message(f"{interaction.user.mention} I am not in a vocal channel!",ephemeral=True,delete_after=5)



def setup(bot : commands.Bot):
    bot.add_cog(MusicCommands(bot))