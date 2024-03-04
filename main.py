from nextcord.ext import commands
from utils.jsonfile import JsonFile
from utils.terminal import clear, F, B
from config.intents import get
import os

config = JsonFile('./config/config.jsonc')

Bot = commands.Bot(intents=get(),command_prefix=config['COMMAND_PREFIX'],application_id=config['APPLICATION_ID'])

clear()
def load_commands():
    categories = [c for c in os.listdir('./commands') if c not in config['ignore_categories']]

    for category in categories:
        print(f' + 🔍 {F.BLUE}looking in commands.{category} for commands...{F.RESET}')
        for filename in os.listdir(f'./commands/{category}'):
            if filename.endswith('.py') and filename not in config['ignore_commands']:
                try:
                    print(f' | - ✅ {F.LIGHTGREEN_EX}Importing cog {filename} as commands.{category}.{filename[:-3]}{F.RESET}...')
                    Bot.load_extension(f'commands.{category}.{filename[:-3]}')
                except (commands.ExtensionFailed,
                    commands.NoEntryPointError,
                    commands.ExtensionAlreadyLoaded,
                    commands.ExtensionNotFound,
                    commands.InvalidSetupArguments) as e:
                    print(f' | - ❌ {F.RED}Loading Extension Error: Cog {e.name}{F.RESET}\n{e}')
                else:
                    print(f' | - 🎉 {F.GREEN}Successfully imported cog {filename} as commands.{category}.{filename[:-3]}{F.RESET}')
            elif filename in config['ignore_commands']: pass
            else:
                print(f' | - ⚠️ {F.YELLOW}(Warning) Skipping non-py file: {filename}{F.RESET}')
load_commands()

if __name__ == '__main__':
    Bot.run(token=config['TOKEN'],reconnect=True)
