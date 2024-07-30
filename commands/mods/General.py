from nextcord import Embed,Color,utils,channel,Permissions,Interaction
from nextcord.ext import commands
from utils.terminal import getlogger
import datetime
import nextcord
import asyncio
import random
import shutil
import os

logger = getlogger()

permissions = Permissions(
    manage_messages=True
)

class General(commands.Cog):
    def __init__(self,bot : commands.Bot):
        super().__init__()
        self.bot = bot

    @nextcord.slash_command('mods',"...",default_member_permissions=permissions)
    async def mods(self, interaction : nextcord.Interaction): pass

    @mods.subcommand('clear',"A simple command for clearing an amount of messages in a chat!")
    async def clear(self, interaction : nextcord.Interaction, amount : int = None):
        try:
            await interaction.response.defer(ephemeral=True)

            await interaction.channel.purge(limit=amount)
        except Exception as e:
            await interaction.followup.send(f'{interaction.user.mention} An error occured!',ephemeral=True,delete_after=2.5)
            logger.error(e)
        else:
            await interaction.followup.send(f'{interaction.user.mention} Successfully purged {amount} messages!',ephemeral=True,delete_after=2.5)



def setup(bot : commands.Bot):
    bot.add_cog(General(bot))