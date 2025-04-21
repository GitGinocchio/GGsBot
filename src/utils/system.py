from datetime import datetime, timezone
import subprocess
import platform
import psutil
import os

from utils.terminal import getlogger

logger = getlogger()

OS = platform.system()

ARCH = 'x64' if '64' in platform.architecture()[0] else 'x32'

def printsysteminfo():
    logger.debug(f'Current Working Directory: {os.getcwd()}')
    logger.debug(f'Architecture: {platform.architecture()} (arch: {ARCH})')
    logger.debug(f'Platform: {platform.platform()}')
    logger.debug(f'Machine: {platform.machine()}')
    logger.debug(f'Processor: {platform.processor()}')
    logger.debug(f'Node: {platform.node()}')
    logger.debug(f'System: {platform.system()} (os: {OS})')
    logger.debug(f'Libc Version: {platform.libc_ver()}')
    logger.debug(f'Python Version: {platform.python_version()}')
    logger.debug(f'Python Build: {platform.python_build()}')
    logger.debug(f'Python Revision: {platform.python_revision()}')

def get_psutil_stats():
    boot_time = datetime.now(timezone.utc) - datetime.fromtimestamp(psutil.boot_time(), timezone.utc)

    # Cpu
    cpu_count = {'physical': psutil.cpu_count(False), 'logical': psutil.cpu_count()}
    cpu_freqs = [{'current': freq.current, 'min': freq.min, 'max': freq.max} for freq in psutil.cpu_freq(True)]
    cpu_usage = { 'percpu' : psutil.cpu_percent(percpu=True), 'total' : psutil.cpu_percent()} 

    # Memory
    ram_usage = {'available': (memory:=psutil.virtual_memory()).available,'free' : memory.free,'percent' : memory.percent,'total' : memory.total,'used' : memory.used}

    # Disk
    disk_usage = { 'total' : (disk:=psutil.disk_usage('/')).total, 'used' : disk.used, 'free' : disk.free, 'percent' : disk.percent }

    # Swap
    swap_usage = { 'total' : (swap:=psutil.swap_memory()).total, 'used' : swap.used, 'free' : swap.free, 'percent' : swap.percent, 'sin' : swap.sin, 'sout' : swap.sout }

    status = {
        'boot_time' : boot_time.total_seconds(),
        'cpu' : {
            'count' : cpu_count,
            'freqs' : cpu_freqs,
            'usage' : cpu_usage
        },
        'memory' : ram_usage,
        'disk' : disk_usage,
        'swap' : swap_usage,
    }

    return status