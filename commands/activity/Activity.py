from nextcord.ext import commands, tasks
from nextcord import \
    Status
import nextcord
import random

from utils.terminal import getlogger

logger = getlogger()


"""
activity = nextcord.Activity(
    #application_id=os.environ['APPLICATION_ID'],
    name="Ai ChatBot",
    state="/help",
    type=nextcord.ActivityType.playing,
    details="Details",
    #timestamps={ "start": int(time.time()), "end" : int(time.time()) + 1000},
    #assets={ "large_image": os.environ['LARGE_IMAGE'], "large_text": os.environ['LARGE_TEXT'] },
    #party={
        #"id" : 1234567890,
        #"size": [1, 1],
    #},
    buttons=[
        { "label" : "GitHub Repository", "url" : "https://github.com/GitGinocchio/GGsBot" },
        { "label" : "Developer", "url" : f"https://discord.com/users/{os.environ['DEVELOPER_ID']}" }
    ]
)
"""



class Activity(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.names = {
            '/help' : "Use /help  to see all available commands.",
            '/ask' : "Use /ask to ask a question and get an answer from GGsBot AI.",
            '/chat' : "Use /chat to chat with GGsBot AI.",
            '/image' : "Use /image to generate images with GGsBot AI.",
            '/level' : "Use /level to check your level and experience.",
            '/translate' : "Use /translate to translate a text from one language to another.",
            '/summarize' : "Use /summarize to summarize a text with GGsBot AI."
        }
        self.names_keys = list(self.names.keys())
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        activity = nextcord.Activity(
            type=nextcord.ActivityType.playing,
            name=(name:=random.choice(self.names_keys)),
            state=self.names[name]
        )
        logger.info(f"Setting bot activity to: {name}")
        await self.bot.change_presence(activity=activity)

    @tasks.loop(seconds=30)
    async def update_activity(self):
        activity = nextcord.Activity(
            type=nextcord.ActivityType.playing,
            name=(name:=random.choice(self.names_keys)),
            state=self.names[name]
        )
        logger.info(f"Changing bot activity to: {name}")
        await self.bot.change_presence(activity=activity)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Activity(bot))