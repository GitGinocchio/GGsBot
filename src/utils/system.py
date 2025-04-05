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
    logger.debug(f'Current Working Directory:       {os.getcwd()}')
    logger.debug(f'Architecture:                    {platform.architecture()} (arch: {ARCH})')
    logger.debug(f'Platform:                        {platform.platform()}')
    logger.debug(f'Machine:                         {platform.machine()}')
    logger.debug(f'Processor:                       {platform.processor()}')
    logger.debug(f'Node:                            {platform.node()}')
    logger.debug(f'System:                          {platform.system()} (os: {OS})')
    logger.debug(f'Libc Version:                    {platform.libc_ver()}')
    logger.debug(f'Python Version:                  {platform.python_version()}')
    logger.debug(f'Python Build:                    {platform.python_build()}')
    logger.debug(f'Python Revision:                 {platform.python_revision()}')

def get_top_stats():
    # Testing purposes on Windows with wsl
    command = f"{'wsl -e \"' if OS != "Linux" else ''}top -b -n 1{'\"' if OS != 'Linux' else ''}"
    top_output = subprocess.check_output(command, shell=True).decode()

    current_time : str = None
    uptime : str = None
    load_avg_1min : float = None
    load_avg_5min : float = None
    load_avg_15min : float = None
    users : str = None

    tasks : list[int] = []
    cpu_times : list[float] = []
    memory_usage : list[float] = []
    swap_usage : list[float] = []

    for i, line in enumerate(top_output.split('\n')):
        if i == 0:
            first_line_parsed = line.split('-', 1)[1].strip().split(',', 2)

            current_time, uptime = [piece.strip() for piece in first_line_parsed[0].split("up")]
            load_avg_1min, load_avg_5min, load_avg_15min = [float(piece.strip()) for piece in first_line_parsed[2].split(':', 1)[1].split(',', 2)]
            users = first_line_parsed[1].strip()
        if i == 1:
            tasks = [int(piece.strip().split(' ')[0]) for piece in line.split(':', 1)[1].split(',')]
        if i == 2:
            cpu_times = [float(piece.strip().split(' ')[0]) for piece in line.split(':', 1)[1].split(',')]
        if i == 3:
            memory_usage = [float(piece.strip().split(' ')[0]) for piece in line.split(':')[1].split(',')]
        if i == 4:
            swap_usage = [float(piece.strip().split(' ')[0]) for piece in line.split(':')[1].split(',')]

    return {
        'current_time' : current_time,
        'uptime' : uptime,
        'load_avg_1min' : load_avg_1min,
        'load_avg_5min' : load_avg_5min,
        'load_avg_15min' : load_avg_15min,
        'num_users' : users,
        
        'tasks' : { 'total' : tasks[0], 'running' : tasks[1], 'sleeping' : tasks[2],'stopped' : tasks[3], 'zombie' : tasks[4] },
        'cpu' : { 
            'user_cpu_time' : cpu_times[0],
            'system_cpu_time' : cpu_times[1],
            'nice_cpu_time' : cpu_times[2],
            'idle_cpu_time' : cpu_times[3],
            'wait_cpu_time' : cpu_times[4],
            'hi_cpu_time' : cpu_times[5],
            'si_cpu_time' : cpu_times[6],
            'steal_cpu_time' : cpu_times[7]
        },
        'memory' : {
            'total' : memory_usage[0],
            'free' : memory_usage[1],
            'used' : memory_usage[2],
            'buff/cache' : memory_usage[3],
        },
        'swap' : {
            'total' : swap_usage[0],
            'free' : swap_usage[1],
            'used' : swap_usage[2]
        }
    }

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