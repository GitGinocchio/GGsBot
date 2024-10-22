import os

for root, dirs, _ in os.walk('./data/guilds'):
    for dir in dirs:
        if os.path.isdir(guild:=os.path.join(root, dir)):
            os.system(f'rmdir /s /q "{guild}"')