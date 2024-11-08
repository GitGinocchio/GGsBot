from nextcord.ext import commands
from nextcord import Permissions
import nextcord
import asyncio
import os

from utils.jsonfile import JsonFile, _JsonDict
from utils.terminal import getlogger

logger = getlogger()

permissions = nextcord.Permissions(
    administrator=True
)

class TemporaryChannels(commands.Cog):
    def __init__(self,bot : commands.Bot):
        self.dirfmt = './data/guilds/{guild_id}/commands.channels.TemporaryChannels'
        self.permission = 0
        self.bot = bot

    @nextcord.slash_command("tempvc","Very useful set of commands for set and unset vocals channels generators",default_member_permissions=permissions,dm_permission=False)
    async def tempvc(self, interaction : nextcord.Interaction): pass

    @tempvc.subcommand("add","Set :channel: to generate channels in :category: and remove them after :timeout: of inactivity")
    async def add(self, interaction : nextcord.Interaction, channel : nextcord.VoiceChannel, category : nextcord.CategoryChannel, timeout : float):
        await interaction.response.defer(ephemeral=True)

        datadir = self.dirfmt.format(guild_id=interaction.guild_id)

        try:
            assert timeout >= 0, "Error: The time before the channel is deleted cannot be negative!"
            os.makedirs(datadir,exist_ok=True)
        except AssertionError as e:
            await interaction.followup.send(e, ephemeral=True)
        except OSError as e:
            await interaction.followup.send(f"Error occurred while creating directory: {e}", ephemeral=True)
            return
        
        try:
            if os.path.exists(f'{datadir}/config.json'):
                file = JsonFile(f'{datadir}/config.json')
                assert str(channel.id) not in file['listeners'], "Error: There is already a configuration with this generator channel!"

                file['listeners'][channel.id] = {
                    "categoryID" : str(category.id),
                    "timeout" : timeout
                }

            else:
                file = JsonFile(f'{datadir}/config.json')
                file['listeners'] = _JsonDict({},file)
                file['listeners'][str(channel.id)] = {
                    "categoryID" : str(category.id),
                    "timeout" : timeout
                }
                file['channels'] = _JsonDict({},file)
        except AssertionError as e:
            await interaction.followup.send(e, ephemeral=True)
        else:
            await interaction.followup.send(f"Channel '{channel.name}' is now a temporary voice channel generator in category '{category.name}', with an inactivity timeout of {timeout}!", ephemeral=True)
     
    @tempvc.subcommand('del',"Delete one :channel: generator of temporary voice channels")
    async def delete(self, interaction : nextcord.Interaction, channel : nextcord.VoiceChannel):
        await interaction.response.defer(ephemeral=True)
        datadir = self.dirfmt.format(guild_id=interaction.guild_id)

        try:
            assert os.path.exists(f'/{datadir}/config.json'), "There are no saved temporary voice channel configurations!"
            file = JsonFile(f'{datadir}/config.json')
            assert str(channel.id) in file['listeners'], "The inserted generator channel is not present in the configurations!"

            for channel_id, generator_id in file['channels'].copy().items():
                if str(generator_id) == str(channel.id):
                    file['channels'].pop(channel_id)

            file['listeners'].pop(str(channel.id))
        except AssertionError as e:
            await interaction.followup.send(e, ephemeral=True)
        else:
            await interaction.followup.send(f"The channel '{channel.name}' is no longer a temporary channel generator channel!", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("TemporaryChannels.py ready, clearing unused temporary channels")

        guild_ids = [int(guild_id) for guild_id in os.listdir('./data/guilds/') if os.path.exists(f'{self.dirfmt.format(guild_id=guild_id)}/config.json')]

        for guild_id in guild_ids:
            file = JsonFile(f'{self.dirfmt.format(guild_id=guild_id)}/config.json')

            try:
                for channel_id in file['channels'].copy():
                    channel = self.bot.get_channel(int(channel_id))
                    if not channel: 
                        file['channels'].pop(channel_id)
                        continue

                    if len(channel.members) == 0:
                        await channel.delete(reason='GGsBot::TemporaryChannels')
                        file['channels'].pop(channel_id)
                        logger.debug(f'Temporary channel \"{channel.name}\"({channel.id}) in guild \"{channel.guild.name}\"({channel.guild.id}) deleted')
                    else:
                        logger.debug(f'Temporary channel \"{channel.name}\"({channel.id}) in guild \"{channel.guild.name}\"({channel.guild.id}) not deleted, there is/are {len(channel.members)} user/s inside the channel')
            except RuntimeError as e:
                logger.warning(e)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member : nextcord.Member, before : nextcord.VoiceState, after : nextcord.VoiceState):
        datadir = self.dirfmt.format(guild_id=member.guild.id)

        try:
            assert os.path.exists(f'{datadir}/config.json'), "Temporary channels extension not set."
            
            if after.channel and before.channel:
                if before.channel.id == after.channel.id: return
            
            file = JsonFile(f'{datadir}/config.json')
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

            if after.channel and str(after.channel.id) in file['listeners']:
                vocal_channel : nextcord.VoiceChannel = await member.guild.create_voice_channel(
                    reason='GGsBot::TemporaryChannels',
                    name=f'{str(member.display_name).capitalize()}\'s Vocal Channel',
                    category=self.bot.get_channel(int(file['listeners'][str(after.channel.id)]['categoryID']))
                )
                logger.debug(f'Successfully created temporary vocal channel \'{vocal_channel.name}\' with id: {vocal_channel.id}.')

                await member.move_to(vocal_channel)
                logger.debug(f'Successfully moved member \'{member.name}\' with id: {member.id}.')
                
                await vocal_channel.edit(overwrites=overwrites)
                logger.debug(f'Successfully edited permission for member \'{member.name}\' with id: {member.id}')

                file['channels'][str(vocal_channel.id)] = str(after.channel.id)

            if before.channel:
                file = JsonFile(f'{datadir}/config.json')
                
                if str(before.channel.id) in file['channels'] and len(before.channel.members) == 0:
                    generatorid = file['channels'][str(before.channel.id)]
                    timeout = file['listeners'][str(generatorid)]['timeout']
                    _ = asyncio.create_task(self.delete_channel(before.channel,timeout))

        except AssertionError as e: pass
        except nextcord.errors.HTTPException as e:
            logger.error(f'An HTTPException with code {e.code} occurred: {e.status}')
    
    async def delete_channel(self,channel : nextcord.VoiceChannel, timeout : float):
        datadir = self.dirfmt.format(guild_id=channel.guild.id)
        try:
            await asyncio.sleep(timeout)
            assert os.path.exists(f'{datadir}/config.json'), "Config file deleted when removing a channel!"
            assert len(channel.members) == 0, f'Temporary channel \'{channel.name}\'({channel.id}) not deleted, there is/are {len(channel.members)} user/s inside the channel'
            logger.debug(f'Waited {timeout} seconds before deleting channel \'{channel.name}\'({channel.id})')

            await channel.delete()
        except AssertionError as e: 
            logger.warning(e)
        except nextcord.NotFound:
            file = JsonFile(f'{datadir}/config.json')

            if str(channel.id) in file['channels']: 
                file['channels'].pop(str(channel.id))
        except nextcord.Forbidden as e: 
            logger.error(f'Bot has no permission to delete \"{channel.name}\" with id: {channel.id}')
        except nextcord.HTTPException as e: 
            logger.error(f'An HTTPException with code {e.code} occurred: {e.status}')
        else:
            file = JsonFile(f'{datadir}/config.json')

            if str(channel.id) in file['channels']: 
                file['channels'].pop(str(channel.id))

def setup(bot: commands.Bot):
    bot.add_cog(TemporaryChannels(bot))