from nextcord import Embed,Color,utils,channel,Permissions,Interaction
from nextcord.ext import commands
from utils.terminal import getlogger
from typing import Literal
import nextcord
import ast
import os


EXTENSIONS = []

def has_setup_function(filepath : str):
    with open(filepath, 'r', encoding='utf-8') as file:
        file_content = file.read()

    try:
        parsed_content = ast.parse(file_content)
    except SyntaxError:
        return False

    for node in ast.walk(parsed_content):
        if isinstance(node, ast.FunctionDef) and node.name == 'setup':
            return True

    return False

"""
for category in os.listdir('./commands'):
    for cog in os.listdir(f'./commands/{category}'):
        if cog == '__pycache__': continue
        if has_setup_function(f'./commands/{category}/{cog}'):
            EXTENSIONS.append(cog.replace('.py',''))
EXTENSIONS.remove('CommandsManager')
EXTENSIONS.remove('RequestsErrors')
EXTENSIONS.remove('Development')
"""

permissions = Permissions(
    administrator=True
)

class CommandsManager(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.sync_all_application_commands()
        await self.bot.discover_application_commands(guild_id=os.environ['DEVELOPER_GUILD_ID'])

    @nextcord.slash_command("commands","Command set to enable and disable commands",default_member_permissions=permissions)
    async def commands(self, interaction : nextcord.Interaction): pass

    @nextcord.slash_command("extensions","Set of commands to enable and disable extensions",default_member_permissions=permissions)
    async def extensions(self, interaction : nextcord.Interaction): pass

    @commands.subcommand("enable", "Enable a specific :command:")
    async def enable(self, interaction : nextcord.Interaction, command : str = nextcord.SlashOption(required=True, choices=EXTENSIONS)):
        pass

    @commands.subcommand("disable", "Disable a specific :command:")
    async def disable(self, interaction : nextcord.Interaction, command : str = nextcord.SlashOption(required=True, choices=EXTENSIONS)):
        pass

    @extensions.subcommand("enable", "Enable a specific :extension:")
    async def enable(self, interaction : nextcord.Interaction, extension : str = nextcord.SlashOption(required=True, choices=EXTENSIONS)):
        guild_application_commands = interaction.guild.get_application_commands()
        cog = self.bot.cogs.get(extension)
        
        try:
            await interaction.response.defer(ephemeral=True)

            assert cog, "Extension not found, probably does not exist or is disabled globally"
            
            for command in cog.application_commands:
                if command not in guild_application_commands:
                    interaction.guild.add_application_command(command)
            await interaction.guild.register_application_commands(*cog.application_commands)
        except AssertionError as e:
            await interaction.followup.send(e)
        else:
            await interaction.followup.send(F"Extension {extension} successfully enabled")
        
    @extensions.subcommand("disable", "Disable a specific :extension:")
    async def disable(self, interaction : nextcord.Interaction, extension : str = nextcord.SlashOption(required=True, choices=EXTENSIONS)):
        guild_application_commands = interaction.guild.get_application_commands()
        cog = self.bot.cogs.get(extension)
        
        try:
            await interaction.response.defer(ephemeral=True)

            assert cog, "Extension not found, probably does not exist or is disabled globally"

            await interaction.guild.delete_application_commands(*[command for command in cog.application_commands if command in guild_application_commands])

            await self.bot.sync_all_application_commands()

            await self.bot.discover_application_commands(guild_id=interaction.guild.id)
        except AssertionError as e:
            await interaction.followup.send(e)
        else:
            await interaction.followup.send(F"Extension {extension} successfully disabled")
            

#def setup(bot : commands.Bot):
    #bot.add_cog(CommandsManager(bot))