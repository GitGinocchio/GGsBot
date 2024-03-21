from nextcord.ext import commands
from utils.jsonfile import JsonFile
from utils.terminal import clear, erase_last_line, getlogger
from config.intents import get
import nextcord
import asyncio
import time
import sys
import os


config = JsonFile('./config/config.jsonc')
logger = getlogger()

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



def run():
    logger.info("Starting bot...")
    load_commands()
    try:
        logger.info("Loggin in...")
        Bot.run(token=config['TOKEN'], reconnect=True)
    except nextcord.errors.HTTPException as e:
        logger.error(f"An HTTPException occurred (status code: {e.status})")
        match e.status:
            case 429:
                retry_after = e.response.headers['Retry-After']    
                logger.critical("Bot has been temporary-rate-limited from Discord's api and will not start.")
                for i in range(0, int(retry_after)):
                    logger.warning(f"Retrying after {int(retry_after)-i} seconds...")
                    time.sleep(1)
                    erase_last_line()
                logger.warning(f"Re-starting bot after {retry_after} seconds...")
                run()
            case _:
                logger.fatal(f"Unhandled HTTPException occurred (code: {e.code}): {e.text}")
                input('press any key to continue...')
    except Exception as e:
        logger.critical(f'Unhandled Exception occurred: {e}')
if __name__ == '__main__':
    run()
