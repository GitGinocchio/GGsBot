import nextcord
from nextcord import Embed,Color,utils,channel,Permissions,Interaction,slash_command
from nextcord.ext import commands
from pypresence import Presence
from config import CLIENT_ID
import random,asyncio,os


class RichPresence(commands.Cog):
    def __init__(self, bot : commands.Bot):
        super().__init__()
        self.bot = bot
        self.RPC
        RPC = Presence(client_id=str(CLIENT_ID))
        RPC.connect()
        RPC.update(details="Sto programmando", state="Utilizzando discord.py", large_image="large_image_key")

def setup(bot):
    bot.add_cog(RichPresence(bot))