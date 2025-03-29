from nextcord.ext.commands import Bot, Cog
from web.HTTPServer import HTTPServer
from utils.terminal import getlogger
from utils.config import config

logger = getlogger()

web_config = config.get('web', {})

class HTTPServerCog(Cog, HTTPServer):
    def __init__(self, bot : Bot = None):
        HTTPServer.__init__(self, bot)
        Cog.__init__(self)

    @Cog.listener()
    async def on_ready(self):
        if not self.running:
            await self.run()



def setup(bot : Bot):
    bot.add_cog(HTTPServerCog(bot))