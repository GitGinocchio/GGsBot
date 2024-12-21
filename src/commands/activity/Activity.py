from nextcord.ext import commands, tasks
import nextcord
import random
import time
import os

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
        self.commands = list(self.names.keys())
        self.command : str = None
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self): 
        if not self.update_activity.is_running():
            self.update_activity.start()

    @tasks.loop(seconds=30)
    async def update_activity(self):
        try:
            activity = nextcord.Activity(
                type=ActivityType.playing,
                type=nextcord.ActivityType.playing,
                name=(name:=random.choice([n for n in self.commands if n != self.command] if self.command else self.commands)),
                state=self.names[name],
                details="testing",
                url="https://github.com/GitGinocchio/GGsBot",
                assets={ 
                    "large_image": "https://github.com/GitGinocchio/GGsBot/blob/main/docs/media/banner.png?raw=true", 
                    "large_text": "GGsBot", 
                    "small_image": "https://github.com/GitGinocchio/GGsBot/blob/main/docs/media/circular_icon.png?raw=true", 
                    "small_text": "GGsBot" 
                },
                buttons=[
                    { "label" : "GitHub Repository", "url" : "https://github.com/GitGinocchio/GGsBot" },
                    { "label" : "Developer", "url" : "https://github.com/GitGinocchio" }
                ],
                timestamps = { "start": int(time.time())}
            )

            self.command = name

            #logger.info(f"Changing bot activity to: {name}")
            await self.bot.change_presence(activity=activity)
        except Exception as e:
            logger.exception(e)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Activity(bot))