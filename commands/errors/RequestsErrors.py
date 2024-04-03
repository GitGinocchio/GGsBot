from nextcord import Embed,Color,Permissions
from nextcord.ext import commands
import datetime
import nextcord
import asyncio
import random
import time
import os



class RequestsErrors(commands.Cog):
    def __init__(self,bot : commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print('on_command_error',error)
        if isinstance(error, nextcord.HTTPException):
            if error.status == 429:
                retry_after = error.response.headers.get('Retry-After')
                if retry_after:
                    print(f"Rate limit hit, sleeping for {retry_after} seconds")
                    asyncio.sleep(int(retry_after))
                    # Qui potresti voler riprovare la tua richiesta o comando
                else:
                    print("Rate limit hit, but no Retry-After header available")
        else:
            print(f"Unhandled exception: {error}")

    

def setup(bot : commands.Bot):
    bot.add_cog(RequestsErrors(bot))
