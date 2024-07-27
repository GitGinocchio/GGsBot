from nextcord import Embed,Color,utils,channel,Permissions,Interaction,slash_command
from nextcord.ext import commands
from utils.jsonfile import JsonFile
from utils.terminal import getlogger
import datetime
import nextcord
import asyncio
import random
import shutil
import os


logger = getlogger()

class UpdateMetadata(commands.Cog):
    def __init__(self,bot : commands.Bot):
        super().__init__()
        self.dirfmt = './data/guilds/{guild_id}'
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            datadir = self.dirfmt.format(guild_id=guild.id)

            if not os.path.exists(datadir):
                logger.warning(f"Leaving guild \'{guild.name}\'({guild.id}) no data found!")
                await guild.leave()

    @commands.Cog.listener()
    async def on_member_join(self, member : nextcord.Member):
        datadir = self.dirfmt.format(guild_id=member.guild.id)

        try:
            assert os.path.exists(f'{datadir}/metadata.json')

            file = JsonFile(f'{datadir}/metadata.json')
            file['guild_member_count'] += 1
            file['guild_last_update'] = str(datetime.datetime.now(datetime.UTC)) + ' UTC'
            logger.debug(f"User \'{member.name}\'({member.id}) joined guild \'{member.guild.name}\'({member.guild.id})")
        except AssertionError as e:
            logger.warning(e)

    @commands.Cog.listener()
    async def on_member_remove(self, member : nextcord.Member):
        datadir = self.dirfmt.format(guild_id=member.guild.id)

        try:
            assert os.path.exists(f'{datadir}/metadata.json')

            file = JsonFile(f'{datadir}/metadata.json')
            file['guild_member_count'] -= 1
            file['guild_last_update'] = str(datetime.datetime.now(datetime.UTC)) + ' UTC'
            logger.debug(f"User \'{member.name}\'({member.id}) leaved guild \'{member.guild.name}\'({member.guild.id})")
        except AssertionError as e:
            logger.warning(e)

    @commands.Cog.listener()
    async def on_guild_join(self, guild : nextcord.Guild):
        await self.newguild(guild)
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild : nextcord.Guild):
        datadir = self.dirfmt.format(guild_id=guild.id)
        
        try:
            assert os.path.exists(datadir)

            shutil.rmtree(datadir)
            logger.debug(f"Kicked from guild \'{guild.name}\'({guild.id})")
        except AssertionError as e:
            logger.warning(e)

    async def newguild(self, guild : nextcord.Guild):
        datadir = self.dirfmt.format(guild_id=guild.id)

        try:
            os.mkdir(datadir)
        except Exception as e:
            logger.warning(f'Error on "newguild": {e}')
            return

        file = JsonFile(f'{datadir}/metadata.json')
        file['guild_join_date'] = str(datetime.datetime.now(datetime.UTC)) + ' UTC'
        file['guild_last_update'] = str(datetime.datetime.now(datetime.UTC)) + ' UTC'
        file['guild_name'] = guild.name
        file['guild_id'] = guild.id
        file['guild_owner'] = guild.owner_id
        file['guild_member_count'] = sum(1 for member in guild.members if not member.bot)
        file['guild_bots_count'] = sum(1 for member in guild.members if member.bot)
        file['guild_roles_count'] = len(guild.roles)
        file['guild_description'] = guild.description
        file['guild_premium_tier'] = guild.premium_tier
        file['guild_premium_subscription_count'] = guild.premium_subscription_count
        file.save()

def setup(bot : commands.Bot):
    bot.add_cog(UpdateMetadata(bot))