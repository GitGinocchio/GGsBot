from nextcord import Embed,Color,utils,channel,Permissions,Interaction,User, Member
from nextcord.ext import commands, tasks
import datetime
import nextcord
import asyncio
import os

from utils.db import Database, ExtensionException
from utils.commons import Extensions
from utils.jsonfile import JsonFile, _JsonDict
from utils.terminal import getlogger

logger = getlogger()

staff_permissions = Permissions(
    use_slash_commands=True
)

class StaffCommands(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.db = Database()
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.schedule_periodic_task())

    @nextcord.slash_command('staff',"Set of useful commands to set or view the status of staffers",default_member_permissions=staff_permissions,dm_permission=False)
    async def staff(self, interaction : nextcord.Interaction): pass

    @staff.subcommand('show',"Show a list of active and/or inactive staffers")
    async def show(self, 
                   interaction : nextcord.Interaction, 
                   status : str = nextcord.SlashOption("status","Whether to show only active staffers, inactive staffers, or both",required=True,choices=['active','inactive','both'],default='both')
                ):
        await interaction.response.defer(ephemeral=True)
        try:
            async with self.db:
                config = await self.db.getExtensionConfig(interaction.guild,Extensions.STAFF)

            staffer_role = nextcord.utils.get(interaction.guild.roles, id=config['active_role'])
            inactive_role = nextcord.utils.get(interaction.guild.roles, id=config['inactive_role'])

            inactive_staffers = [(inactive,config['inactive'][staffer]['reason'],config['inactive'][staffer]['timestamp']) for staffer in config['inactive'].keys() if (inactive:=interaction.guild.get_member(int(staffer))) is not None]

            active_staffers = [member for member in interaction.guild.members if staffer_role in member.roles and not inactive_role in member.roles]

            embed = Embed(title="Staffers Status",description="Information on who and how many active and inactive staffers there are",timestamp=datetime.datetime.now(datetime.UTC))

            embed.set_author(name=interaction.user.display_name,icon_url=interaction.user.avatar.url)

            embed.add_field(name="Total Staffers",value=f"{len(inactive_staffers+active_staffers)} Staffers", inline=True)

            embed.add_field(name="Active Staffers",value=f"{len(active_staffers)} Staffers", inline=True)

            embed.add_field(name="Inactive Staffers",value=f"{len(inactive_staffers)} Staffers", inline=True)

            if status == 'active' or status == 'both':
                if len(active_staffers) > 0:
                    embed.add_field(name="Active Staffers",value="\n".join(f'<@{staffer.id}>' for staffer in active_staffers),inline=False)
                else:
                    embed.add_field(name="Active Staffers",value="There are no active staffers at the moment",inline=False)
            
            if status == 'inactive' or status == 'both':
                if len(inactive_staffers) > 0:
                    embed.add_field(name="Inactive Staffers",value="",inline=False)
                    for staffer, reason, timestamp in inactive_staffers:
                        embed.add_field(name="User",value=f"<@{staffer.id}>",inline=True)
                        embed.add_field(name="Until", value=datetime.datetime.fromtimestamp(float(timestamp)).strftime("%d/%m/%Y") if timestamp else 'Not Given',inline=True)
                        embed.add_field(name="Reason", value=reason if reason else 'Not Given',inline=True)
                else:
                    embed.add_field(name="Inactive Staffers",value="There are no inactive staffers at the moment",inline=False)

            embed.add_field(name="",value="")
            developer = await self.bot.fetch_user(int(os.environ['DEVELOPER_ID']))
            embed.set_footer(text=f'Developed by {developer.display_name}',icon_url=developer.display_avatar.url)

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.STAFF,config)
        except AssertionError as e:
            await interaction.followup.send(e)
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        else:
            await interaction.followup.send(embed=embed,ephemeral=True)

    @staff.subcommand('set',"Set a staffer as active or inactive")
    async def set(self, 
                interaction : nextcord.Interaction, 
                status : str = nextcord.SlashOption("status","Set a staffer as active or inactive",required=True,choices=['active','inactive'],default='inactive'),
                staffer : Member = nextcord.SlashOption("member","The staffer to set as active or inactive",required=True,autocomplete=True),
                fordays : int | None = nextcord.SlashOption("fordays","*(Only if status is inactive)* Specify how many days the staffer will be inactive",required=False,default=None),
                reason : str | None = nextcord.SlashOption("reason","*(Only if status is inactive)* The reason for the staffer's absence",required=False,default=None)
                ):
        await interaction.response.defer(ephemeral=True)

        try:
            async with self.db:
                config = await self.db.getExtensionConfig(interaction.guild, Extensions.STAFF)
            
            staffer_role = nextcord.utils.get(interaction.guild.roles, id=config['active_role'])
            inactive_role = nextcord.utils.get(interaction.guild.roles, id=config['inactive_role'])

            assert staffer_role in interaction.user.roles, "You do not have the necessary permissions to use this command"

            assert staffer_role in staffer.roles, "The specified member is not a staffer"

            if status == 'inactive':
                assert inactive_role not in staffer.roles, "The specified member is already set to inactive"

                if fordays:
                    timestamp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=fordays)
                else:
                    timestamp = None

                config['inactive'][staffer.id] = {
                    "timestamp" : timestamp.timestamp() if timestamp else None,
                    "reason" : reason
                }

                await staffer.add_roles(inactive_role,reason=f"Staffer is inactive (Set by '{interaction.user.name}' <@{interaction.user.id}>)")
                await interaction.followup.send(f"Staffer <@{staffer.id}> set to 'inactive' {f'for {fordays} day/s' if fordays else ''}",ephemeral=True)
            elif status == 'active':
                assert inactive_role in staffer.roles, "The specified member is already set to active"
                await staffer.remove_roles(inactive_role,reason=f"Staffer is active (Set by '{interaction.user.name}' <@{interaction.user.id}>)")
                
                assert str(staffer.id) in config['inactive'], "The specified member is already set to active"
                config['inactive'].pop(str(staffer.id))
                
                await interaction.followup.send(f"Staffer <@{staffer.id}> set to 'active'",ephemeral=True)
            
            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.STAFF, config)
        
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed())
        except AssertionError as e:
            await interaction.followup.send(e)

    async def schedule_periodic_task(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        midnight = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time.min, tzinfo=datetime.timezone.utc)
        
        # Calcola il tempo rimanente fino alla prossima mezzanotte
        delay = (midnight - now).total_seconds()
        
        # Pianifica il task per l'esecuzione iniziale
        await asyncio.sleep(delay)
        
        # Avvia il task periodico
        self.check_inactive_staffers.start()

        logger.debug(f"Check inactive staffers schedule started at {datetime.datetime.now(datetime.timezone.utc).strftime('%d/%m/%Y, %H:%M:%S')}")

    @tasks.loop(hours=24)
    async def check_inactive_staffers(self):
        try:
            async with self.db:
                configurations = await self.db.getAllExtensionConfig(Extensions.STAFF)

            for guild_id, config in configurations:
                current_time = datetime.datetime.now(datetime.timezone.utc)

                for stafferid, data in config['inactive'].items():
                    if not data['timestamp']: continue

                    saved_time = datetime.datetime.fromtimestamp(data['timestamp'], datetime.timezone.utc)
                    guild = self.bot.get_guild(int(guild_id))

                    if not guild: continue

                    staffer = guild.get_member(int(stafferid))

                    if not staffer: continue

                    inactive_role = nextcord.utils.get(guild.roles, id=config['inactive_role'])

                    if current_time > saved_time:
                        await staffer.remove_roles(inactive_role,reason=f"Staffer is active (Set by '{self.bot.user.name}' <@{self.bot.user.id}>)")
                        config['inactive'].pop(stafferid)
                
                async with self.db:
                    await self.db.editExtensionConfig(guild,Extensions.STAFF,config)
        except ExtensionException as e: pass

def setup(bot : commands.Bot):
    bot.add_cog(StaffCommands(bot))