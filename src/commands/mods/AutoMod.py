from nextcord.ext import commands
from nextcord.errors import Forbidden
from datetime import datetime, timedelta, timezone
from cachetools import LRUCache
from nextcord import \
    TextChannel,     \
    User,            \
    Guild,           \
    Member,          \
    Message,         \
    Member,          \
    SlashOption,     \
    Interaction,     \
    slash_command
import requests
import asyncio
import os

from utils.terminal import getlogger

models = [
    '@cf/huggingface/distilbert-sst-2-int8'
]

translation_model = '@cf/meta/m2m100-1.2b'
punctuation_marks = [":", ".", ",", "/", "?", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "=", "+", "[", "]", "{", "}", ";", "'", '"', "\\", "|", "<", ">", "~", "`"]

logger = getlogger()

session = requests.Session()

class AutoMod(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.cache : dict[User | Member,dict] = LRUCache(1000)
        self.bot = bot

    # Aggiungere avvisi e timeout se azioni ripetute nel tempo
    # Aggiungere comandi per la configurazione
    # Aggiungere piu' controlli perche' troppo esagerati...
    # Aggiungere una lista di parole bannate

    async def evaluate_message(self, message : Message):
        try:
            api = f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/run/"
            headers = { "Authorization": f"Bearer {os.environ['CLOUDFLARE_API_KEY']}" }

            translated : requests.Response = session.post(api + translation_model, json={'text' : message.clean_content, 'target_lang' : 'english'}, headers=headers).json()

            assert translated["success"], f"Error occured while translating (code: {translated['errors'][0]['code']}): {translated['errors'][0]['message']}"

            table = str.maketrans('','', ''.join(punctuation_marks))
            text = translated['result']['translated_text'].translate(table).lower()

            response : requests.Response = session.post(api + models[0], json={'text' : text}, headers=headers).json()
        except Exception as e:
            logger.error(e)
        else:
            return (response, message)

    async def send_timeout(self, message : Message, time : timedelta, reason : str):
        try:
            timeout = datetime.now(timezone.utc) + time
            await message.author.timeout(timeout)
        except Forbidden as e:
            logger.warning(f'Unable to timeout user {message.author.name}({message.author.mention}): {e}')
        else:
            await message.reply(reason)

    async def on_message_evaluated(self, future : asyncio.Future):
        try:
            result = future.result()
            response : requests.Response = result[0]
            message : Message = result[1]

            assert response["success"], f"Error occurred while moderating this message (code: {response['errors'][0]['code']}): {response['errors']['message']}"

            negative : float = response["result"][0]['score']
            positive : float = response["result"][1]['score']

            logger.info(f'{message.author.name}({message.author.mention}) [{negative * 100:.2f}% ({negative}) negative, {positive * 100:.2f}% ({positive}) positive]: {message.clean_content}')

            if negative > 0.95:
                await self.send_timeout(message, timedelta(minutes=5), f'This message has been flagged as {negative * 100:.2f}% negative, you will take a timeout')
        except AssertionError as e:
            await message.reply(e)
            logger.warning(e)

    @commands.Cog.listener()
    async def on_message(self, message : Message) -> None:
        if message.author.id == self.bot.user.id: return
        try:
            n = 0
            if (last:=self.cache.get(message.author)) and (datetime.now(timezone.utc) - last['datetime']).total_seconds() < 3:
                n = int(last['times']) + 1

                if n >= 5:
                    await message.author.send(f'{message.author.mention} you\'re sending too many messages too quickly, slow down!')
                    await self.send_timeout(message, timedelta(seconds=6*n),f'{message.author.mention} you\'re sending messages too quickly, slow down!')
                    n = 0

            self.cache[message.author] = {'datetime' : message.created_at, 'times' : n}

            task = asyncio.create_task(self.evaluate_message(message))

            task.add_done_callback(lambda future: asyncio.create_task(self.on_message_evaluated(future)))
        except AssertionError as e:
            await message.reply(e)
            logger.warning(e)

def setup(bot : commands.Bot):
    bot.add_cog(AutoMod(bot))