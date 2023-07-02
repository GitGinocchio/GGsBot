import nextcord
from nextcord import Embed,Color,utils,channel,permissions
from discord.ext.tasks import loop
from nextcord.ext import commands
import random,asyncio,time,os,json

class json_utils:
    def __init__(self,fp: str = None,*,indent: int = 3):
        self.fp = fp
        self.indent = indent

    def content(self):
        with open(self.fp, 'r') as json_file:
            content = json.load(json_file)
            return content

    def save_to_file(self,content,indent: int = 3):
        with open(self.fp, 'w') as json_file:
            json.dump(content,json_file,indent=indent)

class Update(commands.Cog):
    def __init__(self,bot):
        super().__init__()
        self.saved_file = json_utils('./cogs/metadata/saved.json')
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.update_metadata()
        self.every_ten_seconds.start()

    @loop(hours=2)#@loop(hours=2)
    async def every_ten_seconds(self):
        self.update_metadata()

    def update_metadata(self):
        content = self.saved_file.content()
        try:
            last_update = str(time.strftime("%d-%m-%Y / %H:%M:%S"))
            guild = self.bot.guilds[0]
            server_name = str(guild.name)  # Nome del server
            member_count = sum(1 for member in guild.members if not member.bot)
            bot_count = sum(1 for member in guild.members if member.bot)
            role_count = len(guild.roles)

            content["tracked_server"] = server_name
            content["last_update"] = last_update
            content["counters"]["members"] = member_count
            content["counters"]["bots"] = bot_count
            content["counters"]["roles"] = role_count
        except IndexError as e:
            pass
        except Exception as e:
            print(e)
        else:
            self.saved_file.save_to_file(content)        

def setup(bot):
    bot.add_cog(Update(bot))

if __name__ == "__main__":
    os.system("python main.py")