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

from web.HTTPServer import HTTPServer
from utils.terminal import getlogger
from utils.config import config
from utils.db import Database

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