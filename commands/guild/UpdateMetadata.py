from nextcord import Embed,Color,utils,channel,Permissions,Interaction,slash_command
from nextcord.ext import commands
from utils.jsonfile import JsonFile
import datetime
import nextcord
import asyncio
import random
import shutil
import os



class UpdateMetadata(commands.Cog):
    def __init__(self,bot : commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if str(guild.id) not in os.listdir('./data/guilds/'):
                await self.newguild(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member : nextcord.Member):
        path = f'./data/guilds/{member.guild.id}/metadata.json'
        if os.path.exists(path):
            file = JsonFile(path)
            file['guild_member_count'] += 1
            file['guild_last_update'] = str(datetime.datetime.utcnow()) + ' UTC'

    @commands.Cog.listener()
    async def on_member_remove(self, member : nextcord.Member):
        path = f'./data/guilds/{member.guild.id}/metadata.json'
        if os.path.exists(path):
            file = JsonFile(path)
            file['guild_member_count'] -= 1
            file['guild_last_update'] = str(datetime.datetime.utcnow()) + ' UTC'

    @commands.Cog.listener()
    async def on_guild_join(self, guild : nextcord.Guild):
        try:
            os.mkdir(f'./data/guilds/{guild.id}')
        except FileExistsError: pass
        else:
            file = JsonFile(f'./data/guilds/{guild.id}/metadata.json')
            file['guild_join_date'] = str(datetime.datetime.utcnow()) + ' UTC'
            file['guild_last_update'] = str(datetime.datetime.utcnow()) + ' UTC'
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
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild : nextcord.Guild):
        try:
            shutil.rmtree(f'./data/guilds/{guild.id}')
        except Exception as e: 
            print(e)

    async def newguild(self, guild : nextcord.Guild):
        try:
            os.mkdir(f'./data/guilds/{guild.id}')
        except FileExistsError: pass
        else:
            file = JsonFile(f'./data/guilds/{guild.id}/metadata.json')
            file['guild_join_date'] = str(datetime.datetime.utcnow()) + ' UTC'
            file['guild_last_update'] = str(datetime.datetime.utcnow()) + ' UTC'
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