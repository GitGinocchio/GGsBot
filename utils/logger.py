from utils.jsonfile import JsonFile
from datetime import datetime
from os import path, getcwd, chdir
import logging
import sys

config = JsonFile('./config/config.jsonc')

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filemode='a',
    stream=sys.stdout)
"""
filename=path.join(config['logdir'],f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.txt'),
"""

logger = logging.getLogger(config["loggername"])

handler = logging.FileHandler('bot.log', 'a')
logger.addHandler(handler)