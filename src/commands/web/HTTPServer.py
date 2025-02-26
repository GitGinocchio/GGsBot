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
from utils.config import config
from utils.db import Database

logger = getlogger()

WEB_DIR = abspath('./src/commands/web')
PUBLIC_DIR = join(WEB_DIR, 'public')
TEMPLATES_DIR = join(PUBLIC_DIR, 'templates')
STAITC_DIR = join(PUBLIC_DIR, 'static')

web_config = config.get('web', {})

class HTTPServer(Cog):
    def __init__(self, 
        bot : Bot = None, 
        *, 
        address : str = web_config.get('address', '0.0.0.0'), 
        protocol : str = web_config.get('protocol', 'http'),
        port : int = web_config.get('port', 21662), 
        debug : bool = web_config.get('debug', False)
    ):
        if bot: Cog.__init__(self)
        self.loop = bot.loop if bot else asyncio.get_event_loop()
        self.app = Application(logger=logger, loop=self.loop if bot else None, debug=debug)
        self.runner = AppRunner(self.app, handle_signals=False)
        self.site : TCPSite = None
        self.db = Database(loop=self.loop)
        self.bot : Bot | None = bot
        self.address = address
        self.protocol = protocol
        self.port = port
        self.running = False

        self.app.router.add_static('/static/', STAITC_DIR, show_index=True)
        aiojinja.setup(self.app, loader=jinja2.FileSystemLoader(TEMPLATES_DIR))
        self.app.middlewares.append(self.logger)

        # user
        self.app.router.add_get('/',                        self.index)
        self.app.router.add_get('/about',                   self.about)
        self.app.router.add_get('/docs',                    self.docs)
        self.app.router.add_get('/support',                 self.support)
        self.app.router.add_get('/faq',                     self.faq)

        self.app.router.add_get('/privacy-policy',          self.pp)
        self.app.router.add_get('/terms-of-service',        self.tos)
        self.app.router.add_get('/invite',                  self.invite)
        self.app.router.add_get('/contact',                 self.contact)


        # api
        self.app.router.add_get('/api/status',              self.status)
        self.app.router.add_get('/api/verify',              self.verify)
        self.app.router.add_get('/api/webhooks',            self.webhooks)
        self.app.router.add_get('/api/interactions',        self.interactions)

    @middleware
    async def logger(self, request : Request, handler : RequestHandler):
        response : Response = await handler(request)
        log = f"{request.remote} - {request.method} ({response.status}) {request.path}"

        if response.status < 399: logger.info(log)
        else: logger.error(log)

        return response
    
    # user

    @aiojinja.template('index.html')
    async def index(self, request : Request): return { "request" : request}

    @aiojinja.template('about.html')
    async def about(self, request : Request): return { "request" : request}

    @aiojinja.template('docs.html')
    async def docs(self, request : Request): return { "request" : request}

    @aiojinja.template('support.html')
    async def support(self, request : Request): return { "request" : request}

    @aiojinja.template('faq.html')
    async def faq(self, request : Request): return { "request" : request}

    @aiojinja.template('tos.html')
    async def tos(self, request : Request): return { "request" : request}
    
    @aiojinja.template('pp.html')
    async def pp(self, request : Request): return { "request" : request}

    async def invite(self, request : Request):
        return Response(text="Invite", status=200)
    
    async def contact(self, request : Request):
        return Response(text="Contact", status=200)

    # api

    async def verify(self, request : Request):
        return Response(text="Verify", status=200)
    
    async def webhooks(self, request : Request):
        return Response(text="Webhooks", status=200)
    
    async def interactions(self, request : Request):
        return Response(text="Interactions", status=200)

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
        try:
            if not self.bot:
                logger.warning("By running the HTTP server as a standalone process, you will not be able to get bot methods")

            await self.runner.setup()

            self.site = TCPSite(self.runner, self.address, self.port)

            await self.site.start()
            self.running = True

            logger.info(f"HTTP Server started on {self.protocol}://{self.address}:{self.port}")

            if self.bot: return

            logger.info("press Ctrl+C to stop the server")

            while True: await asyncio.sleep(1)

        except asyncio.CancelledError: 
            # TODO: Handle shutdown gracefully
            # == KeyboardInterrupt
            pass
        except Exception as e:
            logger.error(e)
        finally:
            logger.info("User requested shutdown")
            await self.shutdown()

    async def restart(self):
        logger.info("Restarting HTTP Server...")
        await self.shutdown()
        await self.run()

    async def shutdown(self):
        await self.runner.cleanup()
        logger.info("Cleaned up resources")
        await self.runner.shutdown()
        logger.info("Server stopped")
        self.running = False

    @Cog.listener()
    async def on_ready(self):
        if not self.running:
            await self.run()



def setup(bot : Bot):
    bot.add_cog(HTTPServer(bot))