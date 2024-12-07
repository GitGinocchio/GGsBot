from nextcord.ext import commands
from nextcord import \
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
    Modal,              \
    View,               \
    TextInput,          \
    Button,             \
    button
from datetime import datetime, timezone
from typing import Callable
from enum import StrEnum
import hashlib

from utils.exceptions import ExtensionException
from utils.terminal import getlogger
from utils.commons import asyncget

logger = getlogger()

class VerificationTypes(StrEnum):
    BUTTON = "button"
    QUESTION = "question"

class VerificationStatus(StrEnum):
    ALREADY_VERIFIED = "ALREADY_VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    VERIFIED = "VERIFIED"

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