from nextcord import SlashOption, Interaction, Permissions, SelectOption, Message
from nextcord.ext import commands
from nextcord.ui import Modal, TextInput, StringSelect
from typing import Callable
import nextcord
import json
import os

from utils.exceptions import GGsBotException
from utils.commons import \
    GLOBAL_INTEGRATION,   \
    GUILD_INTEGRATION,    \
    USER_INTEGRATION,     \
    asyncget,             \
    asyncpost


models = [
    '@cf/facebook/bart-large-cnn'
]

permissions = Permissions(
    use_slash_commands=True
)

class SummarizerModel(Modal):
    def __init__(self, summarize_method : Callable, message : Message):
        super().__init__(title="Max Length & Model Selection")
        self.summarize_method = summarize_method
        self.message = message

        # Input per la lunghezza massima
        self.max_length = TextInput(
            label="Max Length",
            placeholder="Enter maximum length",
            required=True,
            min_length=10
        )
        self.add_item(self.max_length)

        # Input per il modello
        self.model = StringSelect(
            placeholder="Enter model to use",
            options=[SelectOption(label=model,value=model,default=(True if model == models[0] else False)) for model in models],
        )
        self.add_item(self.model)

    async def on_submit(self, interaction: Interaction):
        max_length_value = self.max_length.value
        model_value = self.model.values[0]

        try:
            max_length_int = int(max_length_value)

            if max_length_int < 0: 
                raise GGsBotException(
                    title="Argument Exception",
                    description="Max Length must be a positive number.",
                    suggestions="Please enter a positive number for Max Length and try again."
                )

            await interaction.response.send_message(f"Max Length: {max_length_value}\nModel: {model_value}", ephemeral=True)
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)

class Summarizer(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.api = f"https://gateway.ai.cloudflare.com/v1/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ggsbot-ai"

    @nextcord.message_command(name='summarize', integration_types=GLOBAL_INTEGRATION)
    async def summarize_message(self,
                    interaction : Interaction,
                    message  : nextcord.Message
                ):
        try:
            if message.clean_content == '':
                raise GGsBotException(
                    title="Argument Exception",
                    description="You must provide a valid text message to summarize",
                    suggestions="Please choose a message with text content and try again.",
                )

            view = SummarizerModel(self.summarize,message)
            await interaction.response.send_message(content='Fill out the translation form:', view=view,ephemeral=True)
        except GGsBotException as e:
            await interaction.response.send_message(embed=e.asEmbed(),ephemeral=True,delete_after=5)

    @nextcord.slash_command(name='summarize',description="Summarize text using AI", integration_types=GLOBAL_INTEGRATION)
    async def summarize_text(self, 
                    interaction : nextcord.Interaction,
                    text : str = SlashOption(description="The text that you want to summarize",required=True),
                    max_length : int = SlashOption(description="The maximum length of the generated summary in characters",required=False,default=1024),
                    ephemeral : bool = SlashOption(description="Whether the response should be ephemeral or not",required=False,default=True),
                    model : str = SlashOption(description="The model to use",required=False,default='@cf/facebook/bart-large-cnn',choices=models)
                ):
        try:
            await interaction.response.defer(ephemeral=ephemeral)
            response = await self.summarize(text, max_length,model)

        except GGsBotException as e:
            await interaction.followup.send(embed=e.asEmbed(), delete_after=5, ephemeral=True)
        else:
            await interaction.followup.send(response['result']['summary'])

    async def summarize(self, text : str, max_length : int, model : str):
        headers = {"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_KEY']}", 'Content-Type': 'application/json'}
        data = [
            {
                "provider": "workers-ai",
                "endpoint": model,
                "headers" : headers,
                "query" : {
                    "input_text" : text,
                    "max_length" : max_length
                }
            }
        ]

        content_type, content, code, reason = await asyncpost(self.api, json=data, headers=headers)

        if code != 200 or content_type != "application/json":
            raise GGsBotException(
                title="Summarization failed",
                description=f"Failed to summarize the text. Status code: {code} Reason: {reason}",
                suggestions="Try again later or contact the support team.",
            )

        return json.loads(content)




def setup(bot : commands.Bot) -> None:
    bot.add_cog(Summarizer(bot))