import nextcord
from nextcord.ext import commands
from config import TOKEN,APPLICATION_ID
import base64,os,asyncio
from datetime import datetime,timedelta
from jsonutils import jsonfile

def clear_terminal():
    os_name = os.name
    if os_name == 'nt': os.system('cls') # Windows
    else: os.system('clear')# Unix/Linux/Mac
clear_terminal()

intents = nextcord.Intents.all()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='/',intents=intents,application_id=APPLICATION_ID)

def load_cogs():
    ignore = ['jsonutils.py']

    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename not in ignore:
            print(f' - importing cog {filename} as cogs.{filename[:-3]}...')
            bot.load_extension(f'cogs.{filename[:-3]}')
        
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename not in ignore:
            if bot.get_cog(filename[:-3]):
                print(f' - {filename} imported correctly...')
            else:
                raise commands.ExtensionFailed()

load_cogs()
print('\n[ System messages... ]')

if __name__ == '__main__':
    if not bot.is_closed(): print(f'[{str(datetime.utcnow() + timedelta(hours=2))}] - WARNING: Another istance of bot is already running, waiting for it to finish... (this could use a lot of resources)')
    while not bot.is_closed(): pass
    print(f'[{str(datetime.utcnow() + timedelta(hours=2))}] - Starting bot...')
    bot.run(base64.urlsafe_b64decode(bytes.fromhex(TOKEN)).decode(),reconnect=True)
    #asyncio.run(bot.start(base64.urlsafe_b64decode(bytes.fromhex(TOKEN)).decode(),reconnect=True))