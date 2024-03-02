from nextcord import Intents

def get():
    intents = Intents.all()
    intents.members = True
    intents.message_content = True
    intents.guilds = True
    return intents