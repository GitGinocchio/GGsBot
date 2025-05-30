from argparse import ArgumentParser, Namespace
from nextcord.ext import commands
from dotenv import load_dotenv
import traceback
import nextcord
import asyncio
import time

load_dotenv('./config/.env', verbose=True)

from utils.db import Database
from utils.terminal import clear, erase, getlogger
from utils.intents import getintents
from utils.system import printsysteminfo
from utils.commons import load_commands
from utils.config import \
    APPLICATION_ID,      \
    DEV_APPLICATION_ID,  \
    DEVELOPER_ID,        \
    DEV_TOKEN,           \
    TOKEN,               \
    config,              \
    show_paths

logger = getlogger()

clear()
printsysteminfo()
show_paths(logger)



def run(args : Namespace):
    intents = getintents(config.get('INTENTS', None))

    bot = commands.Bot(
        intents=intents,
        command_prefix=config['COMMAND_PREFIX'],
        application_id=DEV_APPLICATION_ID if (config['logger']['level'] == 'DEBUG' and DEV_APPLICATION_ID) else APPLICATION_ID,
        owner_id=DEVELOPER_ID
    )

    bot.loop.set_debug(True if config['logger']['level'] == 'DEBUG' else False)

    db = Database(loop=bot.loop)

    logger.info("Starting bot...")

    load_commands(bot, logger, ignore_categories=['web'] if args.bot else [])

    try:
        logger.info("Loggin in...")
        bot.run(token=DEV_TOKEN if (config['logger']['level'] == 'DEBUG' and DEV_TOKEN) else TOKEN, reconnect=True)
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
                logger.fatal(f"Unhandled HTTPException occurred (code: {e.code}): {traceback.format_exc()}")
                input('press any key to continue...')

    except Exception as e:
        logger.critical(f'Unhandled Exception occurred: {traceback.format_exc()}')

def run_webserver_only(args : Namespace):
    from web.HTTPServer import HTTPServer

    server = HTTPServer(
        address=args.address, 
        protocol=args.proto, 
        port=args.port,
        debug=args.debug
    )

    asyncio.run(server.run())

def main():

    parser = ArgumentParser(
        description="GGsBot command line interface"
    )

    #parser.add_argument('-v', '--version', action='store_true', help='Show the version of GGsBot')
    parser.add_argument('--bot',        '-b',       action='store_true', help="Run only the discord bot")
    parser.add_argument('--web',        '-w',       action='store_true', help="Run only the web server")
    parser.add_argument('--address',    '-a',       type=str, default='127.0.0.1', help="Address to use for the web server")
    parser.add_argument('--port',       '-po',      type=int, default=8080, help="Port to use for the web server")
    parser.add_argument('--proto',      '-pr',      type=str, default='http', help="Protocol to use for the web server")
    parser.add_argument('--debug',      '-d',       action='store_true', help="Enable debug mode")

    args = parser.parse_args()

    if args.web:
        run_webserver_only(args)
    else:
        run(args)

if __name__ == '__main__':
    main()
