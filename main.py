import nextcord
from nextcord.ext import commands
from config import TOKEN,APPLICATION_ID
import base64,os,asyncio
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
print('-------------------------[ Logs ]-------------------------')

if __name__ == '__main__':
    #bot.run(base64.urlsafe_b64decode(bytes.fromhex(TOKEN)).decode())
    asyncio.run(bot.start(base64.urlsafe_b64decode(bytes.fromhex(TOKEN)).decode(),reconnect=True))