from nextcord import Embed,Color,Permissions
from nextcord.ext import commands
from utils.jsonfile import JsonFile
import nextcord
import os


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
        self.dirfmt = './data/guilds/{guild_id}/commands.general.Greetings'
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member : nextcord.Member):
        workingdir = self.dirfmt.format(guild_id=member.guild.id)
        
        if os.path.exists(workingdir + '/config.json'):
            try:
                setup = JsonFile(workingdir + '/config.json')
                channel = self.bot.get_channel(setup['welcome_channel_id'])
                embed = Embed(
                    title='Welcome!',
                    description=f'Welcome to {member.name}, {member.mention} Enjoy your stay and feel free to look around!',
                    color=Color.green()
                )

                embed.set_thumbnail(url=(member.avatar.url if member.avatar else member.default_avatar.url))
            except AssertionError as e:
                await channel.send(embed=Embed(title="Error:",description=e,color=Color.red()))
            else:
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member : nextcord.Member):
        workingdir = self.dirfmt.format(guild_id=member.guild.id)

        if os.path.exists(workingdir + '/config.json'):
            try:
                setup = JsonFile(workingdir + '/config.json')
                channel = self.bot.get_channel(setup['goodbye_channel_id'])
                embed = Embed(
                    title='Goodbye!',
                    description=f'Goodbye to {member.name}, {member.mention} we\'re sorry to see you go, we hope you\'ll be back soon!',
                    color=Color.green()
                )

                embed.set_thumbnail(url=(member.avatar.url if member.avatar else member.default_avatar.url))
            except AssertionError as e:
                await channel.send(embed=Embed(title="Error:",description=e,color=Color.red()))
            else:
                await channel.send(embed=embed)

def setup(bot : commands.Bot):
    bot.add_cog(Greetings(bot))