from colorama import Fore, Back
import sys
import os

F = Fore
B = Back


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def erase_last_line():
    print('')
    sys.stdout.write('\033[F')
    sys.stdout.write('\033[K')
