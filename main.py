from nextcord.ext import commands
from utils.jsonfile import JsonFile
from utils.terminal import clear, F, B, erase_last_line
from config.intents import get
import nextcord
import asyncio
import time
import sys
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
                    print(f' {"│" if not i == len(categories) - 1 else " " }    {F.RED}{"└──" if not j == len(files) - 1 else "├──" } ❌  Loading Extension Error: Cog {e.name}{F.RESET}\n │         {F.RED}{"└──" if not j == len(files) - 1 else "├──" }{e}{F.RESET}')
                except commands.NoEntryPointError as e:
                    pass # if no entry point found maybe is a file used by the main command file.
                else:
                    print(f' {"│" if not i == len(categories) - 1 else " " }    {F.MAGENTA}{"└──" if not j == len(files) - 1 else "├──" } 🎉  Successfully imported cog {filename} as commands.{category}.{filename[:-3]}{F.RESET}')
            elif filename in config['ignore_commands']: pass
            else:
                print(f' {"│" if not i == len(categories) - 1 else " " }    {F.YELLOW}{"│" if not j == len(files) - 1 else "└──" } ⚠️  Skipping non-py file: {filename}{F.RESET}')
load_commands()

def run():
    print(f"\n🚀  {F.YELLOW}Initiating bot starting sequence...{F.RESET}")
    try:
        print(f"🔍  {F.BLUE}Starting bot...{F.RESET}")
        Bot.run(token=config['TOKEN'],reconnect=True)
    except nextcord.errors.HTTPException as e:
        print(f" └── ❌  {F.RED}An HTTPException occurred(status code: {e.status}){F.RESET}")
        match e.status:
            case 429:
                retry_after = e.response.headers['Retry-After']
                print(f"      {F.RED}├── ❌  Bot has been temporary-RateLimited from the Discord api's and the bot will not start!{F.RESET}")
                for i in range(0,int(retry_after)):
                    sys.stdout.write(f"\r      {F.RED}└── ⚠️  {F.YELLOW}Trying after {int(retry_after)-i} seconds...{F.RESET}")
                    time.sleep(1)
                    erase_last_line()
                print(f"🔍  {F.BLUE}Re-Starting bot after {retry_after} seconds...{F.RESET}")
                run()
            case _:
                print(f'      {F.RED}├── ❌  Unhandled HTTPException(code: {e.code}): {e.text}{F.RESET}')
                input('press any key to continue...')
        

if __name__ == '__main__':
    run()