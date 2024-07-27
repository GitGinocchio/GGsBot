from utils.terminal import clear, erase, getlogger,F
from nextcord.ext import commands
from utils.config import config
from utils.intents import getintents
from utils.system import getsysteminfo
from dotenv import load_dotenv
import nextcord
import time
import os

clear()
getsysteminfo()
logger = getlogger()

load_dotenv()

Bot = commands.Bot(intents=getintents(),command_prefix=config['COMMAND_PREFIX'],application_id=os.environ['APPLICATION_ID'])

def load_commands():
    categories = [c for c in os.listdir('./commands') if c not in config['ignore_categories']]
    logger.info('Loading commands...')
    for category in categories:
        logger.info(f'Looking in commands.{category}...')
        for filename in os.listdir(f'./commands/{category}'):
            if filename.endswith('.py') and filename not in config['ignore_files']:
                try:
                    Bot.load_extension(f'commands.{category}.{filename[:-3]}')
                except (commands.ExtensionFailed,
                        commands.ExtensionAlreadyLoaded,
                        commands.ExtensionNotFound,
                        commands.InvalidSetupArguments) as e:
                    logger.critical(f'Loading command error: Cog {e.name} message: \n{e}')
                except commands.NoEntryPointError as e:
                    pass  # if no entry point found maybe is a file used by the main command file.
                else:
                    logger.info(f'Imported command {F.LIGHTMAGENTA_EX}{category}.{filename[:-3]}{F.RESET}')
            elif filename in config['ignore_files']:
                pass
            else:
                logger.warning(f'Skipping non-py file: \'{filename}\'')

def run():
    logger.info("Starting bot...")
    load_commands()
    try:
        logger.info("Loggin in...")
        Bot.run(token=os.environ['TOKEN'], reconnect=True)
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
