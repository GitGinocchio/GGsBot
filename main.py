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

    print(f"🚀  {F.YELLOW}Initiating command module loading sequence...{F.RESET}")
    for i,category in enumerate(categories):
        print(f' │\n{" ├──" if not i == len(categories) - 1 else " └──" } 🔍  {F.BLUE}looking in commands.{category} for commands...{F.RESET}')
        for j,filename in enumerate(files:=os.listdir(f'./commands/{category}')):
            if filename.endswith('.py') and filename not in config['ignore_commands']:
                try:
                    Bot.load_extension(f'commands.{category}.{filename[:-3]}')
                except (commands.ExtensionFailed, commands.ExtensionAlreadyLoaded, commands.ExtensionNotFound, commands.InvalidSetupArguments) as e:
                    print(f' {"│" if not i == len(categories) - 1 else " " }    {"└──" if not j == len(files) - 1 else "├──" } ❌  {F.RED}Loading Extension Error: Cog {e.name}{F.RESET}\n │         {F.RED}{"└──" if not j == len(files) - 1 else "├──" }{e}{F.RESET}')
                except commands.NoEntryPointError as e:
                    pass # if no entry point found maybe is a file used by the main command file.
                else:
                    print(f' {"│" if not i == len(categories) - 1 else " " }    {"└──" if not j == len(files) - 1 else "├──" } 🎉  {F.MAGENTA}Successfully imported cog {filename} as commands.{category}.{filename[:-3]}{F.RESET}')
            elif filename in config['ignore_commands']: pass
            else:
                print(f' {"│" if not i == len(categories) - 1 else " " }    {"│" if not j == len(files) - 1 else "└──" } ⚠️  {F.YELLOW}Skipping non-py file: {filename}{F.RESET}')
load_commands()

if __name__ == '__main__':
    Bot.run(token=config['TOKEN'],reconnect=True)