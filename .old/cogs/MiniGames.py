import nextcord
from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands,tasks
import random,asyncio,os
from datetime import datetime, timedelta



class MiniGames(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(MiniGames(bot))
