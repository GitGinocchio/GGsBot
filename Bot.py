from discord import Intents,Status,ActivityType,Activity,Member,Permissions
from discord.ext import commands
from discord.ext.tasks import loop
from time import sleep

TOKEN = "MTA5NDQxMjM3MTM5MDM3NDAyOQ.G7ARec.QB3g0K0m5G_n0GMxm6W-3B6jxzHn7oOFcDGMk4"
intents = Intents.all()
intents.message_content = True

#bot = Client(intents=intents)
#channels = [channel for channel in bot.get_all_channels()]
#print(channels)


bot = commands.Bot(command_prefix=('/'),status=Status.online, activity=Activity(type=ActivityType.playing, name="Setting up!", intents = intents),intents=intents)

channel_id = 1069733888815026250



@bot.command()
async def c(ctx):
    await ctx.send("hai attivato un comando!")


@bot.command()
async def clear(ctx,amount=10000):
    await ctx.channel.purge(limit=amount)

@bot.command()
@commands.has_permissions()
async def ban(ctx, member: Member,*,reason=None):
    await member.ban(reason=reason)



@bot.event
async def on_ready():
    print("Ready!")
    #channel = bot.get_channel(channel_id)
    #await channel.send("Ready!")


@loop(minutes=10)
async def every_ten_minutes():
    pass


#@bot.event
#async def on_message(message):
    #author = message.author
    #text = message.content
    #channel = message.channel
    #if not author == bot.user:
        #pass
        #await channel.send(f"Ciao {author.name}")

        #if text.startswith("/command") and text.split()[0] == "/command":
            #splitted_text = text.split()
            #print(splitted_text)
            #await channel.send(f"Questo e' un comando!")




bot.run(TOKEN,reconnect=True)
