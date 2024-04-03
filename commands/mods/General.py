from nextcord import Embed,Color,utils,channel,Permissions,Interaction
from nextcord.ext import commands
import datetime
import nextcord
import asyncio
import random
import shutil
import os


class General(commands.Cog):
    def __init__(self,bot : commands.Bot):
        super().__init__()
        self.bot = bot

    @nextcord.slash_command('mods_clear',"A simple command for clearing an amount of messages in a chat!",default_member_permissions=1101659119616)
    async def clear(self, interaction : nextcord.Interaction, amount : int = None):
        try:
            await interaction.channel.purge(limit=amount)
            await interaction.response.send_message(f'{interaction.user.mention} Successfully purged {amount} messages on {interaction.channel.name} channel!',ephemeral=True,delete_after=2.5)
        except Exception as e:
            await interaction.response.send_message(f'{interaction.user.mention} An error occured!',ephemeral=True,delete_after=2.5)
            print(e)


def setup(bot : commands.Bot):
    bot.add_cog(General(bot))