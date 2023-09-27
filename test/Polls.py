import nextcord
from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands
import os

class Polls(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    
    @commands.command(name="poll",help="""""")
    async def poll(self, ctx,*,params : str = None):
        try:
            await ctx.message.delete()
            assert params is not None, """
            You must provide a Title for your Poll, use `/poll title=\"YOUR TITLE HERE\" ...`
            You must provide your Params for your Poll, use `/poll ... choices=\"YOUR CHOICES HERE\"`
            """
            assert params.find('title=\"') != -1, 'You must provide a Title for your Poll, use `/poll title=\"YOUR TITLE HERE\" ...`'
            assert params.find('choices=\"') != -1,'You must provide your choices for your Poll, use `/poll ... choices=\"YOUR CHOICES HERE\"`'

            title_start = params.find('title=\"')
            params_start = params.find('choices=\"')

            PARAM_TITLE = params[title_start:params_start].split('\"')[:2]
            PARAM_PARAMS = params[params_start:].split('\"')[:2]

            formatted_options = [(chr(0x1f1e6 + index),option.strip()) for index, option in enumerate(''.join(PARAM_PARAMS[1:]).split())]

            embed = nextcord.Embed(
                title=f"Poll: {PARAM_TITLE[1]}",
                color=Color.blue()
            )
            for num,(emoji, option) in enumerate(formatted_options):
                embed.add_field(name=f"Option-{num+1}", value=f"{emoji} {option}", inline=False)

            poll_message  = await ctx.channel.send(embed=embed)
            
            for i in range(len(str(PARAM_PARAMS[1:]).split())):
                await poll_message.add_reaction(chr(0x1f1e6 + i))
        except AssertionError as e:
            await ctx.message.delete()
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)

def setup(bot):
    bot.add_cog(Polls(bot))



if __name__ == "__main__":
    os.system("python main.py")