from nextcord.ext import commands
from nextcord import \
    Permissions,     \
    Interaction,     \
    Message,         \
    SlashOption,     \
    SelectOption,    \
    ButtonStyle,     \
    slash_command,   \
    message_command  \

from nextcord.ui import \
    View,               \
    StringSelect,       \
    Button,             \
    string_select,      \
    button
from typing import Callable
import requests
import os

from utils.terminal import getlogger

logger = getlogger()

permissions = Permissions(
    use_slash_commands=True
)

models = [
    '@cf/meta/m2m100-1.2b'
]

languages = [
    'english',
    'spanish',
    'french',
    'german',
    'italian',
    'portuguese',
    'arabic',
    'chinese',
    'japanese',
    'korean',
    'hindi',
    'russian',
    'dutch',
    'turkish',
    'swedish',
    'norwegian',
    'finnish',
    'danish',
    'greek',
    'hungarian',
    'thai',
    'vietnamese',
    'filipino',
    'swahili',
    'hebrew',
]

class TranslationForm(View):
    def __init__(self, translation_method : Callable, message : Message):
        super().__init__()
        self.translation_method = translation_method
        self.message = message

        self.from_lang = None
        self.to_lang = 'english'
        self.model = models[0]
        self.response = None

    @string_select(placeholder='Enter language to translate from (optional)', options=[SelectOption(label=lang.capitalize(),value=lang) for lang in languages],min_values=0)
    async def from_lang_select(self, select : StringSelect, interaction : Interaction):
        self.from_lang = select.values[0]

    @string_select(placeholder='Enter language to translate to', options=[SelectOption(label=lang.capitalize(),value=lang, default=(True if lang == 'english' else False)) for lang in languages])
    async def to_lang_select(self, select : StringSelect, interaction : Interaction):
        self.to_lang = select.values[0]

    @string_select(placeholder='Enter model to use', options=[SelectOption(label=model,value=model, default=(True if model == models[0] else False)) for model in models])
    async def model_select(self, select : StringSelect, interaction : Interaction):
        self.model = select.values[0]

    @button(label="Submit", style=ButtonStyle.primary, row=3)
    async def submit(self, button : Button, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            assert self.to_lang and self.model,'You must provide languages to translate from and to!'
            assert self.from_lang != self.to_lang, "You can't translate a text into the same language it is in"

            await interaction.edit_original_message(
                content=f'Translating from **{self.from_lang.capitalize()}** to **{self.to_lang.capitalize()}**...' 
                        if self.from_lang else \
                        f'Translating into **{self.to_lang.capitalize()}**...',
                view=None)

            self.response = await self.translation_method(
                                        text=self.message.clean_content,
                                        from_lang=self.from_lang,
                                        to_lang=self.to_lang,
                                        model=self.model
                                        )


            assert self.response["success"], f"Error occured while translating (code: {self.response['errors']['code']}): {self.response['errors']['message']}"
        except AssertionError as e:
            await interaction.edit_original_message(content=f'Fill out the translation form:\n{e}')
            #await interaction.followup.send(e, ephemeral=True)
        else:
            await interaction.edit_original_message(content=self.response['result']['translated_text'],view=None)

class Translator(commands.Cog):
    def __init__(self, bot : commands.Bot) -> None:
        self.api = f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/run/"
        self.bot = bot

    @message_command(name="translate",default_member_permissions=permissions, dm_permission=True)
    async def translate_message(self,
                                interaction : Interaction,
                                message : Message
                                ):
        try:
            assert message.clean_content != '', 'You must provide a valid text message to translate'
            view = TranslationForm(self.translate,message)
            await interaction.response.send_message(content='Fill out the translation form:', view=view,ephemeral=True)
        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True,delete_after=5)

    @slash_command(name="translate", description="Translate a given text to language using AI",default_member_permissions=permissions, dm_permission=True)
    async def translate_text(self, 
                interaction : Interaction,
                text : str = SlashOption(description="Text to translate",required=True),
                to_lang : str = SlashOption(name='to',description='Language to translate to',required=True,choices=languages),
                from_lang : str = SlashOption(name='from',description="Language to translate from",required=False,choices=languages,default=None),
                ephemeral : bool = SlashOption(name='ephemeral',description="Whether or not to send the translated text as an ephemeral message",required=False,default=True),
                model : str = SlashOption(description="Model to use",required=False,choices=models,default='@cf/meta/m2m100-1.2b')
                ) -> str:
        try:
            await interaction.response.defer(ephemeral=ephemeral)
            assert from_lang != to_lang, "You can't translate a text into the same language it is in"

            response = await self.translate(
                                    text=text,
                                    from_lang=from_lang,
                                    to_lang=to_lang,
                                    model=model
                                )

            assert response["success"], f"Error occured while translating (code: {response['errors'][0]['code']}): {response['errors'][0]['message']}"
        except AssertionError as e:
            await interaction.followup.send(e)
        else:
            await interaction.followup.send(response['result']['translated_text'])

    async def translate(self, text : str, to_lang : str, model : str, from_lang : str | None = None):
        headers = {"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_KEY']}"}

        payload = {'text' : text,'target_lang' : to_lang}
        if from_lang is not None: payload['source_lang'] = from_lang

        return requests.post(self.api + model, json=payload, headers=headers).json()

def setup(bot: commands.Bot): 
    bot.add_cog(Translator(bot))