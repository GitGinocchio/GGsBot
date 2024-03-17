from colorama import Fore, Back
import sys
import os

clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')

F = Fore
B = Back

def erase_last_line():
    print('')
    sys.stdout.write('\033[F')
    sys.stdout.write('\033[K')
