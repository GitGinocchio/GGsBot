from nextcord import Embed,Color,Permissions
from nextcord.ext import commands
from utils.jsonfile import JsonFile
import datetime
import nextcord
import asyncio
import random
import os


permissions = Permissions(
    use_slash_commands=True,
    mention_everyone=True,
    manage_channels=True,
    manage_messages=True,
    send_messages=True,
)

class ServerMessages(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.bot = bot

    @nextcord.slash_command("servermessages",default_member_permissions=permissions,dm_permission=False)
    async def servermessages(self, interaction : nextcord.Interaction): pass

    @servermessages.subcommand("setup","Set up server messages in the server.")
    async def setup(self, interaction : nextcord.Interaction, welcome_channel : nextcord.TextChannel, goodbye_channel : nextcord.TextChannel):
        try:
            os.makedirs(f'./data/guilds/{interaction.guild_id}/ServerMessages',exist_ok=True)
        except OSError as e:
            await interaction.response.send_message(f"Error occurred while creating directory: {e}", ephemeral=True)
            return
        else:
            file = JsonFile(f'./data/guilds/{interaction.guild_id}/ServerMessages/setup.json')
            file['welcome_channel_id'] = welcome_channel.id
            file['goodbye_channel_id'] = goodbye_channel.id
            file.save()
            await interaction.response.send_message("Server Messages setup completed successfully!", ephemeral=True)

    @servermessages.subcommand("teardown","Teardown server messages in the server.")
    async def teardown(self, interaction : nextcord.Interaction):
        try:
            pass
        except Exception as e:
            pass
        else:
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member : nextcord.Member):
        setup_path = f'./data/guilds/{member.guild.id}/ServerMessages/setup.json'
        
        if os.path.exists(setup_path):
            try:
                setup = JsonFile(setup_path)
                channel = self.bot.get_channel(setup['welcome_channel_id'])
                embed = Embed(
                    title='Welcome!',
                    description=f'Welcome to {member.name}, {member.mention} Enjoy your stay and feel free to look around!',
                    color=Color.green()
                )
                if member.avatar is not None: embed.set_thumbnail(url=member.avatar.url)
            except AssertionError as e:
                await channel.send(embed=Embed(title="Error:",description=e,color=Color.red()))
            else:
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self,member : nextcord.Member):
        setup_path = f'./data/guilds/{member.guild.id}/ServerMessages/setup.json'

        if os.path.exists(setup_path):
            try:
                setup = JsonFile(setup_path)
                channel = self.bot.get_channel(setup['goodbye_channel_id'])
                embed = Embed(
                    title='Goodbye!',
                    description=f'Goodbye to {member.name}, {member.mention} we\'re sorry to see you go, we hope you\'ll be back soon!',
                    color=Color.green()
                )
                if member.avatar is not None: embed.set_thumbnail(url=member.avatar.url)
            except AssertionError as e:
                await channel.send(embed=Embed(title="Error:",description=e,color=Color.red()))
            else:
                await channel.send(embed=embed)

def setup(bot : commands.Bot):
    bot.add_cog(ServerMessages(bot))