from nextcord.ext import commands
from nextcord import \
    Interaction,     \
    Message,         \
    slash_command

import pyttsx3
import gtts


class GTTS:
    def __init__(self):
        pass

class PYTTSX3:
    def __init__(self):
        pass


class TextToSpeech(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.engine = pyttsx3.init()
        self.bot = bot

    @slash_command("tts", "Write your message and the bot will convert it to speech.")
    async def tts(self, interaction : Interaction): pass


    @commands.Cog.listener()
    async def on_message(self, message: Message):
        pass








def setup(bot : commands.Bot):
    bot.add_cog(TextToSpeech(bot))