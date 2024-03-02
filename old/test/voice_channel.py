from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands,tasks
import random,asyncio,os

class voice_channel(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.TIMEOUT = 60
        self.tracked = []
    
    @commands.command(name="createvc",help="""""")
    async def createvc(self,ctx,*,params : str = None):
        try:
            param_channel_name = params.find('name=') if params is not None else -1
            param_max_users = params.find('maxusers=') if params is not None else -1
            assert params is None and param_channel_name == -1 or param_max_users == -1 or params is not None and param_channel_name != -1 or param_max_users != -1,"""Invalid way to pass params!"""

            if param_channel_name != -1:
                assert params.find('name=\"') != -1, 'You must provide use of `\"` with the name of your channel: \n\n example: `name=\"YOUR CHANNEL NAME\"`'
                channel_name = params[param_channel_name:param_max_users if param_max_users > param_channel_name else len(params)].split('\"')[:2][1]
            else: channel_name = f'VocalChannel-{random.randint(1000,9999)}'
            
            if param_max_users != -1:
                max_users = params[param_max_users:param_channel_name if param_channel_name > param_max_users else len(params)].split('=')[:2][1].replace('\"','').strip()
                assert max_users.isdecimal(), 'param `maxusers` must be type `int` not `str`'
            else: max_users = 0

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

            d = {'vocal' : vocal_channel, 'text' : ctx.channel,'author' : ctx.message.author}
            self.tracked.append(d)
            _ = asyncio.create_task(self.delete_channel(vocal_channel))

    @commands.command(name="deletevcs",help="""""")
    async def deletevcs(self,ctx):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True),Permissions(manage_channels=True)]

        try:
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            
            channel_removed = len(self.tracked)
            for tracked_info in self.tracked:
                await tracked_info['vocal'].delete()
            self.tracked.clear()

            
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        else:
            await ctx.channel.send(embed=Embed(title="Info:",description=f"Successfully eliminated {channel_removed} vocal channel/channels.",color=Color.green()), delete_after=5)
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            assert before.channel is not None
            #print([member.name], [before.channel.name],'--->',[after.channel.name if after.channel is not None else None])

            tracked_ids = [track['vocal'].id for track in self.tracked]

            if after.channel is not None:
                if before.channel.id != after.channel.id:
                    if before.channel.id in tracked_ids:
                        _ = asyncio.create_task(self.delete_channel(before.channel))
            else:
                if before.channel.id in tracked_ids:
                    _ = asyncio.create_task(self.delete_channel(before.channel))

        except AssertionError as e:
            pass
        except Exception as e:
            print(e)
        
    async def delete_channel(self,channel):
        try:
            tracked_info = [info for info in self.tracked if info['vocal'].id == channel.id]
            assert len(tracked_info) == 1
            tracked_info = tracked_info[0]

            await asyncio.sleep(self.TIMEOUT)
            if len(channel.members) == 0:
                if tracked_info in self.tracked:
                    await tracked_info['text'].send(embed=Embed(title="Info:",description=f"{tracked_info['author'].mention} Nel canale vocale {channel.mention} sono passati {self.TIMEOUT/60} minuti senza qualcuno al suo interno, il canale e' stato eliminato.",color=Color.green()))
                    self.tracked.remove(tracked_info)
                    await channel.delete()

        except AssertionError as e:
            await tracked_info['text'].send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=7)
        except Exception as e:
            print('delete_channel error:',e)
            await tracked_info['text'].send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=7)





def setup(bot):
    bot.add_cog(voice_channel(bot))

if __name__ == "__main__":
    os.system("python main.py")
