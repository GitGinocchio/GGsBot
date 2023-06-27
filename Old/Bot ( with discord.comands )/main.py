import nextcord
from nextcord.ext import commands
from json_utils import json_utils
from config import TOKEN
import base64
import os

os.system('cls')
#data = json_utils(fp="./assets.json",indent=3)
#content = data.content()

intents = nextcord.Intents.all()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='/',intents=intents)

def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')
            
            if bot.get_cog(filename[:-3]):
                print(f' - {filename} imported correctly...')
            else:
                raise commands.ExtensionFailed()
load_cogs()

if __name__ == '__main__':
    bot.run(base64.urlsafe_b64decode(bytes.fromhex(TOKEN)).decode())