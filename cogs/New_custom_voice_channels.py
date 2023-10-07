import nextcord
from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands,tasks
import random,asyncio,os
from datetime import datetime, timedelta
from jsonutils import jsonfile


class New_custom_voice_channels(commands.Cog):
    content = jsonfile('cogs/data/saved.json')
    def __init__(self,bot : commands.Bot):
        self.bot = bot
        self.custom_channels = []
        self.custom_channels_ids = []
    
    @commands.Cog.listener()
    async def on_ready(self):
        previous_channels_ids = len(self.content["Custom Channels"]["custom_channels"])
        for channel_id in self.content["Custom Channels"]["custom_channels"]:
            channel = self.bot.get_channel(channel_id)
            if channel is not None:
                if len(channel.members) == 0: 
                    await channel.delete()
                    self.content["Custom Channels"]["custom_channels"].remove(channel_id)
                    self.content.save()
        print(f'[{str(datetime.utcnow() + timedelta(hours=2))}] - Checking custom vocals channels ids. founded:{previous_channels_ids},removed:{previous_channels_ids - len(self.content["Custom Channels"]["custom_channels"])}')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            if after.channel is not None:
                if after.channel.id == self.content["Custom Channels"]["setup_channel_id"]:
                    vocal_channel = await after.channel.category.create_voice_channel(f'{str(member.name).capitalize()}\'s Vocal Channel')
                    self.custom_channels.append(vocal_channel)
                    self.custom_channels_ids.append(vocal_channel.id)
                    self.content["Custom Channels"]["custom_channels"] = self.custom_channels_ids
                    self.content.save()

                    overwrites = {
                        member: nextcord.PermissionOverwrite(
                            connect=True,
                            speak=True,
                            manage_channels=True,
                            manage_permissions=True
                        )
                    }
                    await vocal_channel.edit(overwrites=overwrites)
                    await member.move_to(vocal_channel)
                    _ = asyncio.create_task(self.delete_channel(vocal_channel))

                if before.channel is not None:
                    if before.channel.id != after.channel.id:
                        if before.channel in self.custom_channels or before.channel.id in self.content["Custom Channels"]["custom_channels"]:
                            _ = asyncio.create_task(self.delete_channel(before.channel))
            else:
                if before.channel in self.custom_channels or before.channel.id in self.content["Custom Channels"]["custom_channels"]:
                    _ = asyncio.create_task(self.delete_channel(before.channel))

        except AssertionError as e: pass
        except Exception as e: print(e)

    async def delete_channel(self,channel):
        try:
            await asyncio.sleep(self.content["Custom Channels"]['timeout'])

            if len(channel.members) == 0: 
                if channel in self.custom_channels:
                    self.custom_channels.remove(channel)
                if channel.id in self.content["Custom Channels"]["custom_channels"]:
                    self.content["Custom Channels"]["custom_channels"].remove(channel.id)
                    self.content["Custom Channels"]["custom_channels"] = self.custom_channels_ids
                    self.content.save()
                await channel.delete()
        except AssertionError as e:
            pass
        except Exception as e:
            print('delete_channel error:',e)

def setup(bot):
    bot.add_cog(New_custom_voice_channels(bot))