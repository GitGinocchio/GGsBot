from nextcord.ext.commands import Bot, Cog
from aiohttp.web import \
    Application,        \
    AppRunner,          \
    Response,           \
    Request,            \
    TCPSite

from utils.terminal import getlogger

logger = getlogger()

class HTTPServer(Cog):
    def __init__(self, bot : Bot):
        Cog.__init__(self)
        self.app = Application(logger=logger, loop=bot.loop)
        self.address = '127.0.0.1'
        self.protocol = 'http'
        self.port = 8080
        self.bot = bot

        self.app.router.add_get('/', self.index)

    @Cog.listener()
    async def on_ready(self):
        runner = AppRunner(self.app)
        await runner.setup()
        site = TCPSite(runner, self.address, self.port)
        await site.start()
        logger.info(f"HTTP Server started on {self.protocol}://{self.address}:{self.port}")


    async def index(self, request : Request):
        return Response(text="Hello World!", content_type="text/plain")



def setup(bot : Bot):
    bot.add_cog(HTTPServer(bot))