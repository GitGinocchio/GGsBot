from nextcord.ext import commands
from nextcord import \
    WebhookMessage,  \
    SelectOption,    \
    Interaction,     \
    ButtonStyle,     \
    TextInputStyle,  \
    TextChannel,     \
    Embed,           \
    Member,          \
    Guild,           \
    Message,         \
    Role,            \
    NotFound,        \
    Forbidden,       \
    HTTPException,   \
    Colour
from nextcord.ui import \
    StringSelect,       \
    Modal,              \
    View,               \
    TextInput,          \
    Button,             \
    string_select,      \
    button
from datetime import datetime, timezone
from typing import Callable
from enum import StrEnum
import hashlib
import random

from utils.exceptions import ExtensionException
from utils.commons import Extensions
from utils.terminal import getlogger
from utils.commons import asyncget
from utils.db import Database

logger = getlogger()

class VerificationTypes(StrEnum):
    BUTTON = "button"
    QUESTION = "question"

class VerificationStatus(StrEnum):
    ALREADY_VERIFIED = "ALREADY_VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    VERIFIED = "VERIFIED"

class StartVerificationUI(Embed, View):
    modes = [SelectOption(label=type.value.capitalize(), value=type.value) for type in VerificationTypes]
    def __init__(self, bot : commands.Bot):
        View.__init__(self, timeout=None)
        Embed.__init__(self)
        self.description = "Select the verification mode you want to use to verify yourself (optional)\nClick **Start Verification** to begin."
        self.uis : dict[VerificationTypes, VerificationUI] = {
            VerificationTypes.BUTTON : ButtonVerificationUi,
            VerificationTypes.QUESTION : QuestionVerificationUi
        }
        self.colour = Colour.green()
        self.db = Database()
        self.bot = bot

        self.mode : VerificationTypes | None = None

        self.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)
        self.set_footer(text=f"Official verification message sent by {bot.user.name}", icon_url=bot.user.avatar.url)

    @string_select(placeholder="Select verification mode",custom_id='GGsBot:Verify::SelectMode', min_values=0, max_values=1, options=modes)
    async def select_mode_callback(self, select : StringSelect, interaction : Interaction):
        self.mode = select.values[0] if len(select.values) > 0 else None

    @button(label="Start Verification", style=ButtonStyle.primary, custom_id='GGsBot:Verify::StartVerification')
    async def start_verification(self, button : Button, interaction : Interaction):
        message = None
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                config, enabled = await self.db.getExtensionConfig(interaction.guild, Extensions.VERIFY)
            assert enabled, "Verification is not enabled for this server"

            if not self.mode:
                self.mode = random.choice(config['modes'])
            else:
                assert self.mode in config['modes'], f"This server does not allow verification with this method!"

            ui_type = self.uis.get(VerificationTypes(self.mode))

            if ui_type is not None:
                verified_role_id = config['verified_role']

                verified_role = interaction.guild.get_role(verified_role_id)

                ui : VerificationUI = ui_type(self.bot, verified_role)
                await ui.async_init()

                message = await interaction.followup.send(embed=ui, view=ui, wait=True, ephemeral=True)
                assert not await ui.wait(), f'The verification process has expired'

        except AssertionError as e:
            if message: await message.delete()
            await interaction.followup.send(e, ephemeral=True)
        except ExtensionException as e:
            if message: await message.delete()
            await interaction.followup.send(embed=e.asEmbed(), ephemeral=True)
        else:
            if ui.status == VerificationStatus.ALREADY_VERIFIED:
                await message.edit('You have already been verified!', view=None, embed=None, delete_after=5)
            elif ui.status == VerificationStatus.NOT_VERIFIED:
                await message.edit('Verification failed!', view=None, embed=None, delete_after=5)
            else:
                await message.edit(f'Verification completed successfully!', view=None, embed=None, delete_after=5)


class VerificationUI(Embed, View):
    def __init__(self,
            bot : commands.Bot,
            verified : Role | None = None,
        ):
        View.__init__(self, timeout=120)
        Embed.__init__(self)
        self.verified = verified
        self._status = VerificationStatus.NOT_VERIFIED

        self.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)
        self.set_footer(text=f"Official verification message sent by {bot.user.name}", icon_url=bot.user.avatar.url)

    @property
    def status(self): return self._status

    @status.setter
    def status(self, value : VerificationStatus): self._status = value

    async def async_init(self): pass

class ButtonVerificationUi(VerificationUI):
    def __init__(self,
            bot : commands.Bot,
            verified : Role | None = None
        ):
        VerificationUI.__init__(self, bot, verified)
        self.title = "Button Verification"
        self.description = "Click the button below to verify your account"

    @button(label="Verify",style=ButtonStyle.primary)
    async def verify(self, button: Button, interaction : Interaction):
        try:
            await interaction.user.add_roles(self.verified, reason="GGsBot::ButtonVerification")
        except Forbidden as e:
            logger.error(e)
        else:
            self.status = VerificationStatus.VERIFIED
        
        self.stop()

class QuestionVerificationUi(VerificationUI):
    def __init__(self,
            bot : commands.Bot,
            verified : Role | None = None
        ):
        VerificationUI.__init__(self, bot, verified)
        self.title = "Question Verification"
        self.description = "Press the button and answer the question to verify yourself"

        self.modal = self.QuestionModal(self.on_answer)

        self.question : str = None
        self.answers : list[str] = []

        self.add_field(
            name="Question",
            value="...",
            inline=False
        )

    class QuestionModal(Modal):
        def __init__(self, submit_callback : Callable[[Interaction, str], None]):
            Modal.__init__(self, "Question Verification")
            self.submit_callback = submit_callback


            self.user_input = TextInput(
                label="What’s the answer to the question?",
                placeholder="Type the answer here...",
                style=TextInputStyle.short,
                required=True
            )

            self.add_item(self.user_input)

        async def callback(self, interaction: Interaction):
            try:
                await self.submit_callback(interaction, self.user_input.value.strip().lower())
            except Exception as e:
                raise e

    @button(label="Answer", style=ButtonStyle.primary)
    async def answer_button(self, button : Button, interaction : Interaction):
        await interaction.response.send_modal(self.modal)

    async def async_init(self):
        response = await asyncget("https://api.textcaptcha.com/ggsbot.json")

        self.question = response['q']
        self.answers = response['a']

        self.set_field_at(0, name="Question", value=self.question)

    async def on_answer(self, interaction : Interaction, answer : str):
        encoded_answer = hashlib.md5(answer.strip().lower().encode()).hexdigest()

        if encoded_answer in self.answers:
            self.status = VerificationStatus.VERIFIED
            await interaction.user.add_roles(self.verified, reason="GGsBot::QuestionVerification")

        self.stop()