import os

def clear():
    if os.name == 'nt': 
        os.system('cls') # Windows
    else: 
        os.system('clear')# Unix/Linux/Mac