from nextcord.ext import commands
from nextcord import Permissions
import nextcord
import asyncio
import json
import os

from utils.jsonfile import JsonFile, _JsonDict
from utils.commons import Extensions
from utils.exceptions import ExtensionException
from utils.db import Database
from utils.terminal import getlogger

logger = getlogger()

permissions = nextcord.Permissions(
    administrator=True
)

class TemporaryChannels(commands.Cog):
    def __init__(self,bot : commands.Bot):
        self.db = Database()
        self.bot = bot

    @nextcord.slash_command("tempvc","Very useful set of commands for set and unset vocals channels generators",default_member_permissions=permissions,dm_permission=False)
    async def tempvc(self, interaction : nextcord.Interaction): pass

    @tempvc.subcommand("add","Set :channel: to generate channels in :category: and remove them after :timeout: of inactivity")
    async def add(self, interaction : nextcord.Interaction, channel : nextcord.VoiceChannel, category : nextcord.CategoryChannel, timeout : float):
        try:
            await interaction.response.defer(ephemeral=True)
            
            assert timeout >= 0, "Error: The time before the channel is deleted cannot be negative!"
            
            async with self.db:
                config = await self.db.getExtensionConfig(interaction.guild,Extensions.TEMPVC)

            assert str(channel.id) not in config['listeners'], "Error: There is already a configuration with this generator channel!"

            config['listeners'][str(channel.id)] = {
                'categoryID' : str(category.id),
                'timeout' : timeout
            }

            serialized = json.dumps(config)
            
            async with self.db:
                await self.db.editExtensionConfig(interaction.guild,Extensions.TEMPVC,serialized)

        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except AssertionError as e:
            await interaction.followup.send(e)
        else:
            await interaction.followup.send(f"Channel '{channel.name}' is now a temporary voice channel generator in category '{category.name}', with an inactivity timeout of {timeout}!", ephemeral=True)

    @tempvc.subcommand('del',"Delete one :channel: generator of temporary voice channels")
    async def delete(self, interaction : nextcord.Interaction, channel : nextcord.VoiceChannel):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                config = await self.db.getExtensionConfig(interaction.guild, Extensions.TEMPVC)

            assert str(channel.id) in config['listeners'], "The inserted generator channel is not present in the configurations!"

            for channel_id, generator_id in config['channels'].copy().items():
                if str(generator_id) != str(channel.id):
                    continue
                
                config['channels'].pop(str(channel_id))

            config['listeners'].pop(str(channel.id))

            serialized = json.dumps(config)

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.TEMPVC, serialized)
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed(), ephemeral=True)
        except AssertionError as e:
            await interaction.followup.send(e, ephemeral=True)
        else:
            await interaction.followup.send(f"The channel '{channel.name}' is no longer a temporary channel generator channel!", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("TemporaryChannels.py ready, clearing unused temporary channels")

        async with self.db:
            configurations = await self.db.getAllExtensionConfig(Extensions.TEMPVC)

        for guild_id, config in configurations:
            for channel_id in config['channels'].copy():
                channel = self.bot.get_channel(int(channel_id))

                if not channel:
                    config['channels'].pop(channel_id)
                elif len(channel.members) == 0:
                    try:
                        await channel.delete(reason='GGsBot::TemporaryChannels')
                    except nextcord.NotFound as e: pass
                    
                    config['channels'].pop(channel_id)
                    logger.debug(f'Temporary channel \"{channel.name}\"({channel.id}) in guild \"{channel.guild.name}\"({channel.guild.id}) deleted')
                else:
                    logger.debug(f'Temporary channel \"{channel.name}\"({channel.id}) in guild \"{channel.guild.name}\"({channel.guild.id}) not deleted, there is/are {len(channel.members)} user/s inside the channel')

            guild = self.bot.get_guild(int(guild_id))

            async with self.db:
                await self.db.editExtensionConfig(guild, Extensions.TEMPVC, config)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member : nextcord.Member, before : nextcord.VoiceState, after : nextcord.VoiceState):
        try:
            if after.channel and before.channel:
                if before.channel.id == after.channel.id: return

            async with self.db:
                config = await self.db.getExtensionConfig(member.guild,Extensions.TEMPVC)
        
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

            if after.channel and str(after.channel.id) in config['listeners']:
                vocal_channel : nextcord.VoiceChannel = await member.guild.create_voice_channel(
                    reason='GGsBot::TemporaryChannels',
                    name=f'{str(member.display_name).capitalize()}\'s Vocal Channel',
                    category=self.bot.get_channel(int(config['listeners'][str(after.channel.id)]['categoryID']))
                )
                logger.debug(f'Successfully created temporary vocal channel \'{vocal_channel.name}\' with id: {vocal_channel.id}.')

                await member.move_to(vocal_channel)
                logger.debug(f'Successfully moved member \'{member.name}\' with id: {member.id}.')
                
                await vocal_channel.edit(overwrites=overwrites)
                logger.debug(f'Successfully edited permission for member \'{member.name}\' with id: {member.id}')

                config['channels'][str(vocal_channel.id)] = str(after.channel.id)

            if before.channel and str(before.channel.id) in config['channels'] and len(before.channel.members) == 0:
                generatorid = config['channels'][str(before.channel.id)]
                timeout = config['listeners'][str(generatorid)]['timeout']
                _ = asyncio.create_task(self.delete_channel(before.channel,timeout))

            async with self.db:
                await self.db.editExtensionConfig(member.guild, Extensions.TEMPVC, config)

        except ExtensionException as e: pass
        except nextcord.errors.HTTPException as e:
            logger.error(f'An HTTPException with code {e.code} occurred: {e.status}')
    
    async def delete_channel(self,channel : nextcord.VoiceChannel, timeout : float):
        try:
            await asyncio.sleep(timeout)
            assert len(channel.members) == 0, f'Temporary channel \'{channel.name}\'({channel.id}) not deleted, there is/are {len(channel.members)} user/s inside the channel'

            logger.debug(f'Waited {timeout} seconds before deleting channel \'{channel.name}\'({channel.id})')

            async with self.db:
                config = await self.db.getExtensionConfig(channel.guild, Extensions.TEMPVC)

            try:
                await channel.delete()
            except nextcord.NotFound: pass
            except nextcord.Forbidden as e: 
                logger.error(f'Bot has no permission to delete \"{channel.name}\" with id: {channel.id}')
            except nextcord.HTTPException as e: 
                logger.error(f'An HTTPException with code {e.code} occurred: {e.status}')
            finally:
                if str(channel.id) in config['channels']:
                    config['channels'].pop(str(channel.id))

            async with self.db:
                await self.db.editExtensionConfig(channel.guild, Extensions.TEMPVC, config)

        except AssertionError as e: logger.warning(e)
        except ExtensionException as e: pass

def setup(bot: commands.Bot):
    bot.add_cog(TemporaryChannels(bot))