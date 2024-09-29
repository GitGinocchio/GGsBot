from nextcord import SlashOption, Interaction, Permissions, SelectOption, Message
from nextcord.ext import commands
from nextcord.ui import Modal, TextInput, StringSelect
from typing import Callable
import nextcord
import requests
import os


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
        # Estrai i valori inseriti dall'utente
        max_length_value = self.max_length.value
        model_value = self.model.values[0]

        try:
            # Verifica che il max_length sia un numero valido
            max_length_int = int(max_length_value)
            assert max_length_int > 0, "Max Length must be a positive number."

            # Invia un messaggio con i dati inseriti
            await interaction.response.send_message(f"Max Length: {max_length_value}\nModel: {model_value}", ephemeral=True)

        except ValueError:
            # Errore nel caso in cui `max_length` non sia un numero
            await interaction.response.send_message("Max Length must be a valid number.", ephemeral=True)
        except AssertionError as e:
            # Errori di validazione personalizzati
            await interaction.response.send_message(str(e), ephemeral=True)

class Summarizer(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.api = f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/run/"

    """
    @nextcord.message_command(name='summarize')
    async def summarize_message(self,
                    interaction : Interaction,
                    message  : nextcord.Message
                ):
        try:
            assert message.clean_content != '', 'You must provide a valid text message to translate'
            view = SummarizerModel(self.summarize,message)
            await interaction.response.send_message(content='Fill out the translation form:', view=view,ephemeral=True)
        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True,delete_after=5)
    """

    @nextcord.slash_command(name='summarize',description="Summarize text using AI")
    async def summarize_text(self, 
                    interaction : nextcord.Interaction,
                    text : str = SlashOption(description="The text that you want to summarize",required=True),
                    max_length : int = SlashOption(description="The maximum length of the generated summary in characters",required=False,default=1024),
                    ephemeral : bool = SlashOption(description="Whether the response should be ephemeral or not",required=False,default=True),
                    model : str = SlashOption(description="The model to use",required=False,default='@cf/facebook/bart-large-cnn',choices=models)
                ):
        try:
            await interaction.response.defer(ephemeral=True)
            response = await self.summarize(text, max_length,model)

            assert response["success"], f"Error occured while translating (code: {response['errors']['code']}): {response['errors']['message']}"
        except AssertionError as e:
            await interaction.followup.send(e,ephemeral=True)
        else:
            await interaction.followup.send(response['result']['summary'],ephemeral=ephemeral)

    async def summarize(self, text : str, max_length : int, model : str):
        headers = {"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_KEY']}"}
        return requests.post(self.api + model, json={'input_text' : text, 'max_length' : max_length}, headers=headers).json()



def setup(bot : commands.Bot) -> None:
    bot.add_cog(Summarizer(bot))