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

from utils.abc import UI, Page, SubmitPage

class SetupUI(UI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        UI.__init__(self, bot, guild, extension)

    class SetupSubmitPage(SubmitPage):
        def __init__(self, ui : 'SetupUI', extension : str):
            SubmitPage.__init__(self, ui, extension, submit_title="Setup")
            self.description = f"Clicking Setup will confirm all saved settings so far and install the {self.extension.capitalize()} extension on the server, do you want to continue?"
            self.colour = Colour.green()

class AiChatBotSetupUI(SetupUI):
    def __init__(self, bot : Bot, guild : Guild, extension : str):
        SetupUI.__init__(self, bot, guild, extension)
    
    class AiChatBotPage(Page):
        delays = [SelectOption(label=f'{n} Seconds', value=str(n), default=(True if n == 5 else False)) for n in range(1, 26,1)]
        def __init__(self, ui : UI, extension : str):
            Page.__init__(self, ui, extension)
            self.description = f"This extension allows you to have a chatbot Ai within your discord server"
            self.ui.config = { 'chat-delay' : 5, 'threads' : {} }
            self.colour = Colour.green()

            self.add_field(
                name="2. Chat Delay", 
                value="Select the delay of the chat with GGsBot Ai. (no choice=5 Seconds)"
            )

        @string_select(placeholder="2. Chat Delay", options=delays, min_values=1,row=1)
        async def select_delay(self, select: StringSelect, interaction : Interaction):
            self.ui.config['chat-delay'] = (select.values[0] if len(select.values) != 0 else None)

