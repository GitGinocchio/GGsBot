from discord import Intents,Status,ActivityType,Activity,Member,Permissions,Client, Embed, Color,DiscordException,Emoji
from discord.ext import commands
from discord.ext.tasks import loop
from datetime import datetime
import json5 as json

class json_utils:
    def __init__(self,fp: str = None,*,indent: int = 3):
        self.fp = fp
        self.indent = indent
    
    def content(self):
        with open(self.fp, 'r') as json_file:
            content = json.load(json_file)
            return content

    def save_to_file(self,content,indent: int = 3):
        with open(self.fp, 'w') as json_file:
            json.dump(content,json_file,indent=indent)



data = json_utils(fp="./assets.json",indent=3)
content = data.content()

#data.save_to_file(content,3)

intents = Intents.all()
intents.message_content = True

bot = Client(intents=intents,status=Status.online, activity=Activity(type=ActivityType.listening, name="...", intents=intents))
SENT_MESSAGE_IDS = []


@bot.event
async def on_ready():
    print("Ready!")
    #channel = bot.get_channel(channel_id)
    #await channel.send("Ready!")


@loop(minutes=10)
async def every_ten_minutes():
    pass


@bot.event
async def on_message(message):
    author = message.author
    text = message.content
    channel = message.channel

    if not author == bot.user:
        #await channel.send(f"Ciao {author.name}")

        if text.startswith("//SEND_RULES_MESSAGE") and text.split()[0] == "//SEND_RULES_MESSAGE":
            await message.delete()
            Rules = """
 - Tratta ogni persona con rispetto. Non sarà tollerato alcun tipo di molestia, persecuzione, sessismo, razzismo o incitamento all'odio.

 - Se noti qualcosa che va contro alle regole o non ti fa sentire al sicuro, informa lo staff. Vogliamo che questo server sia un luogo accogliente!

 - Niente contenuti osceni o soggetti a limiti di età. Ciò include testi, immagini o link contenenti nudità, sesso, violenza brutale o altri contenuti esplicitamente scioccanti.

 - Niente spam o autopromozione (inviti a server, pubblicità, ecc.) senza il permesso di un membro dello staff. Ciò include inviare messaggi diretti ai membri.
"""
            embed = Embed(title="Rules",description=Rules,color=Color.green())
            sent = await channel.send(embed=embed)
            await sent.add_reaction("✅")

        if text.startswith("//SEND_VERIFY_MESSAGE") and text.split()[0] == "//SEND_VERIFY_MESSAGE":
            await message.delete()
            embed = Embed(title="",description="",color=Color.green())

        #----------------------------------------------------------------------------------------------------------------

        if text.startswith("/help") or text.startswith("/commands") and text.split()[0] == "/help" or text.split()[0] == "/commands" and text.endswith("/help") or text.endswith("/commands"):
            await message.delete()
            description = f"""
**commands without arguments**
`/help`,`/commands` - shows all the available commands

**commands with arguments**
- ( ) : optional arguments
- [ ] : required arguments


`/clear` (messages) - clear the amount of messages in the channel (default: 100).

`/poll` [title] // [choices] // (description) // (time limit) - create a poll message in the channel 
es. `/poll Superpowers // (1️⃣,invisibility),(2️⃣,Super strength),(3️⃣,flight),(4️⃣,Teleportation) // if you could have any superpower, wich one would you choose?`
 
"""
            embed = Embed(title="All commands available:",description=description,color=Color.green())
            await channel.send(embed=embed)

        if text.startswith("/poll") and text.split()[0] == "/poll":
            try:
                if "//" in text:
                    splitted = text.split('//')
                    title = splitted[0].replace(text.split()[0],'').strip()
                    choices = [s.strip().replace('(','').replace(')','') for s in splitted[1].strip().split(',(')]
                    parsed_choices = " \n".join(choices).replace(',',' - ')
                    emojis = [word.split(',')[0] for word in choices]
                    description = splitted[2].strip()


                Embed_message = f"""
    **{description}**

    {parsed_choices}
    """
                embed = Embed(title=f"POLL: {title}",description=Embed_message,color=Color.green())
                sent = await channel.send(embed=embed)
                
                SENT_MESSAGE_IDS.append(sent.id)

                for emoji in emojis:
                    try:
                        print(emoji)
                        await sent.add_reaction(emoji)
                    except:pass
            except DiscordException as e:
                print(e)
                await channel.send(embed=Embed(title="Error:",description="You must use '//' to correctly separate the kwargs arguments in the message",color=Color.red()))
            except Exception as e:
                print(e)

        if text.startswith("/clear") and text.split()[0] == "/clear":
            await message.delete()
            if len(text.split()) == 2 and text.split()[1].isdecimal():
                await channel.purge(limit=int(text.split()[1]))
            elif len(text.split()) == 1:
                await channel.purge(limit=100)
            elif len(text.split()) > 2:
                await channel.send(embed=Embed(title="Error:",description="Invalid number of arguments. Expected exactly 1 argument.",color=Color.red()))
            else:
                await channel.send(embed=Embed(title="Error:",description="Invalid type of arguments. Expected type integer.",color=Color.red()))

        if text.startswith("{}") and text.split()[0] == "{}":
            pass


@bot.event
async def on_raw_reaction__add(payload):
    global SENT_MESSAGE_IDS

    #Get the message object
    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    print(channel)
    print(message)


    #Get the member object
    guild = message.guild
    member = await guild.fetch_member(payload.user_id)

    for message_id in SENT_MESSAGE_IDS:
        if message_id == message.id:
            pass
            #if payload.emoji.name not in POLL_OPTION_EMOJIS:
                #pass



bot.run(content["TOKEN"],reconnect=True)