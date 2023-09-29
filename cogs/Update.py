import nextcord
from nextcord import Embed,Color,utils,channel,permissions,Member
from nextcord.ext import commands,tasks
from datetime import datetime,timedelta
from jsonutils import jsonfile


class Update(commands.Cog):
    content = jsonfile('./cogs/metadata/saved.json')
    def __init__(self,bot):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if len(self.bot.guilds) > 1:
            for guild in self.bot.guilds:
                if guild.name != self.content["tracked_server_name"] or guild.id != self.content["tracked_server_id"]:
                    print('warning: Bot is in another server!',' name: ',guild.name,' id: ',guild.id)
                    await guild.leave()

        self.update_metadata()
        if not self.every.is_running(): self.every.start()

    @tasks.loop(hours=content["updatetime-h-m-s"][0],minutes=content["updatetime-h-m-s"][1],seconds=content["updatetime-h-m-s"][2])
    async def every(self):
        print(f'[{str(datetime.utcnow() + timedelta(hours=2))}] - Updating Metadata...')
        self.update_metadata()

    def update_metadata(self):
        try:
            guild = self.bot.guilds[0]
            self.content["tracked_server_name"] = guild.name
            self.content['tracked_server_id'] = guild.id
            self.content["last_update"] = str(datetime.utcnow() + timedelta(hours=2))
            self.content["counters"]["members"] = sum(1 for member in guild.members if not member.bot)
            self.content["counters"]["bots"] = sum(1 for member in guild.members if member.bot)
            self.content["counters"]["roles"] =  len(guild.roles)
        except IndexError as e: pass
        except Exception as e: print(e)
        else: self.content.save()

def setup(bot):
    bot.add_cog(Update(bot))
