import nextcord
from nextcord import Embed,Color,utils,channel,Permissions,Interaction,slash_command
from nextcord.ext import commands
from pypresence import Presence,Client
from config import CLIENT_ID,TOKEN
import random,asyncio,os,base64



class RichPresence(commands.Cog):
    def __init__(self, bot : commands.Bot):
        super().__init__()
        self.bot = bot
        #self.RPClient = Client(client_id=f"{CLIENT_ID}",pipe=0)
        #self.RPClient.start()
        #self.RPClient.authorize(client_id=f"{CLIENT_ID}",scopes=['rpc.activities.write'])\

        self.RPC = Presence(client_id=f"{CLIENT_ID}")
        self.RPC.connect()
        self.RPC.update(details="Sto programmando", state="Utilizzando discord.py", large_image="large_image_key")


def setup(bot):
    bot.add_cog(RichPresence(bot))