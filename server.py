from aiohttp import web
import asyncio

async def handle(request):
	return web.Response(text="Hello, world")

app = web.Application()
app.router.add_get('/', handle)

async def init():
	runner = web.AppRunner(app)
	await runner.setup()
	site = web.TCPSite(runner, '0.0.0.0', 80)
	await site.start()

# Metodo per fare run del server
def run_http_server():
	loop = asyncio.get_event_loop()
	loop.run_until_complete(init())