from nextcord.ext import commands
from dotenv import load_dotenv
import traceback
import nextcord
import asyncio
import time
import os

load_dotenv('./config/.env', verbose=True)

from utils.db import Database
from utils.terminal import clear, erase, getlogger,F
from utils.intents import getintents
from utils.system import getsysteminfo
from utils.config import \
    APPLICATION_ID,      \
    DEV_APPLICATION_ID,  \
    DEVELOPER_ID,        \
    DEV_TOKEN,           \
    TOKEN,               \
    config

clear()
getsysteminfo()
logger = getlogger()
intents = getintents()

Bot = commands.Bot(
    intents=intents,
    command_prefix=config['COMMAND_PREFIX'],
    application_id=DEV_APPLICATION_ID if (config['logger']['level'] == 'DEBUG' and DEV_APPLICATION_ID) else APPLICATION_ID,
    owner_id=DEVELOPER_ID
)

Bot.loop.set_debug(True if config['logger']['level'] == 'DEBUG' else False)

db = Database(loop=Bot.loop)

def load_commands():
    categories = [c for c in os.listdir('./src/commands') if c not in config['ignore_categories']]
    logger.info('Loading extensions...')
    for category in categories:
        #logger.info(f'Looking in commands.{category}...')
        for filename in os.listdir(f'./src/commands/{category}'):
            if filename.endswith('.py') and filename not in config['ignore_files']:
                try:
                    Bot.load_extension(f'commands.{category}.{filename[:-3]}')
                except (commands.ExtensionAlreadyLoaded,
                        commands.ExtensionNotFound,
                        commands.InvalidSetupArguments) as e:
                    logger.critical(f'Loading command error: Cog {e.name} message: \n{traceback.format_exc()}')
                except commands.NoEntryPointError as e:
                    continue  # if no entry point found maybe is a file used by the main command file.
                except commands.ExtensionFailed as e:
                    logger.warning(f"Extension {e.name} failed to load: \n{traceback.format_exc()}")
                else:
                    logger.info(f'Imported extension {F.LIGHTMAGENTA_EX}{category}.{filename[:-3]}{F.RESET}')

            elif filename in config['ignore_files']:
                continue
            else:
                logger.warning(f'Skipping non-py file: \'{filename}\'')

def run():
    logger.info("Starting bot...")
    load_commands()
    try:
        logger.info("Loggin in...")
        Bot.run(token=DEV_TOKEN if (config['logger']['level'] == 'DEBUG' and DEV_TOKEN) else TOKEN, reconnect=True)
    except nextcord.errors.HTTPException as e:
        logger.error(f"An HTTPException occurred (status code: {e.status})")
        match e.status:
            case 429:
                retry_after = e.response.headers['Retry-After']    
                logger.critical("Bot has been temporary-rate-limited from Discord's api and will not start.")
                for i in range(0, int(retry_after)):
                    logger.warning(f"Retrying after {int(retry_after)-i} seconds...")
                    time.sleep(1)
                    erase()
                logger.warning(f"Re-starting bot after {retry_after} seconds...")
                run()
            case _:
                logger.fatal(f"Unhandled HTTPException occurred (code: {e.code}): {e.text}")
                input('press any key to continue...')
    except Exception as e:
        logger.critical(f'Unhandled Exception occurred: {e}')

if __name__ == '__main__':
    run()
