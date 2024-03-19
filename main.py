from nextcord.ext import commands
from utils.jsonfile import JsonFile
from utils.terminal import clear, F, B, erase_last_line
from utils.logger import logger
from config.intents import get
import nextcord
import asyncio
import time
import sys
import os

config = JsonFile('./config/config.jsonc')

Bot = commands.Bot(intents=get(),
                   command_prefix=config['COMMAND_PREFIX'],
                   application_id=config['APPLICATION_ID'])
clear()


def load_commands():
    categories = [
        c for c in os.listdir('./commands')
        if c not in config['ignore_categories']
    ]
    logger.info('Loading commands...')
    for i, category in enumerate(categories):
        logger.info(f'Looking in commands.{category}...')
        for j, filename in enumerate(
                files := os.listdir(f'./commands/{category}')):
            if filename.endswith(
                    '.py') and filename not in config['ignore_commands']:
                try:
                    Bot.load_extension(f'commands.{category}.{filename[:-3]}')
                except (commands.ExtensionFailed,
                        commands.ExtensionAlreadyLoaded,
                        commands.ExtensionNotFound,
                        commands.InvalidSetupArguments) as e:
                    logger.critical(
                        f'Loading command error: Cog {e.name} message: {e}')
                except commands.NoEntryPointError as e:
                    pass  # if no entry point found maybe is a file used by the main command file.
                else:
                    logger.info(
                        f'Succesfully imported command {filename[:-3]} as commands.{category}.{filename[:-3]}'
                    )
            elif filename in config['ignore_commands']:
                pass
            else:
                logger.warning(f'Skipping non-py file: {filename}')


load_commands()


def run():
    print(f"\n🚀  {F.YELLOW}Initiating bot starting sequence...{F.RESET}")
    try:
        print(f"🔍  {F.BLUE}Starting bot...{F.RESET}")
        Bot.run(token=config['TOKEN'], reconnect=True)
    except nextcord.errors.HTTPException as e:
        print(
            f" └── ❌  {F.RED}An HTTPException occurred(status code: {e.status}){F.RESET}"
        )
        match e.status:
            case 429:
                retry_after = e.response.headers['Retry-After']
                print(
                    f"      {F.RED}├── ❌  Bot has been temporary-RateLimited from the Discord api's and the bot will not start!{F.RESET}"
                )
                for i in range(0, int(retry_after)):
                    sys.stdout.write(
                        f"\r      {F.RED}└── ⚠️  {F.YELLOW}Trying after {int(retry_after)-i} seconds...{F.RESET}"
                    )
                    time.sleep(1)
                    erase_last_line()
                print(
                    f"🔍  {F.BLUE}Re-Starting bot after {retry_after} seconds...{F.RESET}"
                )
                run()
            case _:
                print(
                    f'      {F.RED}├── ❌  Unhandled HTTPException(code: {e.code}): {e.text}{F.RESET}'
                )
                input('press any key to continue...')


if __name__ == '__main__':
    run()
