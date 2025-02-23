from nextcord.ext.commands import Bot, Cog
from aiohttp.web import \
    Application,        \
    AppRunner,          \
    Response,           \
    Request,            \
    TCPSite
from datetime import datetime, timezone
import psutil
import json
import ssl

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
        self.app.router.add_get('/tos', self.tos)
        self.app.router.add_get('/api/status', self.api_status)

    async def index(self, request : Request):
        return Response(text="Hello World!", content_type="text/plain")
    
    async def tos(self, request : Request):
        return Response(text="Terms of Service", content_type="text/plain")

        self.app.router.add_get('/api/status', self.api_status)

    async def index(self, request : Request):
        return Response(text="Hello World!", content_type="text/plain")

    async def api_status(self, request : Request):
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
                'latency' : self.bot.latency
            }
        }

        return Response(text=json.dumps(status), content_type="application/json")

    @Cog.listener()
    async def on_ready(self):
        try:
            runner = AppRunner(self.app)
            await runner.setup()
            site = TCPSite(runner, self.address, self.port)
            await site.start()
            logger.info(f"HTTP Server started on {self.protocol}://{self.address}:{self.port}")
        except Exception as e:
            raise e



def setup(bot : Bot):
    bot.add_cog(HTTPServer(bot))