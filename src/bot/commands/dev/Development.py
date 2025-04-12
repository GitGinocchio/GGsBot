from nextcord.ext import commands
from nextcord import Permissions
from utils.config import config, reload_config_files
from utils.terminal import getlogger, F
import nextcord
import os

logger = getlogger()

DEV_ID = os.environ['DEVELOPER_ID']
DEVGUILD_ID = os.environ['DEVELOPER_GUILD_ID']

EXTENSIONS = [extension for extension in os.listdir('./src/bot/commands') if extension not in config['ignore_categories']]

permissions = Permissions(0)

class Development(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot

    @nextcord.slash_command("dev",default_member_permissions=permissions,guild_ids=[int(DEVGUILD_ID)])
    async def dev(self, interaction : nextcord.Interaction): pass

    @dev.subcommand("reload")
    async def reload(self, interaction : nextcord.Interaction): pass

    @reload.subcommand('extensions','Reload all Extensions or the specified extension')
    async def reloadExtensions(self,interaction : nextcord.Interaction, extension : str = nextcord.SlashOption(required=False,choices=EXTENSIONS,default=None)):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.id == int(DEV_ID): 
            await interaction.followup.send(f'Only the developer can execute this command!')
            return
        
        if not extension:
            categories = EXTENSIONS
        else:
            categories = [extension]

        for category in categories:
            logger.info(f'Looking in commands.{category}...')
            for filename in os.listdir(f'./src/bot/commands/{category}'):
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

    @reload.subcommand('config','Reload the config file')
    async def reloadConfig(self, interaction : nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.id == int(DEV_ID): 
            await interaction.followup.send(f'Only the developer can execute this command!')
            return
        
        try:
            reload_config_files()
        except Exception as e:
            logger.error(f'Unhandled Exception: {e}')
            await interaction.send(f'Unhandled Exception: {e}')
        else:
            await interaction.followup.send("Configuration file successfully reloaded.")


def setup(bot : commands.Bot):
    bot.add_cog(Development(bot))