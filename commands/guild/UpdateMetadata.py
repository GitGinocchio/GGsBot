from nextcord.ext import commands
import nextcord

from utils.terminal import getlogger
from utils.exceptions import DatabaseException
from utils.db import Database

logger = getlogger()

class UpdateMetadata(commands.Cog):
    def __init__(self,bot : commands.Bot):
        super().__init__()
        self.db = Database()
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                # maybe too many query at the same time:
                # hasGuild
                # adjustGuildMemberCount
                # newGuild
                async with self.db:
                    if await self.db.hasGuild(guild) and guild.member_count is not None:
                        await self.db.adjustGuildMemberCount(guild, guild.member_count,True)
                    else:
                        await self.db.newGuild(guild)
            except DatabaseException as e:
                logger.error(e)

  
        #logger.warning(f"Leaving guild \'{guild.name}\'({guild.id}) no data found!")
        #await guild.leave()

    @commands.Cog.listener()
    async def on_member_join(self, member : nextcord.Member):
        try:
            async with self.db:
                await self.db.adjustGuildMemberCount(member.guild, 1)

            logger.debug(f"User \'{member.name}\'({member.id}) joined guild \'{member.guild.name}\'({member.guild.id})")
        except DatabaseException as e:
            logger.debug(e)

    @commands.Cog.listener()
    async def on_member_remove(self, member : nextcord.Member):
        try:
            async with self.db:
                await self.db.adjustGuildMemberCount(member.guild, -1)

            logger.debug(f"User \'{member.name}\'({member.id}) leaved guild \'{member.guild.name}\'({member.guild.id})")
        except DatabaseException as e:
            logger.debug(e)

    @commands.Cog.listener()
    async def on_guild_join(self, guild : nextcord.Guild):
        try:
            async with self.db: 
                await self.db.newGuild(guild)

            logger.debug(f"{self.bot.user.name} joined guild  \'{guild.name}\'({guild.id})")
        except DatabaseException as e:
            logger.debug(e)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild : nextcord.Guild):
        try:
            async with self.db: await self.db.delGuild(guild)

            logger.debug(f"Kicked from guild \'{guild.name}\'({guild.id})")
        except DatabaseException as e:
            logger.debug(e)

def setup(bot : commands.Bot):
    bot.add_cog(UpdateMetadata(bot))