from nextcord.ext.commands import Bot, Cog
from aiohttp.web import \
    Application,        \
    AppRunner,          \
    Response,           \
    Request,            \
    RequestHandler,     \
    TCPSite,            \
    middleware
from datetime import datetime, timezone
from os.path import join, abspath
import aiohttp_jinja2 as aiojinja
import jinja2
import asyncio
import psutil
import json
import ssl

from utils.terminal import getlogger

logger = getlogger()

PUBLIC_DIR = abspath('./src/commands/web/public')
TEMPLATES_DIR = join(PUBLIC_DIR, 'templates')
STAITC_DIR = join(PUBLIC_DIR, 'static')

class HTTPServer(Cog):
    def __init__(self, bot : Bot = None):
        if bot: Cog.__init__(self)
        self.app = Application(logger=logger, loop=bot.loop if bot else None, debug=True)
        self.address = '0.0.0.0'
        self.protocol = 'http'
        self.port = 21662
        self.bot : Bot | None = bot

        self.app.router.add_static('/static/', STAITC_DIR, show_index=True)
        aiojinja.setup(self.app, loader=jinja2.FileSystemLoader(TEMPLATES_DIR))
        self.app.middlewares.append(self.logger)

        self.app.router.add_get('/',                    self.index)
        self.app.router.add_get('/privacy-policy',      self.pp)
        self.app.router.add_get('/terms-of-service',    self.tos)
        self.app.router.add_get('/api/status',          self.status)

    @middleware
    async def logger(self, request : Request, handler : RequestHandler):
        response : Response = await handler(request)
        log = f"{request.remote} - {request.method} ({response.status}) {request.path}"

        if response.status < 399: logger.info(log)
        else: logger.error(log)

        return response


    @aiojinja.template('index.html')
    async def index(self, request : Request):
        return {}

    @aiojinja.template('tos.html')
    async def tos(self, request : Request):
        return {}
    
    @aiojinja.template('pp.html')
    async def pp(self, request : Request):
        return {}

    async def status(self, request : Request):
        uptime = datetime.now(timezone.utc) - datetime.fromtimestamp(psutil.boot_time(), timezone.utc)

        # Cpu
        cpu_count = {'physical': psutil.cpu_count(False), 'logical': psutil.cpu_count()}
        cpu_freqs = [{'current': freq.current, 'min': freq.min, 'max': freq.max} for freq in psutil.cpu_freq(True)]
        cpu_usage = { 'percpu' : psutil.cpu_percent(percpu=True), 'total' : psutil.cpu_percent()} 

        # Memory
        ram_usage = {'available': (memory:=psutil.virtual_memory()).available,'free' : memory.free,'percent' : memory.percent,'total' : memory.total,'used' : memory.used}

        # Disk
        disk_usage = { 'total' : (disk:=psutil.disk_usage('/')).total, 'used' : disk.used, 'free' : disk.free, 'percent' : disk.percent }

        # Swap
        swap_usage = { 'total' : (swap:=psutil.swap_memory()).total, 'used' : swap.used, 'free' : swap.free, 'percent' : swap.percent, 'sin' : swap.sin, 'sout' : swap.sout }

        status = {
            'uptime' : str(uptime),
            'cpu' : {
                'count' : cpu_count,
                'freqs' : cpu_freqs,
                'usage' : cpu_usage
            },
            'memory' : ram_usage,
            'disk' : disk_usage,
            'swap' : swap_usage,

            'discord' : {
                'latency' : self.bot.latency if self.bot else None
            }
        }

        return Response(text=json.dumps(status), content_type="application/json")

    async def run(self):
        runner = None
        try:
            if not self.bot:
                logger.warning("By running the HTTP server as a standalone process, you will not be able to get bot methods")

            runner = AppRunner(self.app)
            await runner.setup()

            site = TCPSite(runner, self.address, self.port)
            await site.start()

            logger.info(f"HTTP Server started on {self.protocol}://{self.address}:{self.port}")

            if self.bot: return

            while True: await asyncio.sleep(1)

        except asyncio.CancelledError: 
            # TODO: Handle shutdown gracefully
            # == KeyboardInterrupt

            logger.info("HTTP Server stopped by user")
        finally:
            if runner:
                await runner.cleanup()
                await runner.shutdown()

    @Cog.listener()
    async def on_ready(self): await self.run()



def setup(bot : Bot):
    bot.add_cog(HTTPServer(bot))