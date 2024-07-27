from nextcord.ext import commands
from utils.config import config, reload
from utils.terminal import getlogger, F
from functools import wraps
import nextcord
import os

logger = getlogger()

DEV_ID = os.environ['DEVELOPER_ID']
DEVGUILD_ID = os.environ['DEVELOPER_GUILD_ID']

class Development(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command('dev_reload_commands','Reload all Extensions or the specified extension',guild_ids=[DEVGUILD_ID])
    async def reload_commands(self,interaction : nextcord.Interaction, extension : str = None):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.id == DEV_ID: 
            await interaction.followup.send(f'Only the developer can execute this command!')
            return
        
        if not extension:
            categories = categories = [c for c in os.listdir('./commands') if c not in config['ignore_categories']]
        else:
            categories = [extension]

        for category in categories:
            logger.info(f'Looking in commands.{category}...')
            for filename in os.listdir(f'./commands/{category}'):
                if filename.endswith('.py') and filename not in config['ignore_files']:
                    try:
                        self.bot.reload_extension(f'commands.{category}.{filename[:-3]}')
                    except (commands.ExtensionFailed,
                            commands.ExtensionAlreadyLoaded,
                            commands.ExtensionNotFound,
                            commands.InvalidSetupArguments) as e:
                        logger.critical(f'Loading command error: Cog {e.name} message: \n{e}')
                    except (commands.NoEntryPointError, commands.ExtensionNotLoaded) as e:
                        pass  # if no entry point found maybe is a file used by the main command file.
                    else:
                        logger.info(f'Imported command {F.LIGHTMAGENTA_EX}{category}.{filename[:-3]}{F.RESET}')
                elif filename in config['ignore_files']:
                    pass
                else:
                    logger.warning(f'Skipping non-py file: \'{filename}\'')
        await interaction.followup.send(f'Reload Complete...')

    @nextcord.slash_command('dev_reload_config','Reload the config file',guild_ids=[DEVGUILD_ID])
    async def reload_config(self, interaction : nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.id == DEV_ID: 
            await interaction.followup.send(f'Only the developer can execute this command!')
            return
        
        try:
            reload()
        except Exception as e:
            logger.error(f'Unhandled Exception: {e}')
            await interaction.send(f'Unhandled Exception: {e}')
        else:
            await interaction.followup.send("Configuration file successfully reloaded.")


def setup(bot : commands.Bot):
    bot.add_cog(Development(bot))