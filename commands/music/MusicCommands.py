from nextcord import Embed,Color,utils,channel,Permissions,Interaction,slash_command
from nextcord.ext import commands
from utils.jsonfile import JsonFile
import nextcord



class MusicCommands(commands.Cog):
    def __init__(self, bot : commands.Bot):
        super().__init__()
        self.bot = bot

    @nextcord.slash_command('play',"Play songs with the bot in your channel!",default_member_permissions=2147483648,dm_permission=False)
    async def play(self, interaction : nextcord.Interaction, queryurl : str = None):
        pass

    @nextcord.slash_command("join","Bring the bot on your current voice channel!",default_member_permissions=2147483648,dm_permission=False)
    async def join(self, interaction : nextcord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message(f"{interaction.user.mention} You have to join a voice channel first!", ephemeral=True, delete_after=2.5)
        elif interaction.guild.voice_client is not None:
            await interaction.response.send_message(f"{interaction.user.mention} I am currently in a voice channel!", ephemeral=True, delete_after=2.5)
        else:
            await interaction.user.voice.channel.connect()
            await interaction.response.send_message(f"{interaction.user.mention} I joined your voice channel!", ephemeral=True, delete_after=2.5)
        
    @nextcord.slash_command('leave',"The bot will leave your vocal channel!",default_member_permissions=2147483648,dm_permission=False)
    async def leave(self, interaction : nextcord.Interaction):
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message(f"{interaction.user.mention} I left the voice channel!",ephemeral=True,delete_after=2.5)
        else:
            await interaction.response.send_message(f"{interaction.user.mention} I am not in a vocal channel!",ephemeral=True,delete_after=2.5)



def setup(bot : commands.Bot):
    bot.add_cog(MusicCommands(bot))