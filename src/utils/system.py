from utils.terminal import getlogger
import platform
import os

logger = getlogger()

OS = platform.system()

ARCH = 'x64' if '64' in platform.architecture()[0] else 'x32'

def getsysteminfo():
    logger.debug(f'Current Working Directory: {os.getcwd()}')
    logger.debug(f'Architecture: {platform.architecture()}')
    logger.debug(f'Platform: {platform.platform()}')
    logger.debug(f'Machine: {platform.machine()}')
    logger.debug(f'Processor: {platform.processor()}')
    logger.debug(f'Node: {platform.node()}')
    logger.debug(f'System: {platform.system()}')
    logger.debug(f'Libc Version: {platform.libc_ver()}')
    logger.debug(f'Python Version: {platform.python_version()}')
    logger.debug(f'Python Build: {platform.python_build()}')
    logger.debug(f'Python Revision: {platform.python_revision()}')
