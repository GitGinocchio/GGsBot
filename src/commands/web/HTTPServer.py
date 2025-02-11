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
        self.address = '0.0.0.0'
        self.protocol = 'http'
        self.port = 21662
        self.bot = bot

        self.app.router.add_get('/', self.index)

    async def index(self, request : Request):
        return Response(text="Hello World!", content_type="text/plain")



    @Cog.listener()
    async def on_ready(self):
        runner = AppRunner(self.app)
        await runner.setup()
        site = TCPSite(runner, self.address, self.port)
        await site.start()
        logger.info(f"HTTP Server started on {self.protocol}://{self.address}:{self.port}")



def setup(bot : Bot):
    bot.add_cog(HTTPServer(bot))