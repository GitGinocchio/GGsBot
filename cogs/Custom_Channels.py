import nextcord
from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands,tasks
import random,asyncio,os
from datetime import datetime, timedelta
from jsonutils import jsonfile


class Custom_Channels(commands.Cog):
    content = jsonfile('cogs/data/saved.json')
    def __init__(self,bot : commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        removed = 0
        for channel_id in self.content["Custom Channels"]["custom_channels"]:
            channel = self.bot.get_channel(channel_id)
            if channel is not None:
                if len(channel.members) == 0: 
                    _ = asyncio.create_task(self.__delete_channel(channel))
                    removed+=1
            else:
                self.content["Custom Channels"]["custom_channels"].remove(channel_id)
                self.content.save()
        print(f'[{str(datetime.utcnow() + timedelta(hours=2))}] - Checking custom vocals channels ids. founded:{len(self.content["Custom Channels"]["custom_channels"])},removed:{removed}')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            if after.channel is not None and after.channel.id == self.content["Custom Channels"]["setup_channel_id"]:
                vocal_channel = await after.channel.category.create_voice_channel(f'{str(member.name).capitalize()}\'s Vocal Channel')
                self.content["Custom Channels"]["custom_channels"].append(vocal_channel.id)
                self.content.save()

                overwrites = {
                    member: nextcord.PermissionOverwrite(
                        connect=True,
                        speak=True,
                        manage_channels=True,
                        manage_permissions=True,
                        move_members=True
                    )
                }
                await member.move_to(vocal_channel)
                await vocal_channel.edit(overwrites=overwrites)
                await asyncio.sleep(5)
                _ = asyncio.create_task(self.__delete_channel(vocal_channel))

            if before.channel is not None:
                if after.channel is not None:
                    if before.channel.id != after.channel.id:
                        if before.channel.id in self.content["Custom Channels"]["custom_channels"]:
                            _ = asyncio.create_task(self.__delete_channel(before.channel))
                else:
                    if before.channel.id in self.content["Custom Channels"]["custom_channels"]:
                        _ = asyncio.create_task(self.__delete_channel(before.channel))

        except AssertionError as e: pass

    async def __delete_channel(self,channel):
        try:
            await asyncio.sleep(self.content["Custom Channels"]['timeout'])
            assert self.bot.get_channel(channel.id) is not None
            
            if len(channel.members) == 0: 
                self.content["Custom Channels"]["custom_channels"].remove(channel.id)
                self.content.save()
                await channel.delete()
        except AssertionError as e: pass
        except Exception as e: print('delete_channel error:',e)

def setup(bot):
    bot.add_cog(Custom_Channels(bot))