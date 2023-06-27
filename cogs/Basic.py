import nextcord
from nextcord import Embed,Color
from nextcord.ext import commands


class Basic(commands.Cog):
    def __init__(self,bot):
        super().__init__()
        self.bot = bot


    #@commands.command()
    #async def help(self, ctx):
        #pass

    @commands.command()
    async def clear(self, ctx, amount : int = 100):
        try:
            # Verifica se l'utente ha i permessi sufficienti per eliminare i messaggi
            if ctx.channel.permissions_for(ctx.author).manage_messages:
                await ctx.channel.purge(limit=amount+1)
                await ctx.channel.send(embed=Embed(title="Info:",description=f"Successfully cleared {amount} messages.",color=Color.green()), delete_after=5)
                #await ctx.channel.send(f'Successfully cleared {amount} messages.', delete_after=5)
            else:
                await ctx.channel.send("You don't have the necessary permissions to use this command.")
        except AssertionError as e: pass



def setup(bot):
    bot.add_cog(Basic(bot))