from nextcord.ext import commands
from utils.jsonfile import JsonFile
from utils.terminal import getlogger
from utils.config import config
from cachetools import TTLCache
import nextcord
import asyncio
import os

logger = getlogger()

class TemporaryChannels(commands.Cog):
    def __init__(self,bot : commands.Bot):
        self.setups_cache = TTLCache(config["temporary-channels"]['maxcachedguilds'],ttl=config["temporary-channels"]['cachettl'])
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
            guild = self.bot.get_guild(int(guild_id))
            file = self.get_setup(guild)
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
                        logger.warning(f'Temporary channel not deleted, there is/are {len(channel.members)} user/s inside the channel')

    def get_setup(self, guild : nextcord.Guild) -> JsonFile:
        setup_path = f'./data/guilds/{guild.id}/{TemporaryChannels.__name__}/setup.json'
        if guild.id not in self.setups_cache:
            logger.debug(f'Successfully added guild config for guild \'{guild.name}\' with id: {guild.id}.')
            self.setups_cache[guild.id] = JsonFile(setup_path)
        logger.debug(f'Currently saving config files for {self.setups_cache.currsize} server/s.')
        logger.debug(f'Getting config file for guild \'{guild.name}\' with id: {guild.id}.')
        return self.setups_cache[guild.id]

    @commands.Cog.listener()
    async def on_voice_state_update(self, member : nextcord.Member, before : nextcord.VoiceChannel, after : nextcord.VoiceChannel):
        if str(member.guild.id) in os.listdir('./data/guilds') and os.path.exists(f'./data/guilds/{member.guild.id}/{TemporaryChannels.__name__}/setup.json'):
            try:
                if after.channel:
                    if before.channel:
                        if before.channel.id == after.channel.id: return

                    setup = self.get_setup(member.guild)
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
                    if after.channel.id == setup['setup_channel_id']:
                        vocal_channel : nextcord.VoiceChannel = await member.guild.create_voice_channel(
                            reason='TEMPORARY_CHANNEL',
                            name=f'{str(member.display_name).capitalize()}\'s Vocal Channel',
                            category=self.bot.get_channel(setup["temporary_channels_category_id"]))
                        logger.info(f'Successfully created temporary vocal channel \'{vocal_channel.name}\' with id: {vocal_channel.id}.')
                        
                        await member.move_to(vocal_channel)
                        logger.info(f'Successfully moved member \'{member.name}\' with id: {member.id}.')
                        
                        await vocal_channel.edit(overwrites=overwrites)
                        logger.info(f'Successfully edited permission for member \'{member.name}\' with id: {member.id}')

                        setup["temporary_channels"].append(vocal_channel.id)

                if before.channel:
                    setup = self.get_setup(member.guild)
                    if before.channel.id in setup['temporary_channels'] and len(before.channel.members) == 0:
                        _ = asyncio.create_task(self.delete_channel(before.channel))
            
            except nextcord.errors.HTTPException as e:
                logger.erorr(f'An HTTPException with code {e.code} occurred: {e.status}')
    
    async def delete_channel(self,channel : nextcord.VoiceChannel):
        try:
            setup = self.get_setup(channel.guild)
            await asyncio.sleep(setup["timeout"])
            logger.info(f'Waited {setup["timeout"]} seconds before deleting channel \'{channel.name}\' with id: {channel.id}')
            assert len(channel.members) <= 0, f'Temporary channel not deleted, there is/are {len(channel.members)} user/s inside the channel'
            
            await channel.delete()
        except AssertionError as e: 
            logger.warning(e)
        except nextcord.NotFound:
            if channel.id in setup["temporary_channels"]: 
                setup["temporary_channels"].remove(channel.id)
        except nextcord.Forbidden as e: 
            logger.error(f'Bot has no permission to delete \"{channel.name}\" with id: {channel.id}')
        except nextcord.HTTPException as e: 
            logger.erorr(f'An HTTPException with code {e.code} occurred: {e.status}')
        else:
            setup["temporary_channels"].remove(channel.id)

def setup(bot: commands.Bot):
    bot.add_cog(TemporaryChannels(bot))