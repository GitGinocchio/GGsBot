from nextcord.ext import commands
from nextcord import \
    WebhookMessage,  \
    Permissions,     \
    Interaction,     \
    SlashOption,     \
    TextChannel,     \
    Embed,           \
    Colour,          \
    Role,            \
    slash_command
from nextcord.ui import \
    Modal,              \
    View

from datetime import datetime, timezone
import asyncio

from utils.db import Database
from utils.exceptions import ExtensionException
from utils.commons import Extensions
from utils.terminal import getlogger

from .ExtensionsUi import *

logger = getlogger()

permissions = Permissions(
    administrator=True
)

class CommandsManager(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.db = Database()
        self.bot = bot
        self.setup_dict : dict[Extensions, ExtensionUI] = {
            Extensions.AICHATBOT : AiChatBotUi,
            Extensions.GREETINGS : GreetingsUi,
            Extensions.VERIFY : VerifyUi,
            Extensions.STAFF : StaffUi,
            Extensions.TEMPVC : TempVCUi
        }

    @slash_command(name='ext', description='Set of commands to manage bot extensions',default_member_permissions=permissions,dm_permission=False)
    async def extensions(self, interacton : Interaction): pass

    # Show
    @extensions.subcommand(name='show', description='Show all the available and enabled extensions')
    async def show(self, 
            interaction : Interaction
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                configurations = await self.db.getAllExtensionConfig(guild=interaction.guild)

            embed = Embed(
                title='GGsBot Extensions', 
                description='List of all the available extensions and their status',
                colour=Colour.green(),
                timestamp=datetime.now(timezone.utc)
            )

            installed = []
            installed_str = ''
            for _, extension_id, enabled, _ in configurations:
                installed_str += f'**{extension_id.capitalize()}**: {'Enabled' if enabled else 'Disabled'}\n'
                installed.append(extension_id)

            available_str = ''
            for extension in Extensions:
                if extension not in installed:
                    available_str += f'**{extension.value.capitalize()}**\n'

            embed.add_field(name="Available Extensions:", value=available_str, inline=True)

            embed.add_field(name='Installed Extensions:', value=installed_str, inline=True)

            embed.set_author(name=self.bot.user.name,icon_url=self.bot.user.avatar.url)

        except AssertionError as e:
            await interaction.followup.send(e)
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else: 
            await interaction.followup.send(embed=embed)

    # Setup
    @extensions.subcommand(description='Setup a bot extension')
    async def setup(self, 
            interaction : Interaction,
            extension : str = SlashOption(description="The extension you want to setup", choices=Extensions, required=True)
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            message : WebhookMessage = None

            async with self.db:
                assert not await self.db.hasExtension(interaction.guild, Extensions(extension)), f'Extension {extension} already configured for this server'

            ui_type = self.setup_dict.get(Extensions(extension), None)

            #1. Inviare una modal o view specifica per quel comando
            #2. Ogni modal o view deve avere un pulsante submit e un pulsante cancel (che chiude la modal o view) e altri campi facoltativi per la configurazione

            config = {}
            if ui_type is not None:
                ui = ui_type(self.bot, interaction.guild, extension)
            else:
                ui = ExtensionUI(self.bot, interaction.guild, extension, lambda _:None)

            print('pre-interaction')
            message = await interaction.followup.send(embed=ui,view=ui, wait=True)

            assert not await ui.wait(), f'The configuration process has expired'
            print('post-interaction')
            config = dict(ui.config)
            
            async with self.db:
                await self.db.setupExtension(interaction.guild,Extensions(extension),config)

        except AssertionError as e:
            if message: 
                await message.edit(e, view=None, embed=None)
            else:
                await interaction.followup.send(e)
        except ExtensionException as e:
            await message.edit(embed=e.asEmbed(), view=None)
        else:
            await message.edit(f'{extension.capitalize()} extension configured successfully', view=None, embed=None)

    # Enable
    @extensions.subcommand(description='Enable a bot extension')
    async def enable(self,
            interaction : Interaction,
            extension : str = SlashOption(description="The extension you want to enable", choices=Extensions, required=True)
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                _, enabled = await self.db.getExtensionConfig(interaction.guild, Extensions(extension))

                if enabled: raise AssertionError(f'{extension.capitalize()} extension already enabled')

                await self.db.setExtension(interaction.guild, Extensions(extension), True)

        except AssertionError as e:
            await interaction.followup.send(e)
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(f'{extension.capitalize()} extension enabled successfully')

    # Disable
    @extensions.subcommand(description='Disable a bot extension')
    async def disable(self,
            interaction : Interaction,
            extension : str = SlashOption(description="The extension you want to enable", choices=Extensions, required=True)
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                _, enabled = await self.db.getExtensionConfig(interaction.guild, Extensions(extension))

                if not enabled: raise AssertionError(f'{extension.capitalize()} extension already disabled')
                
                await self.db.setExtension(interaction.guild, Extensions(extension), False)

        except AssertionError as e:
            await interaction.followup.send(e)
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(f'{extension.capitalize()} extension disabled successfully')

    # Teardown
    @extensions.subcommand(description='Teardown a previously configured bot extension')
    async def teardown(self, 
            interaction : Interaction,
            extension : str = SlashOption(description="The extension you want to remove", choices=Extensions, required=True)
        ): 
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                await self.db.teardownExtension(interaction.guild,Extensions(extension))
        
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(f"{extension.capitalize()} extension teardown completed successfully!")
            
def setup(bot : commands.Bot):
    bot.add_cog(CommandsManager(bot))