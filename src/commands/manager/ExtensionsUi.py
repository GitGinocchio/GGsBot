from nextcord.ui import \
    Modal,              \
    View,               \
    TextInput,          \
    Button,             \
    Item,               \
    RoleSelect,         \
    StringSelect,       \
    ChannelSelect,      \
    channel_select,     \
    string_select,      \
    role_select,        \
    button              \

from nextcord import \
    Forbidden,       \
    HTTPException,   \
    TextChannel,     \
    PermissionOverwrite, \
    Permissions,     \
    ChannelType,     \
    SelectOption,    \
    ButtonStyle,     \
    Interaction,     \
    Embed,           \
    Guild,           \
    Role,            \
    Colour             
from nextcord.abc import GuildChannel

from nextcord.ext.commands import Bot

from typing import Callable

from ..verify.VerificationUis import \
    VerificationTypes,               \
    StartVerificationUI

from utils.abc import SetupUI

class ExtensionUI(SetupUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str, submit_callback : Callable[[Interaction], None], timeout : int = 120):
        SetupUI.__init__(self, bot, guild, f'{extension.capitalize()} extension setup', submit_callback, "Setup", timeout)
        self.description = f"Setup process for {extension.capitalize()} extension"
        self.colour = Colour.green()

class AiChatBotUi(ExtensionUI):
    delays = [SelectOption(label=f'{n} Seconds', value=str(n), default=(True if n == 5 else False)) for n in range(1, 26,1)]
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        ExtensionUI.__init__(self, bot, guild, extension, self.on_submit)
        self.description = f"{super().description}, this extension allows you to have a chatbot Ai within your discord server"
        self.config = { 'chat-delay' : 0, 'threads' : {} }

        self.add_field(
            name="2. Chat Delay", 
            value="Select the delay of the chat with GGsBot Ai. (no choice=5 Seconds)"
        )

    @string_select(placeholder="2. Chat Delay", options=delays, min_values=1,row=1)
    async def select_delay(self, select: StringSelect, interaction : Interaction):
        self.config['chat-delay'] = (select.values[0] if len(select.values) != 0 else None)

    async def on_submit(self, interaction : Interaction):
        self.stop()

class GreetingsUi(ExtensionUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        ExtensionUI.__init__(self, bot, guild, extension, self.on_submit)
        self.description = f"{super().description}, This extension allows you to generate messages whenever a user joins the server"
        self.config = {'welcome_channel':None,'goodbye_channel':None}

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

    async def on_submit(self, interaction : Interaction):
        try:
            assert self.config.get('welcome_channel') is not None or self.config.get('goodbye_channel') is not None, "You must choose at least one welcome channel or one goodbye channel!"
        except AssertionError as e:
            await interaction.response.send_message(e, ephemeral=True, delete_after=5)
        except Exception as e:
            print(e)
        else:
            self.stop()

class TempVCUi(ExtensionUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        ExtensionUI.__init__(self, bot, guild, extension, self.on_submit)
        self.description = f"{super().description}, This extension allows you to transform voice channels into \"generators\" of temporary voice channels"
        self.config = {'listeners' : {}, 'channels' : {}}

    def on_submit(self, interaction : Interaction):
        self.stop()

class VerifyUi(ExtensionUI):
    modes = [SelectOption(label=type.value.capitalize(), value=type.value) for type in VerificationTypes]
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        ExtensionUI.__init__(self, bot, guild, extension, self.on_submit)
        self.description = f'{super().description}, this extension allows you to add a verification level of the account of users who enter within this server'
        self.config = { "modes" : [], 'verify_channel' : None, 'verify_message' : None, 'verified_role' : None}

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
            assert len(self.config.get('modes')), "You must choose at least one verification mode!"

            await self.ensure_everyone_permissions()

            verified_role = (self.guild.get_role(verified_role_id) if (verified_role_id:=self.config.get('verified_role')) else None)
            verify_channel = (self.guild.get_channel(verify_channel_id) if (verify_channel_id:=self.config.get('verify_channel')) else None)

            verified_role = await self.setup_verified_role(verified_role)
            verify_channel = await self.setup_verify_channel(verified_role, verify_channel)

            self.config['verify_channel'] = verify_channel.id
            self.config['verified_role'] = verified_role.id

            await self.send_verification_message(verify_channel)
        except AssertionError as e:
            await interaction.response.send_message(e, ephemeral=True, delete_after=5)
        except Forbidden as e:
            await interaction.response.send_message(e, ephemeral=True, delete_after=5)
        except Exception as e:
            print(e)
        else:
            self.stop()

class StaffUi(ExtensionUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        ExtensionUI.__init__(self, bot, guild, extension, self.on_submit)
        self.description = f"{super().description}, This extension allows you to assign staff members a role when they are inactive and why"
        self.config = { 'staff_role': None, 'inactive_role': None, 'inactive': {}}

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

    async def on_submit(self, interaction : Interaction):
        try:
            assert self.config.get('staff_role') is not None and self.config.get('inactive_role') is not None, "You must choose at least one staff role and one inactive role!"
            assert self.config.get('staff_role') != self.config.get('inactive_role'), "The staff role and inactive role cannot be the same!"
        except AssertionError as e:
            await interaction.response.send_message(e, ephemeral=True, delete_after=5)
        except Exception as e:
            print(e)
        else:
            self.stop()

class CheapGamesUi(ExtensionUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        ExtensionUI.__init__(self, bot, guild, extension, self.on_submit)
        self.description = f'{super().description}, This extension allows you to add commands and updates for free or discounted games for different types and platforms'
        self.config = { 'updates' : {} }

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
            value="The update interval is every 24h starting from a time chosen by you",
            inline=False
        )

    async def on_submit(self, interaction : Interaction):
        self.stop()