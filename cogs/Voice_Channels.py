import nextcord
from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands
import random,asyncio,os

class Voice_Channels(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.CREATED_CHANNELS = {}

    @commands.command(name="createvc",help="""""")
    async def createvc(self,ctx,*,params : str = None):
        #/createvc name="My Voice Channel Name" maxusers=2

        try:
            param_channel_name = params.find('name=') if params is not None else -1
            param_max_users = params.find('maxusers=') if params is not None else -1
            assert params is None and param_channel_name == -1 and param_max_users == -1 or params is not None and param_channel_name != -1 and param_max_users != -1,"""Invalid way to pass params!"""

            if param_channel_name != -1:
                assert params.find('name=\"') != -1, 'You must provide use of `\"` with the name of your channel: \n\n example: `name=\"YOUR CHANNEL NAME\"`'
                channel_name = params[param_channel_name:param_max_users if param_max_users > param_channel_name else len(params)].split('\"')[:2][1]
            else: channel_name = f'VocalChannel-{random.randint(1000,9999)}'
            
            if param_max_users != -1:
                max_users = params[param_max_users:param_channel_name if param_channel_name > param_max_users else len(params)].split('=')[:2][1].replace('\"','').strip()
                assert max_users.isdecimal(), 'param `maxusers` must be type `int` not `str`'
            else:
                max_users = 0

        except AssertionError as e:
            await ctx.message.delete()
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=7)
        except Exception as e: print(e)
        else:
            vocal_channel = await ctx.message.guild.create_voice_channel(channel_name,category=utils.get(ctx.message.guild.categories, id=1122912835962425397))
            if int(max_users) != 0: 
                await ctx.channel.send(embed=Embed(title="Info:",description=f"Canale vocale {vocal_channel.mention} creato con successo con un limite di {max_users} utente/i!",color=Color.green()))
            else: 
                await ctx.channel.send(embed=Embed(title="Info:",description=f"Canale vocale {vocal_channel.mention} creato con successo!",color=Color.green()))
            await vocal_channel.edit(user_limit=int(max_users))

            task = asyncio.create_task(self.delete_channel_after_timeout(vocal_channel))
            self.CREATED_CHANNELS[vocal_channel.id] = {'text_channel' : ctx.channel,'vocal_channel' : vocal_channel,'author': ctx.message.author,'task' : task}

    @commands.command()
    async def deletevcs(self,ctx):
        command_roles = [(1122918623120457849,'astro')]
        command_permissions = [Permissions(administrator=True),Permissions(manage_channels=True)]

        try:
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """

            if len(self.CREATED_CHANNELS.keys()) > 0:
                try:
                    for channel in self.CREATED_CHANNELS.keys():
                        await self.CREATED_CHANNELS[channel]['vocal_channel'].delete()
                        del self.CREATED_CHANNELS[channel]
                except nextcord.ext.commands.errors.CommandInvokeError as e:
                    pass
            else:
                raise AssertionError('There are no vocal channels to delete.')
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        else:
            await ctx.channel.send(embed=Embed(title="Info:",description=f"Successfully eliminated {len(self.CREATED_CHANNELS.keys())} vocal channel/channels.",color=Color.green()), delete_after=5)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            print([member.name], [before.channel.name if before.channel is not None else None],'--->',[after.channel.name if after.channel is not None else None])
            #print(member,before.channel,after.channel)

            if before.channel is not None and before.channel != after.channel and before.channel.id in self.CREATED_CHANNELS:
                task = asyncio.create_task(self.delete_channel_after_timeout(before.channel))
                self.CREATED_CHANNELS[before.channel]['task'] = task
        except Exception as e:
            print(e)

    async def delete_channel_after_timeout(self,channel):
        try:
            timeout = 120
            await asyncio.sleep(timeout)

            if channel.id in self.CREATED_CHANNELS and len(channel.members) == 0: await channel.delete()
        except nextcord.errors.NotFound as e:
            print(e)
        except Exception as e:
            print(e)
        else:
            del self.CREATED_CHANNELS[channel.id]
            await self.CREATED_CHANNELS[channel.id]['text_channel'].send(embed=Embed(title="Info:",description=f"{self.CREATED_CHANNELS[channel.id]['author'].mention} Nel canale vocale {channel.mention} sono passati {timeout/60} minuti senza qualcuno al suo interno, il canale e' stato eliminato.",color=Color.green()))


def setup(bot):
    bot.add_cog(Voice_Channels(bot))

if __name__ == "__main__":
    os.system("python main.py")