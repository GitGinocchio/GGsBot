from nextcord.ext.commands import \
    Cog,                          \
    Bot


from utils.terminal import getlogger

logger = getlogger()

class FreeGames(Cog):
    def __init__(self, bot : Bot):
        self.bot = bot



def setup(bot : Bot):
    bot.add_cog(FreeGames(bot))