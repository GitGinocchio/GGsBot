from nextcord import Embed,Color,Permissions
from nextcord.ext import commands
import nextcord

from utils.db import Database
from utils.exceptions import ExtensionException
from utils.commons import Extensions

permissions = Permissions(
    use_slash_commands=True,
    mention_everyone=True,
    manage_channels=True,
    manage_messages=True,
    send_messages=True,
)

class Greetings(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.db = Database()
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member : nextcord.Member):
        try:
            async with self.db:
                config = await self.db.getExtensionConfig(member.guild,Extensions.GREETINGS)

            if not (welcome_channel_id:=config.get('welcome_channel', None)): return
        
            channel = self.bot.get_channel(welcome_channel_id)
            embed = Embed(
                title='Welcome!',
                description=f'Welcome to {member.name}, {member.mention} Enjoy your stay and feel free to look around!',
                color=Color.green()
            )

            embed.set_thumbnail(url=(member.avatar.url if member.avatar else member.default_avatar.url))
        except ExtensionException as e:
            pass
        else:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member : nextcord.Member):
        try:
            async with self.db:
                config = await self.db.getExtensionConfig(member.guild,Extensions.GREETINGS)

            if not (goodbye_channel_id:=config.get('goodbye_channel', None)): return

            channel = self.bot.get_channel(goodbye_channel_id)
            embed = Embed(
                title='Goodbye!',
                description=f'Goodbye to {member.name}, {member.mention} we\'re sorry to see you go, we hope you\'ll be back soon!',
                color=Color.green()
            )

            embed.set_thumbnail(url=(member.avatar.url if member.avatar else member.default_avatar.url))
        except ExtensionException as e:
            pass
        else:
            await channel.send(embed=embed)

def setup(bot : commands.Bot):
    bot.add_cog(Greetings(bot))