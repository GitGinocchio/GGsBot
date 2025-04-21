from nextcord.ext.commands import Bot, Cog
from aiohttp.web import \
    Application,        \
    AppRunner,          \
    Response,           \
    Request,            \
    RequestHandler,     \
    TCPSite,            \
    HTTPFound,          \
    middleware
from datetime import datetime, timezone
from os.path import join, abspath
import aiohttp_jinja2 as aiojinja
import jinja2
import asyncio
import psutil
import json
import ssl
import os

from utils.terminal import getlogger
from utils.config import config
from utils.db import Database
from utils.system import \
    OS,                  \
    get_psutil_stats,    \
    get_top_stats        \

logger = getlogger()

WEB_DIR = abspath('./src/web')
PUBLIC_DIR = join(WEB_DIR, 'public')
TEMPLATES_DIR = join(PUBLIC_DIR, 'templates')
STATIC_DIR = join(PUBLIC_DIR, 'static')

web_config = config.get('web', {})

class HTTPServer:
    def __init__(self, 
        bot : Bot = None, 
        *, 
        address : str = web_config.get('address', '127.0.0.1'), 
        protocol : str = web_config.get('protocol', 'http'),
        port : int = web_config.get('port', 21662), 
        debug : bool = web_config.get('debug', False)
    ):
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

        self.start_time = datetime.now(timezone.utc)

        self.app.router.add_static('/static/', STATIC_DIR, show_index=True)
        aiojinja.setup(self.app, loader=jinja2.FileSystemLoader(TEMPLATES_DIR))
        self.app.middlewares.append(self.logger)

        # 404
        self.app.router.add_route("*", '/{tail:.*}',        self.four_o_four)

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

        self.app.router.add_get('/authorize',               self.authorize)

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
    async def index(self, request : Request): 
        return { "request" : request}

    @aiojinja.template('about.html')
    async def about(self, request : Request): 
        return { "request" : request, "underconstruction" : True}

    @aiojinja.template('docs.html')
    async def docs(self, request : Request): 
        return { "request" : request, "underconstruction" : True}

    @aiojinja.template('support.html')
    async def support(self, request : Request): 
        return { "request" : request, "underconstruction" : True}

    @aiojinja.template('faq.html')
    async def faq(self, request : Request): 
        return { "request" : request, "underconstruction" : True}

    @aiojinja.template('tos.html')
    async def tos(self, request : Request): 
        return { "request" : request}
    
    #@aiojinja.template('404.html')
    async def four_o_four(self, request : Request):
        return Response(text="404", status=404)

    @aiojinja.template('pp.html')
    async def pp(self, request : Request): 
        return { "request" : request, "underconstruction" : True}

    async def invite(self, request : Request):
        return Response(text="Invite", status=200)
    
    async def contact(self, request : Request):
        return Response(text="Contact", status=200)

    # api

    async def verify(self, request : Request):
        return Response(text="Verify", status=200)
    
    async def webhooks(self, request : Request):
        return Response(text="Webhooks", status=200)

    async def authorize(self, request : Request):
        pass
        """
        client_id = os.environ.get('CLIENT_ID', None)

        if not client_id:
            return Response(text="No client id found, cannot redirect.", status=404)
        
        return Response(status=302, content_type="text/html", headers={
            "Location": f"https://discord.com/oauth2/authorize?client_id={client_id}",
            "Proxy-Pass" : True
        })
        """
    
    async def interactions(self, request : Request):
        return Response(text="Interactions", status=200)

    async def status(self, request : Request):
        uptime = datetime.now(timezone.utc) - self.start_time

        status = {}

        stats = get_psutil_stats()
        status['machine'] = stats

        status['machine']['os'] = OS
        status['uptime'] = uptime.total_seconds()
        status['discord'] = { 'latency' : self.bot.latency if self.bot else None }
        status['database'] = { 'num_queries' : self.db.num_queries }

        return Response(text=json.dumps(status), content_type="application/json")

    # running/restarting/shutdown methods

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
            logger.info("User requested shutdown")
            await self.shutdown()
        except Exception as e:
            logger.error(e)
            logger.error("A fatal error occurred, shutting down")
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

