from nextcord.ext import commands
from nextcord import Permissions
from utils.config import config, reload_config_files
from utils.terminal import getlogger, F
import nextcord
import os

from utils.commons import isdeveloper, load_commands

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
    @isdeveloper()
    async def reloadExtensions(self,interaction : nextcord.Interaction, extension : str = nextcord.SlashOption(required=False,choices=EXTENSIONS,default=None)):
        await interaction.response.defer(ephemeral=True)
        
        if not extension:
            categories = EXTENSIONS
        else:
            categories = [extension]

        load_commands(self.bot, logger, categories=categories, reload=True)
        logger.info('Extensions reloaded successfully')

        await interaction.followup.send(f'Reload Complete...')

    @reload.subcommand('config','Reload the config file')
    @isdeveloper()
    async def reloadConfig(self, interaction : nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            reload_config_files()
        except Exception as e:
            logger.error(f'Unhandled Exception: {e}')
            await interaction.send(f'Unhandled Exception: {e}')
        else:
            await interaction.followup.send("Configuration file successfully reloaded.")


def setup(bot : commands.Bot):
    bot.add_cog(Development(bot))