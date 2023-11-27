from nextcord.ext import commands
import aiohttp
from aiohttp import web


class HTTPListener(commands.Cog):
    def __init__(self, bot : commands.Bot):
        super().__init__()
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        app = web.Application()
        app.router.add_get('/', handle_http_request)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'free.daki.cc', 4612)  # Sostituisci con la porta desiderata
        await site.start()

async def handle_http_request(request):
    # Aggiungi qui la logica per gestire la richiesta HTTP
    print(request)
    return web.Response(text='Richiesta HTTP ricevuta e gestita dal bot Discord.')



def setup(bot):
    bot.add_cog(HTTPListener(bot))