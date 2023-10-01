import nextcord
from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands
import random,asyncio,os


class Basic(commands.Cog):
    def __init__(self,bot : commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.command()
    async def clear(self, ctx, amount : int = 100):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True),Permissions(manage_messages=True)] #Permissions(administrator=True),Permissions(manage_messages=True)

        try:
            await ctx.message.delete()
            # Verifica se l'utente ha i permessi sufficienti per eliminare i messaggi
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            await ctx.channel.purge(limit=amount)

            
        
        
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        else:
            await ctx.channel.send(embed=Embed(title="Info:",description=f"Successfully cleared {amount} messages.",color=Color.green()), delete_after=5)
    
    #@commands.Cog.listener()
    #async def on_message(self,message):
        #pass
        #print(message)

    @commands.Cog.listener()
    async def on_member_join(self,member):
        try:
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


def setup(bot):
    bot.add_cog(Basic(bot))

if __name__ == "__main__": os.system("python main.py")