from nextcord.ext import commands
import nextcord
import asyncio

from utils.exceptions import ExtensionException, GGsBotException
from utils.db import Database
from utils.terminal import getlogger
from utils.commons import \
    Extensions,           \
    GLOBAL_INTEGRATION,   \
    GUILD_INTEGRATION,    \
    USER_INTEGRATION

logger = getlogger()

permissions = nextcord.Permissions(
    administrator=True
)

class TemporaryChannels(commands.Cog):
    def __init__(self,bot : commands.Bot):
        self.db = Database()
        self.bot = bot

    @nextcord.slash_command("tempvc","Very useful set of commands for set and unset vocals channels generators",default_member_permissions=permissions, integration_types=GUILD_INTEGRATION)
    async def tempvc(self, interaction : nextcord.Interaction): pass

    @tempvc.subcommand("add","Set :channel: to generate channels in :category: and remove them after :timeout: of inactivity")
    async def add(self, interaction : nextcord.Interaction, channel : nextcord.VoiceChannel, category : nextcord.CategoryChannel, timeout : float):
        try:
            await interaction.response.defer(ephemeral=True)

            if timeout < 0: 
                raise GGsBotException(
                    title="Invalid Argument",
                    description="`timeout` value cannot be negative!",
                    suggestions="Please provide a valid timeout value and try again!"
                )
            
            async with self.db:
                config, enabled = await self.db.getExtensionConfig(interaction.guild,Extensions.TEMPVC)

            if not enabled: raise ExtensionException("Not Enabled")

            if str(channel.id) in config['listeners']:
                raise GGsBotException(
                    title="Channel Already Configured",
                    description="There is already a configuration with this generator channel!",
                    suggestions="Please remove the existing configuration and try again!"
                )

            config['listeners'][str(channel.id)] = {
                'categoryID' : category.id,
                'timeout' : timeout
            }
            
            async with self.db:
                await self.db.editExtensionConfig(interaction.guild,Extensions.TEMPVC,config)

        except (ExtensionException, GGsBotException) as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(f"Channel '{channel.name}' is now a temporary voice channel generator in category '{category.name}', with an inactivity timeout of {timeout}!", ephemeral=True)

    @tempvc.subcommand('del',"Delete one generator :channel: of temporary voice channels")
    async def delete(self, interaction : nextcord.Interaction, channel : nextcord.VoiceChannel):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                config, enabled = await self.db.getExtensionConfig(interaction.guild, Extensions.TEMPVC)

            if not enabled: raise ExtensionException("Not Enabled")

            if str(channel.id) not in config['listeners']:
                raise GGsBotException(
                    title="Channel Not Found",
                    description=f"The channel {channel.mention} is not a temporary voice channel generator!",
                    suggestions="Please check if the channel is a temporary voice channel generator in category!",
                )

            for channel_id, generator_id in config['channels'].copy().items():
                if generator_id != channel.id:
                    continue

                try:
                    await self.bot.get_channel(int(channel_id)).delete()
                except nextcord.NotFound: pass
                except nextcord.Forbidden as e: 
                    logger.error(f'Bot has no permission to delete this channel')
                except nextcord.HTTPException as e: 
                    logger.error(f'An HTTPException with code {e.code} occurred: {e.status}')
                
                config['channels'].pop(str(channel_id))

            config['listeners'].pop(str(channel.id))

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.TEMPVC, config)
        except (ExtensionException, GGsBotException) as e:
            await interaction.followup.send(embed=e.asEmbed(), ephemeral=True)
        else:
            await interaction.followup.send(f"The channel '{channel.name}' is no longer a temporary channel generator channel!", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("TemporaryChannels.py ready, clearing unused temporary channels")

        async with self.db:
            configurations = await self.db.getAllExtensionConfig(Extensions.TEMPVC)

        for guild_id, extension_id, enabled, config in configurations:
            if not enabled: continue
            if not 'channels' in config: continue

            for channel_id in config['channels'].copy():
                channel = self.bot.get_channel(int(channel_id))

                if (len(channel.members) > 0) if channel else False:
                    logger.debug(f'Temporary channel \"{channel.name}\"({channel.id}) in guild \"{channel.guild.name}\"({channel.guild.id}) not deleted, there is/are {len(channel.members)} user/s inside the channel')
                    continue

                if not channel:
                    config['channels'].pop(str(channel_id))
                elif channel and len(channel.members) == 0:
                    try:
                        await channel.delete(reason='GGsBot::TemporaryChannels')
                    except nextcord.NotFound as e:
                        config['channels'].pop(str(channel_id))
                    except nextcord.Forbidden as e:
                        logger.error(f'Bot has no permission to delete \"{channel.name}\" with id: {channel.id}')
                    else:
                        config['channels'].pop(str(channel_id))
                    
                    logger.debug(f'Temporary channel \"{channel.name}\"({channel.id}) in guild \"{channel.guild.name}\"({channel.guild.id}) deleted')

        async with self.db:
            await self.db.editAllExtensionConfig(configurations)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member : nextcord.Member, before : nextcord.VoiceState, after : nextcord.VoiceState):
        try:
            if after.channel and before.channel:
                if before.channel.id == after.channel.id: return

            async with self.db:
                config, enabled = await self.db.getExtensionConfig(member.guild,Extensions.TEMPVC)

            if not enabled: return
        
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
                    name=f'{member.display_name.capitalize()}\'s Vocal Channel',
                    category=self.bot.get_channel(int(config['listeners'][str(after.channel.id)]['categoryID']))
                )
                logger.debug(f'Successfully created temporary vocal channel \'{vocal_channel.name}\' with id: {vocal_channel.id}.')

                await member.move_to(vocal_channel,reason='GGsBot::TemporaryChannels')
                logger.debug(f'Successfully moved member \'{member.name}\' with id: {member.id}.')
                
                await vocal_channel.edit(overwrites=overwrites)
                logger.debug(f'Successfully edited permission for member \'{member.name}\' with id: {member.id}')

                config['channels'][str(vocal_channel.id)] = after.channel.id

                async with self.db:
                    await self.db.editExtensionConfig(member.guild, Extensions.TEMPVC, config)

            if before.channel and str(before.channel.id) in config['channels'] and len(before.channel.members) == 0:
                generatorid = config['channels'][str(before.channel.id)]
                timeout = config['listeners'][str(generatorid)]['timeout']
                asyncio.create_task(self.delete_channel(before.channel,timeout))

        except ExtensionException as e: pass
        except nextcord.HTTPException as e:
            logger.error(f'HTTPException(code:{e.code}, status:{e.status}, response:{e.response}): {e.text}')
    
    async def delete_channel(self,channel : nextcord.VoiceChannel, timeout : float):
        try:
            async with self.db:
                config, enabled = await self.db.getExtensionConfig(channel.guild, Extensions.TEMPVC)

            if not enabled: return

            logger.debug(f"Waiting {timeout} seconds before deleting channel \'{channel.name}\'({channel.id})")

            await asyncio.sleep(timeout)

            if len(channel.members) != 0:
                raise GGsBotException(
                    title="Channel is still occupied",
                    description=f'Temporary channel \'{channel.name}\'({channel.id}) not deleted, there is/are {len(channel.members)} user/s inside the channel',
                    suggestions="The channel will be deleted when the channel is empty again."
                )

            logger.debug(f'Waited {timeout} seconds before deleting channel \'{channel.name}\'({channel.id})')

            await channel.delete(reason='GGsBot::TemporaryChannels')
            
            if str(channel.id) in config['channels']: 
                config['channels'].pop(str(channel.id))

            async with self.db:
                await self.db.editExtensionConfig(channel.guild, Extensions.TEMPVC, config)

        except GGsBotException as e: logger.warning(e)
        except ExtensionException as e: logger.debug(e)
        except nextcord.NotFound as e:
            pass
            # This means that the channel was deleted before we could delete it.
        except nextcord.Forbidden as e:
            logger.error(f'Bot has no permission to delete \"{channel.name}\" with id: {channel.id}')
        except nextcord.HTTPException as e: 
            logger.error(f'HTTPException(code:{e.code}, status:{e.status}, response:{e.response}): {e.text}')

def setup(bot: commands.Bot):
    bot.add_cog(TemporaryChannels(bot))