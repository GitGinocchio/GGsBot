from nextcord.ui import \
    RoleSelect,         \
    StringSelect,       \
    ChannelSelect,      \
    channel_select,     \
    string_select,      \
    role_select         \

from nextcord import \
    Forbidden,       \
    TextChannel,     \
    PermissionOverwrite, \
    Permissions,     \
    ChannelType,     \
    SelectOption,    \
    Interaction,     \
    Guild,           \
    Role,            \
    Colour             

from nextcord.ext.commands import Bot
from typing import Callable

from ..verify.VerificationUis import \
    VerificationTypes,               \
    StartVerificationUI

from utils.abc import UI, UiPage, UiSubmitPage
from utils.exceptions import \
    GGsBotException
from utils.terminal import getlogger

logger = getlogger()

# NOTE: il parametro extension viene passato automaticamente alle pagine e alle UI

# NOTE: Sostituire .on_submit con una sottoclasse di Button

class SetupUI(UI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        UI.__init__(self, bot, guild)
        self.extension = extension

        self.set_submit_page(self.DefaultSetupSubmitPage)

    class DefaultSetupSubmitPage(UiSubmitPage):
        def __init__(self, ui : 'SetupUI', extension : str):
            UiSubmitPage.__init__(self, ui, submit_title="Setup")
            self.description = f"Clicking Setup will confirm all saved settings so far and install the {extension.capitalize()} extension on the server, do you want to continue?"
            self.colour = Colour.green()

class AiChatBotSetupUI(SetupUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        SetupUI.__init__(self, bot, guild, extension)
        self.config = { 'chat-delay' : 10, 'threads' : {}, 'allowed-channels' : []}
        self.add_pages(self.AiChatBotPage)
    
    class AiChatBotPage(UiPage):
        delays = [SelectOption(label=f'{n} Seconds', value=str(n), default=(True if n == 10 else False)) for n in range(1, 26,1)]
        def __init__(self, ui : UI, extension : str):
            UiPage.__init__(self, ui)
            self.description = f"This extension allows you to have a chatbot Ai within your discord server"
            self.colour = Colour.green()

            self.add_field(
                name="1. Allowed Channels",
                value="Select the channels where GGsBot Ai should be active. (no choice=All Channels)",
                inline=False
            )

            self.add_field(
                name="2. Chat Delay", 
                value="Select the delay of the chat with GGsBot Ai. (no choice=10 Seconds)",
                inline=False
            )

        @channel_select(placeholder="1. Allowed Channels", channel_types=[ChannelType.text, ChannelType.news])
        async def select_channels(self, select : ChannelSelect, interaction : Interaction):
            self.config['allowed-channels'] = [channel.id for channel in select.values.channels]

        @string_select(placeholder="2. Chat Delay", options=delays, min_values=1,row=1, disabled=True)
        async def select_delay(self, select: StringSelect, interaction : Interaction):
            self.config['chat-delay'] = (select.values[0] if len(select.values) != 0 else None)

        async def on_next(self, interaction : Interaction):
            try:
                if len(self.config.get('allowed-channels')) == 0:
                    raise GGsBotException(
                        title="Missing Argument",
                        description="You must choose at least one allowed channel!",
                        suggestions="Choose an allowed channel and try again.",
                    )
            except GGsBotException as e:
                await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)
            else:
                await super().on_next(interaction)

class GreetingsSetupUI(SetupUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        SetupUI.__init__(self, bot, guild, extension)
        self.config = { 'welcome_channel' : None, 'goodbye_channel' : None}
        self.add_pages(self.GreetingsPage)

    class GreetingsPage(UiPage):
        def __init__(self, ui : UI, extension : str):
            UiPage.__init__(self, ui)
            self.description = f"This extension allows you to generate messages whenever a user joins the server"
            
            self.add_field(
                name="1. Welcome Channel",
                value="Choose the text channel where welcome messages will be sent\n(no choice=no channel)",
                inline=False
            )

            self.add_field(
                name="2. Goodbye Channel", 
                value="Choose the text channel where goodbye messages will be sent\n(no choice=no channel)"
            )

        @channel_select(placeholder="1. Welcome Channel",channel_types=[ChannelType.text], min_values=0, row=1)
        async def welcome_channel(self, select: ChannelSelect, interaction : Interaction):
            self.config['welcome_channel'] = (select.values[0].id if len(select.values) > 0 else None)

        @channel_select(placeholder="2. Goodbye Channel",channel_types=[ChannelType.text], min_values=0, row=2)
        async def goodbye_channel(self, select: ChannelSelect, interaction : Interaction):
            self.config['goodbye_channel'] = (select.values[0].id if len(select.values) > 0 else None)

        async def on_next(self, interaction : Interaction):
            try:
                if self.config.get('welcome_channel') == None and self.config.get('goodbye_channel') == None:
                    raise GGsBotException(
                        title="Missing Argument",
                        description="You must choose at least one welcome channel or one goodbye channel!",
                        suggestions="Choose a welcome channel or a goodbye channel and try again.",
                    )
            except GGsBotException as e:
                await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)
            else:
                await super().on_next(interaction)

class TempVCSetupUI(SetupUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        SetupUI.__init__(self, bot, guild, extension)
        self.config = { 'listeners' : {}, 'channels' : {} }
        self.add_pages(self.TempVCPage)

    class TempVCPage(UiPage):
        def __init__(self, ui : UI, extension : str):
            UiPage.__init__(self, ui)
            self.description = "This extension allows you to transform voice channels into \"generators\" of temporary voice channels"

class VerifySetupUI(SetupUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        SetupUI.__init__(self, bot, guild, extension)
        self.config = { "modes" : [], 'verify_channel' : None, 'verify_message' : None, 'verified_role' : None}
        self.set_submit_page(self.VerifySubmitPage)
        self.add_pages(self.VerifyPage)

    class VerifyPage(UiPage):
        modes = [SelectOption(label=type.value.capitalize(), value=type.value) for type in VerificationTypes]
        def __init__(self, ui : SetupUI, extension : str):
            UiPage.__init__(self, ui)
            self.description = f'This extension allows you to add a verification level of the account of users who enter within this server'
            self.colour = Colour.green()

            self.add_field(
                name="1. Verification Channel", 
                value="Choose the text channel where verification messages will be sent\n(no choice=create one)",
                inline=False
            )

            self.add_field(
                name="2. Verified Role", 
                value="Choose the role that will be given to users who verify\n(no choice=create one)",
                inline=False
            )

            self.add_field(
                name="3. Allowed verification modes", 
                value="Select which verification modes you want to enable.\n(Each member can choose from one of these modes to verify)",
                inline=False
            )

        @channel_select(placeholder="1. Verification Channel",channel_types=[ChannelType.text], min_values=0, row=1)
        async def verify_channel(self, select: ChannelSelect, interaction : Interaction):
            self.config['verify_channel'] = (select.values[0].id if len(select.values) > 0 else None)
        
        @role_select(placeholder="2. Verified Role", min_values=0, row=2)
        async def verified_role(self, select: RoleSelect, interaction : Interaction):
            self.config['verified_role'] = (select.values[0].id if len(select.values) > 0 else None)

        @string_select(placeholder="3. Allowed verification modes",min_values=1, max_values=len(modes), options=modes, row=3)
        async def verification_modes(self, select: StringSelect, interaction : Interaction):
            self.config['modes'] = select.values

        async def on_next(self, interaction : Interaction):
            try:
                if len(self.config.get('modes', [])) == 0:
                    raise GGsBotException(
                        title="Missing Argument",
                        description="You must select at least one verification mode",
                        suggestions="Select at least one verification mode and try again",
                    )
            except GGsBotException as e:
                await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)
            else:
                await super().on_next(interaction)
        
    class VerifySubmitPage(UiSubmitPage):
        def __init__(self, ui : UI, extension : str):
            UiSubmitPage.__init__(self, ui)
            self.description = f"Clicking Setup will confirm all saved settings so far and install the {extension.capitalize()} extension on the server, do you want to continue?"
            self.colour = Colour.green()

        async def setup_verified_role(self, role : Role | None = None):
            if role == None:
                role = await self.guild.create_role(
                    name=f"Verified by {self.bot.user.name}",
                    colour=Colour.green(),
                    permissions=Permissions(view_channel=True),
                    reason="GGsBot:Verify"
                )
            else:
                role.permissions.update(view_channel=True)
                role = await role.edit(permissions=role.permissions, reason="GGsBot:Verify")
            return role

        async def setup_verify_channel(self, verified_role : Role, verify_channel : TextChannel | None = None):
            overwrites = {
                self.guild.default_role: PermissionOverwrite(view_channel=True,read_message_history=True),
                verified_role: PermissionOverwrite(view_channel=False)
            }
            
            if verify_channel == None:
                channel = await self.guild.create_text_channel(
                    name=f"verify",
                    reason="GGsBot:Verify",
                    position=0,
                    overwrites=overwrites
                )
            else:
                channel = await verify_channel.edit(overwrites=overwrites, reason="GGsBot:Verify")
            return channel

        async def ensure_everyone_permissions(self):
            await self.guild.default_role.edit(
                reason="GGsBot:Verify",
                permissions=Permissions.none()
            )

        async def send_verification_message(self, channel : TextChannel):
            ui = StartVerificationUI(self.bot)
            message = await channel.send(embed=ui, view=ui)
            self.config['verify_message'] = message.id

        async def on_submit(self, interaction : Interaction):
            try:
                await self.ensure_everyone_permissions()

                verified_role = (self.guild.get_role(verified_role_id) if (verified_role_id:=self.config.get('verified_role')) else None)
                verify_channel = (self.guild.get_channel(verify_channel_id) if (verify_channel_id:=self.config.get('verify_channel')) else None)

                verified_role = await self.setup_verified_role(verified_role)
                verify_channel = await self.setup_verify_channel(verified_role, verify_channel)

                self.config['verify_channel'] = verify_channel.id
                self.config['verified_role'] = verified_role.id

                await self.send_verification_message(verify_channel)
            except Exception as e:
                logger.exception(e)
            else:
                self.stop()

class StaffSetupUI(SetupUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        SetupUI.__init__(self, bot, guild, extension)
        self.config = {'staff_role': None, 'inactive_role': None, 'inactive': {}}

        self.add_pages(self.StaffPage)

    class StaffPage(UiPage):
        def __init__(self, ui : UI, extension : str):
            UiPage.__init__(self, ui)
            self.description = f"This extension allows you to assign staff members a role when they are inactive and why"
            self.colour = Colour.green()

            self.add_field(
                name="1. Staff Role",
                value="The role assigned to each staff member",
                inline=False
            )

            self.add_field(
                name="2. Inactive Role",
                value="The role assigned to each inactive staff member"
            )

        @role_select(placeholder="1. Staff Role",min_values=1, row=1)
        async def staff_role(self, select: RoleSelect, interaction : Interaction):
            self.config['staff_role'] = (select.values[0].id if len(select.values) > 0 else None)

        @role_select(placeholder="2. Inactive Role",min_values=1, row=2)
        async def inactive_role(self, select: RoleSelect, interaction : Interaction):
            self.config['inactive_role'] = (select.values[0].id if len(select.values) > 0 else None)

        async def on_next(self, interaction : Interaction):
            try:
                if self.config.get('staff_role') == None and self.config.get('inactive_role') == None:
                    raise GGsBotException(
                        title="Missing Argument",
                        description="You must choose at least one staff role and one inactive role!",
                    )
                elif self.config.get('staff_role') == self.config.get('inactive_role'):
                    raise GGsBotException(
                        title="Invalid Argument",
                        description="Staff Role and Inactive Role cannot be the same!",
                        suggestions="Choose a different role for the staff role or Inactive Role.",
                    )
            except GGsBotException as e:
                await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)
            else:
                self.stop()
    
class CheapGamesSetupUI(SetupUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        SetupUI.__init__(self, bot, guild, extension)
        self.config = { 'updates' : {} }
        self.add_pages(self.CheapGamesPage)
    
    class CheapGamesPage(UiPage):
        def __init__(self, ui : UI, extension : str):
            UiPage.__init__(self, ui)
            self.colour = Colour.green()
            
            self.add_field(
                name="Updates",
                value="This extension allows you to create more game updates (also by channel) based on different conditions and types such as deals and giveaways",
                inline=False
            )

            self.add_field(
                name="Conditions",
                value="You can define conditions such as price range, platform (such as Steam or Epic Games), and other criteria to determine which updates are considered valid for an extension to be used by different users",
                inline=False
            )

            self.add_field(
                name="Update interval",
                value="Updates will be sent every hour",
                inline=False
            )