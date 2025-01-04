from utils.config import config
from colorama import Fore as F
from datetime import datetime
from enum import Enum
import subprocess
import inspect
import logging
import sys
import os
import re

def clear():
    """call the command for clearing the terminal depending on your system"""
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)

def erase():
    """Erase last terminal line (this should work on all systems)"""
    sys.stdout.write('\033[F')
    sys.stdout.write('\033[K')

class Level(Enum):
    DEBUG    = (logging.DEBUG,      F.GREEN          )
    INFO     = (logging.INFO,       F.WHITE          )
    WARNING  = (logging.WARNING,    F.LIGHTYELLOW_EX )
    ERROR    = (logging.ERROR,      F.YELLOW         )
    CRITICAL = (logging.CRITICAL,   F.LIGHTRED_EX    )
    FATAL    = (logging.FATAL,      F.RED            )


class CustomColorsFormatter(logging.Formatter):
    def format(self, record : logging.LogRecord):
        level = Level[record.levelname] if record.levelname in Level.__members__ else Level.INFO
        record.colored_name = f"{F.LIGHTMAGENTA_EX}[{record.name}]{F.RESET}"
        record.colored_msg = f": {level.value[1]}{record.msg}{F.RESET}"
        record.colored_levelname = f"{level.value[1]}[{record.levelname}]{F.RESET}"

        return super().format(record)


stream_formatter = CustomColorsFormatter(
    '[%(asctime)s] %(colored_name)s %(colored_levelname)s %(colored_msg)s',
    datefmt=config["logger"]["datefmt"]
)
file_formatter = logging.Formatter(
    '[%(asctime)s] [%(name)s] [%(levelname)s] : %(message)s',
    datefmt=config["logger"]["datefmt"]
)

stream = logging.StreamHandler(sys.stdout)
stream.setFormatter(stream_formatter)

if config["logger"]["tofile"]:
    logfile = logging.FileHandler(r"{}//{}.log".format(
        config["logger"]['dir'],
        datetime.now().strftime(config["logger"]["filename_datefmt"])),
        encoding="utf-8"
    )
    logfile.setFormatter(file_formatter)


default_level = Level[str_lvl] if (str_lvl:=config["logger"]["level"]) in Level.__members__ else Level.INFO


def getlogger(name : str = None, level : Level = None) -> logging.Logger:
    if name is None:
        match = re.match(r".*[\\/](.+?)(\.[^.]*$|$)", inspect.stack()[1].filename)

        if match:
            name = match.group(1)
        else:
            name = "unknown"

    logger = logging.getLogger(name)

    if level is not None:
        logger.setLevel(level[0])
    else:
        logger.setLevel(default_level.value[0])

    logger.addHandler(stream)

    if config["logger"]["tofile"]:
        logger.addHandler(logfile)
    
    return logger
