from discord import Intents,Status,ActivityType,Activity,Member,Permissions,Client, Embed, Color,DiscordException,Emoji,utils
from discord.ext.tasks import loop
from datetime import datetime
import asyncio
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

intents = Intents.all()
intents.message_content = True

bot = Client(intents=intents,status=Status.online, activity=Activity(type=ActivityType.listening, name="...", intents=intents))
SENT_MESSAGE_IDS = []
CREATED_CHANNELS = {}

@bot.event
async def on_ready():
    print("Ready!")
    #channel = bot.get_channel(channel_id)
    #await channel.send("Ready!")

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel  # Ottieni il canale predefinito per i messaggi di benvenuto
    if channel is not None:
        message = f'Ciao {member.mention}, benvenuto nel server!'
        await channel.send(message)

@loop(minutes=10)
async def every_ten_minutes():
    pass

@bot.event
async def on_message(message):
    author = message.author
    channel = message.channel
    text = message.content
    roles = [role.name for role in author.roles]
    permissions = channel.permissions_for(author)

    #os.system('cls')
    print('---------------------------------------------------------------')
    print(f"author: {[author]}")
    print(f'roles: {[roles]}')
    print(f'permissions: {[permissions]}')
    print(f"text: {[text]}")
    print(f"channel: {[channel]}")

    try:
        if not author == bot.user:
            #await channel.send(f"Ciao {author.name}")

            if text.startswith("/help") or text.startswith("/commands") and text.split()[0] == "/help" or text.split()[0] == "/commands" and text.endswith("/help") or text.endswith("/commands"):
                command_roles = ['@everyone'] #'astro'
                command_permissions = [] #Permissions(administrator=True),Permissions(manage_messages=True)
                assert any(channel.permissions_for(author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in roles), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {['administrator','manage_messages']}
                
                """
                await message.delete()
                description = f"""
    **commands without arguments**
    `/help`,`/commands` - shows all the available commands

    **commands with arguments**
    - ( ) : optional arguments\n
    - [ ] : required arguments


    `/clear` (messages) - clear the amount of messages in the channel (default: 100).

    `/createvc` [channel name [str]] (max users [[int] - default: no-limit)  - create a voice channel with if specified a max user limit.
    
    """
                embed = Embed(title="All commands available:",description=description,color=Color.green())
                await channel.send(embed=embed)

            elif text.startswith("/clear") and text.split()[0] == "/clear":
                command_roles = ['astro']
                command_permissions = [Permissions(administrator=True),Permissions(manage_messages=True)]

                assert any(channel.permissions_for(author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in roles), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {['administrator','manage_messages']}
                
                """
    
                if len(text.split()) == 2 and text.split()[1].isdecimal():
                    await channel.send(embed=Embed(title="Info:",description=f"{int(text.split()[1])} messages will be deleted.",color=Color.green()))
                    await message.delete()
                    await channel.purge(limit=int(text.split()[1]))
                elif len(text.split()) == 1:
                    await channel.send(embed=Embed(title="Info:",description="100 messages will be deleted.",color=Color.green()))
                    await message.delete()
                    await channel.purge(limit=100)
                elif len(text.split()) > 2:
                    await message.delete()
                    await channel.send(embed=Embed(title="Error:",description="Invalid number of arguments. Expected exactly 1 argument.",color=Color.red()))
                else:
                    await message.delete()
                    await channel.send(embed=Embed(title="Error:",description="Invalid type of arguments. Expected type integer.",color=Color.red()))

            elif text.startswith("/createvc") and text.split()[0] == "/createvc":
                command_roles = ['@everyone'] #'astro'
                command_permissions = [] #Permissions(administrator=True),Permissions(manage_messages=True)
                assert any(channel.permissions_for(author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in roles), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {[]} #'administrator','manage_messages'
                
                """

                try:
                    splitted_params = text.split()[1:]
                    if len(splitted_params) == 1:
                        channel_name = splitted_params[0]
                        vocal_channel = await message.guild.create_voice_channel(channel_name,category=utils.get(message.guild.categories, id=1122912835962425397))
                        await channel.send(embed=Embed(title="Info:",description=f"Canale vocale {vocal_channel.mention} creato con successo!",color=Color.green()))

                        task = asyncio.create_task(delete_channel_after_timeout(vocal_channel))
                        CREATED_CHANNELS[vocal_channel.id] = {'text_channel' : channel,'author': author,'task' : task}
                    elif len(splitted_params) == 2:
                        assert splitted_params[1].isdecimal(), 'Invalid type of arguments. Expected type integer.'
                        
                        channel_name = splitted_params[0]
                        max_users = int(splitted_params[1])
                        vocal_channel = await message.guild.create_voice_channel(channel_name,category=utils.get(message.guild.categories, id=1122912835962425397))
                        await vocal_channel.edit(user_limit=max_users)
                        await channel.send(embed=Embed(title="Info:",description=f"Canale vocale {vocal_channel.mention} creato con successo con un limite di {max_users} utenti!",color=Color.green()))

                        task = asyncio.create_task(delete_channel_after_timeout(vocal_channel))
                        CREATED_CHANNELS[vocal_channel.id] = {'text_channel' : channel,'author': author,'task' : task}
                except AssertionError as e:
                    await channel.send(embed=Embed(title="Error:",description=e,color=Color.red()))

            elif text.startswith("/change color") and text.split()[0] == "/change color":
                command_roles = []
                command_permissions = []
                assert any(channel.permissions_for(author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in roles), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {['administrator','manage_messages']}
                
                """
                
                try:
                    pass
                except AssertionError as e: pass

            elif text.startswith("{}") and text.split()[0] == "{}":
                try:
                    pass
                except AssertionError as e: 
                    pass
            

    except AssertionError as e:
        await channel.send(embed=Embed(title="Error:",description=e,color=Color.red()))
    except Exception as e:
        print(f"Error: {e}")
    finally: pass












@bot.event
async def on_voice_state_update(member, before, after):
    print(member,before.channel.name if before.channel is not None else None,after.channel.name if after.channel is not None else None)

    if before.channel is not None and before.channel.id in CREATED_CHANNELS:
        task = asyncio.create_task(delete_channel_after_timeout(before.channel))
        CREATED_CHANNELS[before.channel.id]['task'] = task

async def delete_channel_after_timeout(channel):
    await asyncio.sleep(120)

    if channel.id in CREATED_CHANNELS and len(channel.members) == 0:
        await CREATED_CHANNELS[channel.id]['text_channel'].send(embed=Embed(title="Info:",description=f"{CREATED_CHANNELS[channel.id]['author'].mention} Nel canale vocale \'#{channel.name}\' sono passati 5 minuti senza qualcuno al suo interno, il canale e' stato eliminato.",color=Color.green()))
        await channel.delete()
        del CREATED_CHANNELS[channel.id]

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