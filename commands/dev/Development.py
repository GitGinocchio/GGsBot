from nextcord.ext import commands
from utils.config import config, reload
from utils.terminal import getlogger, F
import nextcord
import os

logger = getlogger()

class Development(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command('dev_reload_commands','Reload all Extensions or the specified extension',default_member_permissions=8)
    async def reload_commands(self,interaction : nextcord.Interaction, extension : str = None):
        try:
            if not extension:
                categories = [c for c in os.listdir('./commands') if c not in config['ignore_categories']]
                logger.info('Loading commands...')
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
            else:
                for filename in os.listdir(f'./commands/{extension}'):
                    if filename.endswith('.py') and filename not in config['ignore_files']:
                        try:
                            self.bot.reload_extension(f'commands.{extension}.{filename[:-3]}')
                        except (commands.ExtensionFailed,
                                commands.ExtensionAlreadyLoaded,
                                commands.ExtensionNotFound,
                                commands.InvalidSetupArguments) as e:
                            logger.critical(f'Loading command error: Cog {e.name} message: \n{e}')
                        except (commands.NoEntryPointError, commands.ExtensionNotLoaded) as e:
                            pass  # if no entry point found maybe is a file used by the main command file.
                        else:
                            logger.info(f'Imported command {F.LIGHTMAGENTA_EX}{extension}.{filename[:-3]}{F.RESET}')
                    elif filename in config['ignore_files']:
                        pass
                    else:
                        logger.warning(f'Skipping non-py file: \'{filename}\'')
        except Exception as e:
            await interaction.send(f'Errore durante il ricaricamento di {extension}: {e}')
        else:
            if extension:
                await interaction.send(f'Ricaricata con successo l\'estensione: {extension}')
            else:
                await interaction.send(f'Estensioni ricaricaricate con successo.')

    @nextcord.slash_command('dev_reload_config','Reload the config file',default_member_permissions=8)
    async def reload_config(self, interaction : nextcord.Interaction):
        try:
            reload()
        except Exception as e:
            await interaction.send(f'Unhandled Exception: {e}')
        else:
            await interaction.send("File di configurazione ricaricato con successo.")


def setup(bot : commands.Bot):
    bot.add_cog(Development(bot))