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
        async with self.db:
            savedGuildIDs = await self.db.getAllGuildIds()
            unsavedGuilds = set(self.bot.guilds)

            for guild_id in savedGuildIDs:
                # Here we are checking if the guild exist and if the bot is a member of it
                if ((guild:=self.bot.get_guild(guild_id)) == None) and guild not in self.bot.guilds:
                    logger.debug(f"No Guild found for ID: {guild_id}, deleting it from the database.")
                    await self.db.delGuild(guild_id)

                elif guild in self.bot.guilds:
                    logger.debug(f"Updating guild member count for guild {guild.name}(id: {guild.id})")
                    await self.db.adjustGuildMemberCount(guild, guild.member_count,True)

                # List of guild that are not saved in the database and we need to add them to the database
                unsavedGuilds.discard(guild)

            # Here we do not need to check if there is already every guild in the database
            # since we have already done it before
            for guild in unsavedGuilds:
                logger.debug(f"Adding new guild {guild.name} (id: {guild.id}) in the database")
                await self.db.newGuild(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member : nextcord.Member):
        try:
            async with self.db:
                await self.db.adjustGuildMemberCount(member.guild, 1)

                await self.db.newUser(member, {})

            logger.debug(f"User \'{member.name}\'({member.id}) joined guild \'{member.guild.name}\'({member.guild.id})")
        except DatabaseException as e:
            logger.debug(e)

    @commands.Cog.listener()
    async def on_member_remove(self, member : nextcord.Member):
        try:
            async with self.db:
                await self.db.adjustGuildMemberCount(member.guild, -1)

                await self.db.delUser(member)

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