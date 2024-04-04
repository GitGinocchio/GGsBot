from typing import Literal
from utils.terminal import getlogger
import platform

logger = getlogger()

OS = platform.system()

ARCH = 'x64' if '64' in platform.architecture()[0] else 'x32'

def getsysteminfo():
    logger.debug(f'Architecture: {platform.architecture()}')
    logger.debug(f'Platform: {platform.platform()}')
    logger.debug(f'Machine: {platform.machine()}')
    logger.debug(f'Node: {platform.node()}')
    logger.debug(f'System: {platform.system()}')
    logger.debug(f'Python Version: {platform.python_version()}')
    logger.debug(f'Python Build: {platform.python_build()}')
    logger.debug(f'Python Revision: {platform.python_revision()}')