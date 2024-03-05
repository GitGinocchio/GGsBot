from nextcord.ext import commands
from utils.jsonfile import JsonFile
import asyncio,os
import nextcord

class TemporaryChannels(commands.Cog):
    def __init__(self,bot : commands.Bot):
        self.bot = bot

    @nextcord.slash_command("setup_temporary_channels","Set up temporary channels in the server.",default_member_permissions=2147483664,dm_permission=False)
    async def setup_temporary_channels(self, interaction : nextcord.Interaction, setup_channel : nextcord.VoiceChannel, temporary_channels_category : nextcord.CategoryChannel, timeout : float):
        try:
            os.makedirs(f'./data/guilds/{interaction.guild_id}/TemporaryChannels',exist_ok=True)
        except OSError as e:
            await interaction.response.send_message(f"Error occurred while creating directory: {e}", ephemeral=True)
        else:
            file = JsonFile(f'./data/guilds/{interaction.guild_id}/TemporaryChannels/setup.json')
            file['temporary_channels_category_id'] = temporary_channels_category.id
            file['setup_channel_id'] = setup_channel.id
            file['temporary_channels'] = []
            file['timeout'] = timeout
            file.save()
            await interaction.response.send_message("Temporary channels setup completed successfully!", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild_id in os.listdir('./data/guilds/'):
            if os.path.isfile(f'./data/guilds/{guild_id}/TemporaryChannels/setup.json'):
                file = JsonFile(f'./data/guilds/{guild_id}/TemporaryChannels/setup.json')
                for channel_id in file['temporary_channels']:
                    channel = self.bot.get_channel(channel_id)
                    if channel is not None:
                        if len(channel.members) == 0: 
                            await channel.delete(reason='Temporary Channel Deleted')
                            print('Temporary Channel Deleted - Channel id: {}'.format(channel_id))
                    else:
                        file['temporary_channels'].remove(channel_id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member : nextcord.Member, before : nextcord.VoiceChannel, after : nextcord.VoiceChannel):
        setup_path = f'./data/guilds/{after.channel.guild.id if after.channel is not None else before.channel.guild.id}/TemporaryChannels/setup.json'

        if os.path.exists(setup_path):
            setup = JsonFile(setup_path)

            if after.channel is not None and after.channel.id == setup["setup_channel_id"]:
                vocal_channel : nextcord.VoiceChannel = await after.channel.category.create_voice_channel(f'{str(member.name).capitalize()}\'s Vocal Channel')
                await member.move_to(vocal_channel,reason='Temporary Channel Created')
                setup["temporary_channels"].append(vocal_channel.id)
                overwrites = {
                    member: nextcord.PermissionOverwrite(
                        connect=True,
                        speak=True,
                        manage_channels=True,
                        manage_permissions=True,
                        move_members=True
                    )
                }
                await vocal_channel.edit(overwrites=overwrites)
                _ = asyncio.create_task(self.delete_channel(vocal_channel,setup))

            if before.channel is not None:
                if after.channel is not None:
                    if before.channel.id != after.channel.id:
                        if before.channel.id in setup["temporary_channels"]:
                            _ = asyncio.create_task(self.delete_channel(before.channel,setup))
                else:
                    if before.channel.id in setup["temporary_channels"]:
                        _ = asyncio.create_task(self.delete_channel(before.channel,setup))

    async def delete_channel(self,channel : nextcord.VoiceChannel, setup : JsonFile):
        try:
            await asyncio.sleep(setup["timeout"])
            assert self.bot.get_channel(channel.id) is not None
            
            if len(channel.members) == 0: 
                setup["temporary_channels"].remove(channel.id)
                await channel.delete(reason='Temporary Channel Deleted')
        except AssertionError as e: pass
        except Exception as e: print('delete_channel error:',e)

def setup(bot: commands.Bot):
    bot.add_cog(TemporaryChannels(bot))