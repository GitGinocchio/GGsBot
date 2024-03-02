from nextcord.ext import commands
from utils.jsonfile import JsonFile
from config.intents import get
import nextcord
import os

config = JsonFile('./config/config.jsonc')

Bot = commands.Bot(intents=get(),command_prefix=config['COMMAND_PREFIX'],application_id=config['APPLICATION_ID'])

def load_commands():
    categories = [c for c in os.listdir('./commands') if c not in config['ignore_categories']]

    for category in categories:
        print(f' + looking in commands.{category} for commands...')
        for filename in os.listdir(f'./commands/{category}'):
            if filename.endswith('.py') and filename not in config['ignore_commands']:
                try:
                    print(f' | - importing cog {filename} as commands.{category}.{filename[:-3]}...')
                    Bot.load_extension(f'commands.{category}.{filename[:-3]}')
                except (commands.ExtensionFailed,
                    commands.NoEntryPointError,
                    commands.ExtensionAlreadyLoaded,
                    commands.ExtensionNotFound,
                    commands.InvalidSetupArguments) as e:
                    print(f' | - Loading Extension Error:',f'Cog {e.name}',e)
                else:
                    print(f' | - Successfully imported cog {filename} as commands.{category}.{filename[:-3]}')
            else:
                print(' | - (Warning) Skipping non-py file:',filename)
load_commands()

if __name__ == '__main__':
    Bot.run(token=config['TOKEN'],reconnect=True)
