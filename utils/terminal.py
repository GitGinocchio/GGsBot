from utils.jsonfile import JsonFile
from colorama import Fore, Back
from datetime import datetime
import inspect
import logging
import sys
import os

config = JsonFile('./config/config.jsonc')

F = Fore
B = Back


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def erase_last_line():
    print('')
    sys.stdout.write('\033[F')
    sys.stdout.write('\033[K')


levels = {
    "DEBUG": (logging.DEBUG, F.GREEN),
    "INFO": (logging.INFO, F.WHITE),
    "WARNING": (logging.WARNING, F.LIGHTYELLOW_EX),
    "ERROR": (logging.ERROR, F.YELLOW),
    "CRITICAL": (logging.CRITICAL, F.LIGHTRED_EX),
    "FATAL": (logging.FATAL, F.RED)
}


class CustomColorsFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord):
        color = levels.get(record.levelname, F.WHITE)
        record.name = f"{F.LIGHTMAGENTA_EX}[{record.name}]{F.RESET}"
        record.msg = f": {color[1]}{record.msg}{F.RESET}"
        record.levelname = f"{color[1]}[{record.levelname}]{F.RESET}"

        return super().format(record)


formatter = CustomColorsFormatter(
    '[%(asctime)s] %(name)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

stream = logging.StreamHandler(sys.stdout)
stream.setFormatter(formatter)

if config["logtofile"]:
    logfile = logging.FileHandler("{}/{}".format(
        config['logdir'],
        datetime.now().strftime("%Y-%m-%d %H:%M")))
    logfile.setFormatter(formatter)

level = levels.get(config["loglevel"], logging.INFO)


def getlogger():
    filename = inspect.stack()[1].filename.split('/')[-1].split('.')[0]
    logger = logging.getLogger("{}.{}".format(config['loggername'], filename))

    if isinstance(level, tuple):
        logger.setLevel(level[0])
    else:
        logger.setLevel(level)

    logger.addHandler(stream)

    if config["logtofile"]:
        logger.addHandler(logfile)
    return logger
