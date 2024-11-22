from nextcord.ext import commands
from nextcord import \
    Permissions, \
    Interaction, \
    SlashOption, \
    TextChannel, \
    Role, \
    slash_command

from utils.db import Database
from utils.exceptions import ExtensionException
from utils.commons import Extensions
from utils.terminal import getlogger

logger = getlogger()

permissions = Permissions(
    administrator=True
)

class CommandsManager(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.db = Database()
        self.bot = bot
    
    @slash_command(name='setup', description='Setup a bot extension',default_member_permissions=permissions,dm_permission=False)
    async def setup(self, interaction : Interaction): pass

    @setup.subcommand(name=Extensions.TEMPVC.value, description='Initialize TempVC extension on this server')
    async def setup_tempvc(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                await self.db.setupExtension(interaction.guild,Extensions.TEMPVC,{
                    'listeners'  : {},
                    'channels' : {}
                })
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(f'{Extensions.TEMPVC.value.capitalize()} extension installed successfully')

    @setup.subcommand(name=Extensions.AICHATBOT.value, description='Initialize AiChatBot extension on this server')
    async def setup_aichatbot(self, 
                    interaction : Interaction,
                    textchannel : TextChannel = SlashOption("textchannel","The text channel where the bot can be used and all public or private chats will be created",required=True),
                    delay : int = SlashOption("delay","The number of seconds a user must wait before sending another prompt",required=True,default=5)
                ):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                await self.db.setupExtension(interaction.guild,Extensions.AICHATBOT,{
                    'text-channel' : textchannel.id,
                    'chat-delay' : delay,
                    'threads' : {}
                })
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(f'{Extensions.AICHATBOT.value.capitalize()} extension installed successfully')

    @setup.subcommand(name=Extensions.GREETINGS.value,description='Initialize Greetings extension on this server')
    async def setup_greetings(self, 
                interaction : Interaction, 
                welcome_channel : TextChannel = SlashOption("welcome-channel","The channel where the welcome messages will be sent",required=False,default=None),
                goodbye_channel : TextChannel = SlashOption("goodbye-channel","The channel where the goodbye messages will be sent",required=False,default=None),
            ):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                await self.db.setupExtension(interaction.guild,Extensions.GREETINGS,{
                    'welcome_channel_id' : (welcome_channel.id if welcome_channel else None),
                    'goodbye_channel_id' : (goodbye_channel.id if goodbye_channel else None)
                })
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(f'{Extensions.GREETINGS.value.capitalize()} extension installed successfully')

    @setup.subcommand(name=Extensions.STAFF.value, description='Initialize Staff extension on this server')
    async def setup_staff(self,
                interaction : Interaction,
                staffer_role : Role = SlashOption(description="The role assigned to each staffer",required=True,autocomplete=True),
                inactive_role : Role = SlashOption(description="The role assigned to each staffer who is inactive",required=True,autocomplete=True)
                #staffer_commands_accessible_by : list[nextcord.Role] = nextcord.SlashOption(description="...",required=True,autocomplete=True)
            ):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                await self.db.setupExtension(interaction.guild,Extensions.STAFF,{
                    'active_role' : staffer_role.id,
                    'inactive_role' : inactive_role.id,
                    'inactive' : {}
                })
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(f'{Extensions.STAFF.value.capitalize()} extension installed successfully')

    @setup.subcommand(name=Extensions.VALQUIZ.value, description='Initialize ValorantQuiz extension on this server')
    async def setup_valquiz(self,
                            interaction : Interaction,
                ):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                await self.db.setupExtension(interaction.guild,Extensions.VALQUIZ,{
                    # Riempire con delle impostazioni...
                })
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(f'{Extensions.VALQUIZ.value.capitalize()} extension installed successfully')

    @setup.subcommand(name=Extensions.VERIFY.value, description="Initialize Verify extension on this server")
    async def setup_verify(self,
            interaction : Interaction
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                await self.db.setupExtension(interaction.guild,Extensions.VERIFY,{})
        except AssertionError as e:
            await interaction.followup.send(e)
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(f'{Extensions.VERIFY.value.capitalize()} extension installed successfully')

    @slash_command(name='teardown', description='Teardown a bot extension',default_member_permissions=permissions,dm_permission=False)
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