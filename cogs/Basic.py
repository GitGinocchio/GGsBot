import nextcord
from nextcord import Embed,Color,utils,channel,Permissions,Interaction,slash_command
from nextcord.ext import commands
import random,asyncio,os
from jsonutils import jsonfile


class Basic(commands.Cog):
    def __init__(self,bot : commands.Bot):
        super().__init__()
        self.bot = bot
        self.content = jsonfile('./cogs/data/saved.json')

    """
    Migration from decorator @commands.command() to @nextcord.slash_command() for client integration of the command in discord ui.
    >>>
    """
    #@commands.command()
    @slash_command('clear',"A simple command for clearing an amount of messages in a chat!",default_member_permissions=8)
    async def clear(self,interaction: Interaction, amount : int = 100):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True),Permissions(manage_messages=True)] #Permissions(administrator=True),Permissions(manage_messages=True)

        try:
            await interaction.channel.purge(limit=amount)
            #await ctx.message.delete()
            # Verifica se l'utente ha i permessi sufficienti per eliminare i messaggi
            assert any(interaction.channel.permissions_for(interaction.user).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in interaction.user.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            #await ctx.channel.purge(limit=amount)

            
        
        
        except AssertionError as e:
            await interaction.response.send_message(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5,ephemeral=True)
            #await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        else:
            await interaction.response.send_message(embed=Embed(title="Info:",description=f"Successfully cleared {amount} messages.",color=Color.green()), delete_after=5,ephemeral=True)
            #await ctx.channel.send(embed=Embed(title="Info:",description=f"Successfully cleared {amount} messages.",color=Color.green()), delete_after=5)

    @commands.Cog.listener()
    async def on_member_join(self,member):
        try:
            if self.content["Basic"]["welcome_channel_id"] is not None:
                channel = self.bot.get_channel(self.content["Basic"]["welcome_channel_id"])
            else:
                channel = member.guild.system_channel  # Ottieni il canale predefinito per i messaggi di benvenuto
                assert channel is not None,'System channel is not defined. (trying to send a message of welcome in system channel)'
            
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
    async def on_member_remove(self,member):
        try:
            if self.content["Basic"]["goodbye_channel_id"] is not None:
                channel = self.bot.get_channel(self.content["Basic"]["goodbye_channel_id"])
            else: 
                channel = member.guild.system_channel  # Ottieni il canale predefinito per i messaggi di benvenuto
                assert channel is not None,'System channel is not defined. (trying to send a message of welcome in system channel)'
            
            embed = Embed(
                title='Welcome!',
                description=f'Goodbye to {member.name}, {member.mention} we\'re sorry to see you go, we hope you\'ll be back soon!',
                color=Color.green()
            )
            if member.avatar is not None: embed.set_thumbnail(url=member.avatar.url)
        except AssertionError as e:
            await channel.send(embed=Embed(title="Error:",description=e,color=Color.red()))
        else:
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Basic(bot))
