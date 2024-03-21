from nextcord.ext import commands
from utils.jsonfile import JsonFile
from utils.terminal import getlogger
from cachetools import TTLCache
import nextcord
import asyncio
import os

logger = getlogger()

class TemporaryChannels(commands.Cog):
    def __init__(self,bot : commands.Bot):
        config = JsonFile('./config/config.jsonc')
        self.setups_cache = TTLCache(config['maxcachedguildsettings'],ttl=config['cachetimetolive'])
        self.bot = bot

    @nextcord.slash_command("temporarychannels_setup","Set up temporary channels in the server.",default_member_permissions=2147483664,dm_permission=False)
    async def setup_temporary_channels(self, interaction : nextcord.Interaction, setup_channel : nextcord.VoiceChannel, temporary_channels_category : nextcord.CategoryChannel, timeout : float):
        try:
            os.makedirs(f'./data/guilds/{interaction.guild_id}/{TemporaryChannels.__name__}',exist_ok=True)
        except OSError as e:
            await interaction.response.send_message(f"Error occurred while creating directory: {e}", ephemeral=True)
        else:
            file = JsonFile(f'./data/guilds/{interaction.guild_id}/{TemporaryChannels.__name__}/setup.json')
            file['temporary_channels_category_id'] = temporary_channels_category.id
            file['setup_channel_id'] = setup_channel.id
            file['temporary_channels'] = []
            file['timeout'] = timeout
            file.save()
            await interaction.response.send_message("Temporary channels setup completed successfully!", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("TemporaryChannels.py ready, clearing unused temporary channels")
        for i,guild_id in enumerate([file for file in os.listdir('./data/guilds/') if os.path.isfile(f'./data/guilds/{file}/{TemporaryChannels.__name__}/setup.json')]):
            logger.info(f"Fetching data.guilds.{guild_id}")
            file = JsonFile(f'./data/guilds/{guild_id}/{TemporaryChannels.__name__}/setup.json')
            if len(temporary_channels:=file['temporary_channels']) == 0:
                logger.info(f"No temporary channels found in guild with id: {guild_id}")
            for j,channel_id in enumerate(temporary_channels):
                channel = self.bot.get_channel(channel_id)
                if channel is not None:
                    logger.info(f"Found channel \"{channel.name}\" with id: {channel_id}")
                    if len(channel.members) == 0:
                        await channel.delete(reason='Temporary Channel Deleted')
                        logger.info(f'Temporary channel \"{channel.name}\" with id: {channel_id} deleted')
                        file['temporary_channels'].remove(channel_id)
                    else:
                        logger.warning(f'Temporary channel \"{channel.name}\" with id: {channel_id} not deleted there is/are {len(channel.members)} user/s inside the channel')

    def get_setup(self, guild : nextcord.Guild) -> JsonFile:
        setup_path = f'./data/guilds/{guild.id}/{TemporaryChannels.__name__}/setup.json'
        if guild.id not in self.setups_cache:
            self.setups_cache[guild.id] = JsonFile(setup_path)
        return self.setups_cache[guild.id]

    @commands.Cog.listener()
    async def on_voice_state_update(self, member : nextcord.Member, before : nextcord.VoiceChannel, after : nextcord.VoiceChannel):
        if str(member.guild.id) in os.listdir('./data/guilds') and os.path.exists(f'./data/guilds/{member.guild.id}/{TemporaryChannels.__name__}/setup.json'):
            try:
                logger.debug(f'Cache is currently saving config for this ids: {self.setups_cache.keys()}')
                setup = self.get_setup(member.guild)

                if after.channel is not None and after.channel.id == setup['setup_channel_id']:
                    overwrites = {
                        member: nextcord.PermissionOverwrite(
                            view_channel=True,
                            connect=True,
                            speak=True,
                            stream=True,
                            manage_channels=True,
                            manage_permissions=True,
                            move_members=True,
                            mute_members=True,
                            deafen_members=True,
                            priority_speaker=True
                        )
                    }
                    vocal_channel : nextcord.VoiceChannel = await member.guild.create_voice_channel(
                        name=f'{str(member.name).capitalize()}\'s Vocal Channel',
                        category=self.bot.get_channel(setup["temporary_channels_category_id"]),
                        overwrites=overwrites)
                    
                    await member.move_to(vocal_channel,reason='Temporary Channel Created')
                    setup["temporary_channels"].append(vocal_channel.id)
                    _ = asyncio.create_task(self.delete_channel(vocal_channel))

                if before.channel is not None:
                    if after.channel is not None:
                        if before.channel.id != after.channel.id and before.channel.id in setup['temporary_channels']:
                            _ = asyncio.create_task(self.delete_channel(before.channel))
                    else:
                        if before.channel.id in setup["temporary_channels"]:
                            _ = asyncio.create_task(self.delete_channel(before.channel))

            except nextcord.errors.HTTPException as e: print(e)
    
    async def delete_channel(self,channel : nextcord.VoiceChannel):
        try:
            setup = self.get_setup(channel.guild)
            await asyncio.sleep(setup["timeout"])
            assert len(channel.members) <= 0
            
            await channel.delete(reason='Temporary Channel Deleted')
        except AssertionError as e: pass
        except nextcord.NotFound:
            if channel.id in setup["temporary_channels"]: setup["temporary_channels"].remove(channel.id)
        except nextcord.Forbidden as e: 
            logger.error(f'Bot has no permission to delete \"{channel.name}\" with id: {channel.id}')
        except nextcord.HTTPException as e: logger.error(f'delete_channel HTTPException error: {e} args: [{e.args}]')
        else:
            setup["temporary_channels"].remove(channel.id)

def setup(bot: commands.Bot):
    bot.add_cog(TemporaryChannels(bot))