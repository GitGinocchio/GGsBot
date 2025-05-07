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
from cachetools import TTLCache
from typing import Callable
import json
import os

from utils.terminal import getlogger
from utils.exceptions import GGsBotException
from utils.commons import \
    GLOBAL_INTEGRATION,   \
    GUILD_INTEGRATION,    \
    USER_INTEGRATION,     \
    asyncget,             \
    asyncpost


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

# TODO: Sostituire questa view con una GGsBot Page
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

            if not self.to_lang or not self.model:
                raise GGsBotException(
                    title="Argument Exception",
                    description="You must provide languages to translate from and to!",
                    suggestions="Please provide all required arguments and try again."
                )
            elif self.from_lang == self.to_lang:
                raise GGsBotException(
                    title="Argument Exception",
                    description="You can't translate a text into the same language it is in",
                    suggestions="Please choose a different languages for translation.",
                )

            await interaction.edit_original_message(
                content=f'Translating from **{self.from_lang.capitalize()}** to **{self.to_lang.capitalize()}**...' 
                        if self.from_lang else \
                        f'Translating into **{self.to_lang.capitalize()}**...',
                view=None)

            self.response = await self.translation_method(
                userid=interaction.user.id,
                text=self.message.clean_content,
                from_lang=self.from_lang,
                to_lang=self.to_lang,
                model=self.model
            )
        except GGsBotException as e:
            await interaction.edit_original_message(embed=e.asEmbed())
        else:
            await interaction.edit_original_message(content=self.response['result']['translated_text'],view=None)

class Translator(commands.Cog):
    def __init__(self, bot : commands.Bot) -> None:
        self.api = f"https://gateway.ai.cloudflare.com/v1/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ggsbot-ai"
        self.requests_cache = TTLCache(maxsize=10000, ttl=86400)
        self.requests_limit = 20
        self.bot = bot

    @message_command(name="translate",default_member_permissions=permissions, integration_types=GLOBAL_INTEGRATION)
    async def translate_message(self,
                                interaction : Interaction,
                                message : Message
                                ):
        try:
            if message.clean_content == '':
                raise GGsBotException(
                    title="Argument Exception",
                    description="You must provide a valid text message to translate",
                    suggestions="Please choose a message with text content and try again.",
                )
            
            view = TranslationForm(self.translate,message)
            await interaction.response.send_message(content='Fill out the translation form:', view=view,ephemeral=True)
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(),ephemeral=True,delete_after=5)

    @slash_command(name="translate", description="Translate a given text to language using AI",default_member_permissions=permissions, integration_types=GLOBAL_INTEGRATION)
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
            if from_lang == to_lang:
                raise GGsBotException(
                    title="Argument Exception",
                    description="You can't translate a text into the same language it is in",
                    suggestions="Please choose a different languages for translation.",
                )

            response = await self.translate(userid=interaction.user.id, text=text,from_lang=from_lang,to_lang=to_lang,model=model)
        except GGsBotException as e:
            if e.code != 0: logger.error(e)
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(response['result']['translated_text'])

    async def translate(self, userid: int, text : str, to_lang : str, model : str, from_lang : str | None = None):
        # NOTE: The default value is -1 because we want to check if the user has made any requests before. 
        #       If they haven't, then we set it to 1. If they have, then we increment it by 1.
        if (user_requests:=self.requests_cache.get(userid, -1)) >= self.requests_limit:
            raise GGsBotException(
                title="Daily limit reached!",
                description="You have reached your daily limit of requests.",
                suggestions="Please try again after 24 hours, or if you think this is an error contact support."
            )
        
        self.requests_cache[userid] = user_requests + 1 if user_requests != -1 else 1
        
        headers = {"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_KEY']}", 'Content-Type': 'application/json'}
        data = [
            {
                "provider": "workers-ai",
                "endpoint": model,
                "headers" : headers,
                "query" : {
                    "text" : text,
                    "target_lang" : to_lang
                }
            }
        ]

        if from_lang is not None: data[0]["query"]['source_lang'] = from_lang

        content_type, content, code, reason = await asyncpost(self.api, json=data, headers=headers)

        if code != 200 or content_type != 'application/json':
            raise GGsBotException(
                code = 0,
                title="Translation Api Exception",
                description=f"Failed to translated text (code: {code}): {reason}",
                suggestions="Try again later or contact support."
            )
        
        return json.loads(content)

def setup(bot: commands.Bot): 
    bot.add_cog(Translator(bot))