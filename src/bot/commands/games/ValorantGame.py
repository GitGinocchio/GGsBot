from utils.terminal import getlogger
from nextcord.ext import commands
from utils.config import config
import valo_api
import nextcord
import requests 
import asyncio
import sys

logger = getlogger()

class ValorantGame(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot

def setup(bot : commands.Bot):
    bot.add_cog(ValorantGame(bot))