import nextcord
from nextcord import Embed,Color,utils
from nextcord.ext import commands
import random,asyncio



class Voice_Channels(commands.Cog):
    def __init__(self,bot):
        super().__init__()
        self.bot = bot
        self.CREATED_CHANNELS = {}

    @commands.command()
    async def createvc(self, ctx, ChannelName : str = f'Vocal-{random.randint(1000,10000)}',MaxUsers : int = 99):
        vocal_channel = await ctx.message.guild.create_voice_channel(ChannelName,category=utils.get(ctx.message.guild.categories, id=1122912835962425397))
        await ctx.channel.send(embed=Embed(title="Info:",description=f"Canale vocale {vocal_channel.mention} creato con successo!",color=Color.green()))
        await vocal_channel.edit(user_limit=MaxUsers)

        asyncio.create_task(self.delete_channel_after_timeout(vocal_channel))
        self.CREATED_CHANNELS[vocal_channel.id] = {'text_channel' : ctx.channel,'author': ctx.message.author}


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            print(member,before.channel.name if before.channel is not None else None,after.channel.name if after.channel is not None else None)

            if before.channel is not None and before.channel != after.channel and before.channel in self.CREATED_CHANNELS:
                asyncio.create_task(self.delete_channel_after_timeout(before.channel))
        except Exception as e:
            print(e)

    async def delete_channel_after_timeout(self,channel):
        await asyncio.sleep(120)

        if channel.id in self.CREATED_CHANNELS and len(channel.members) == 0:
            await self.CREATED_CHANNELS[channel.id]['text_channel'].send(embed=Embed(title="Info:",description=f"{self.CREATED_CHANNELS[channel.id]['author'].mention} Nel canale vocale {channel.mention} sono passati 5 minuti senza qualcuno al suo interno, il canale e' stato eliminato.",color=Color.green()))
            await channel.delete()
            del self.CREATED_CHANNELS[channel.id]



def setup(bot):
    bot.add_cog(Voice_Channels(bot))