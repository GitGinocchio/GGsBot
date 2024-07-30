from nextcord import Embed,Color,utils,channel,Permissions,Interaction,User, Member
from nextcord.ext import commands, tasks
from typing import Literal
import datetime
import nextcord
import asyncio
import os

from utils.jsonfile import JsonFile, _JsonDict
from utils.terminal import getlogger

logger = getlogger()

staffers_permissions = Permissions(
    use_slash_commands=True
)

staff_permissions = Permissions(
    administrator=True
)

class StaffCommands(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.dirfmt = './data/guilds/{guild_id}/' + StaffCommands.__name__
        self.bot = bot

    @nextcord.slash_command('staff',"Set of commands for configuring the Staff extension inside the server",default_member_permissions=staff_permissions,dm_permission=False)
    async def staff(self, interaction : nextcord.Interaction): pass

    @staff.subcommand("config","Configure the Staff extension inside the server")
    async def config(self, 
                    interaction : nextcord.Interaction,
                    staffer_role : nextcord.Role = nextcord.SlashOption(description="The role assigned to each staffer",required=True,autocomplete=True),
                    inactive_role : nextcord.Role = nextcord.SlashOption(description="The role assigned to each staffer who is inactive",required=True,autocomplete=True)
                    #staffer_commands_accessible_by : list[nextcord.Role] = nextcord.SlashOption(description="...",required=True,autocomplete=True)
                ): 
        await interaction.response.defer(ephemeral=True)
        workingdir = self.dirfmt.format(guild_id=interaction.guild.id)
        try:
            assert not os.path.exists(f'{workingdir}/config.json'), "There is already a configuration for staffers"

            os.makedirs(workingdir,exist_ok=True)
            
            file = JsonFile(f'{workingdir}/config.json')
            file['active_role'] = staffer_role.id
            file['inactive_role'] = inactive_role.id
            file['inactive'] = _JsonDict({},file)

            self.bot.loop.create_task(self.schedule_periodic_task())

        except AssertionError as e:
            await interaction.followup.send(e,ephemeral=True)
        else:
            await interaction.followup.send("Staff extension successfully configured",ephemeral=True)

    @staff.subcommand("teardown","Remove Staff extension from server")
    async def teardown(self, interaction : nextcord.Interaction): 
        await interaction.response.defer(ephemeral=True)
        workingdir = self.dirfmt.format(guild_id=interaction.guild.id)
        try:
            assert os.path.exists(f'{workingdir}/config.json'), "There is no configuration for staffers"

            os.remove(f'{workingdir}/config.json')
            os.rmdir(workingdir)
            
            if self.check_inactive_staffers.is_running():
                self.check_inactive_staffers.stop()

        except AssertionError as e: await interaction.followup.send(e,ephemeral=True)
        except OSError as e: logger.error(e)
        else: await interaction.followup.send("Staffer configuration successfully deleted",ephemeral=True)

    @nextcord.slash_command('staffers',"Set of useful commands to set or view the status of staffers",default_member_permissions=staffers_permissions,dm_permission=False)
    async def staffers(self, interaction : nextcord.Interaction): pass

    @staffers.subcommand('show',"Show a list of active and/or inactive staffers")
    async def show(self, 
                   interaction : nextcord.Interaction, 
                   status : str = nextcord.SlashOption("status","Whether to show only active staffers, inactive staffers, or both",required=True,choices=['active','inactive','both'],default='both')
                ):
        await interaction.response.defer(ephemeral=True)
        workingdir = self.dirfmt.format(guild_id=interaction.guild.id)
        try:
            assert os.path.exists(f'{workingdir}/config.json'), "You must first configure the extension using `/staff config` before using this commands"

            file = JsonFile(f'{workingdir}/config.json')

            staffer_role = nextcord.utils.get(interaction.guild.roles, id=file['active_role'])
            inactive_role = nextcord.utils.get(interaction.guild.roles, id=file['inactive_role'])

            inactive_staffers = [(inactive,file['inactive'][staffer]['reason'],file['inactive'][staffer]['timestamp']) for staffer in file['inactive'].keys() if (inactive:=interaction.guild.get_member(int(staffer))) is not None]

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
                    
        except AssertionError as e:
            await interaction.followup.send(e,ephemeral=True)
        else:
            await interaction.followup.send(embed=embed,ephemeral=True)

    @staffers.subcommand('set',"Set a staffer as active or inactive")
    async def set(self, 
                interaction : nextcord.Interaction, 
                status : str = nextcord.SlashOption("status","Set a staffer as active or inactive",required=True,choices=['active','inactive'],default='inactive'),
                staffer : Member = nextcord.SlashOption("member","The staffer to set as active or inactive",required=True,autocomplete=True),
                fordays : int | None = nextcord.SlashOption("fordays","*(Only if status is inactive)* Specify how many days the staffer will be inactive",required=False,default=None),
                reason : str | None = nextcord.SlashOption("reason","*(Only if status is inactive)* The reason for the staffer's absence",required=False,default=None)
                ):
        await interaction.response.defer(ephemeral=True)
        workingdir = self.dirfmt.format(guild_id=interaction.guild.id)

        try:
            assert os.path.exists(f'{workingdir}/config.json'), "You must first configure the extension using `/staff config` before using this commands"
            file = JsonFile(f'{workingdir}/config.json')
            
            staffer_role = nextcord.utils.get(interaction.guild.roles, id=file['active_role'])
            inactive_role = nextcord.utils.get(interaction.guild.roles, id=file['inactive_role'])

            assert staffer_role in interaction.user.roles, "You do not have the necessary permissions to use this command"

            assert staffer_role in staffer.roles, "The specified member is not a staffer"

            if status == 'inactive':
                assert inactive_role not in staffer.roles, "The specified member is already set to inactive"

                if fordays:
                    timestamp = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=fordays)
                else:
                    timestamp = None

                file['inactive'][staffer.id] = {
                    "timestamp" : timestamp.timestamp() if timestamp else None,
                    "reason" : reason
                }

                await staffer.add_roles(inactive_role,reason=f"Staffer is inactive (Set by '{interaction.user.name}' <@{interaction.user.id}>)")
                await interaction.followup.send(f"Staffer <@{staffer.id}> set to 'inactive' {f'for {fordays} day/s' if fordays else ''}",ephemeral=True)
            elif status == 'active':
                assert inactive_role in staffer.roles, "The specified member is already set to active"
                await staffer.remove_roles(inactive_role,reason=f"Staffer is active (Set by '{interaction.user.name}' <@{interaction.user.id}>)")
                
                assert str(staffer.id) in file['inactive'], "The specified member is already set to active"
                file['inactive'].pop(str(staffer.id))
                
                await interaction.followup.send(f"Staffer <@{staffer.id}> set to 'active'",ephemeral=True)
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

        logger.debug(f"Check inactive staffers schedule started at {datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}")

    @tasks.loop(hours=24)
    async def check_inactive_staffers(self):
        for guild_id in os.listdir('./data/guilds'):
            workingdir = self.dirfmt.format(guild_id=guild_id)
            if not os.path.exists(f'{workingdir}/config.json'): continue

            file = JsonFile(f'{workingdir}/config.json')

            current_time = datetime.datetime.now(datetime.timezone.utc)

            for stafferid, data in file['inactive'].items():
                if not data['timestamp']: continue

                saved_time = datetime.datetime.fromtimestamp(data['timestamp'], datetime.timezone.utc)
                guild = self.bot.get_guild(int(guild_id))

                if not guild: continue

                staffer = guild.get_member(int(stafferid))

                if not staffer: continue

                inactive_role = nextcord.utils.get(guild.roles, id=file['inactive_role'])

                if current_time > saved_time:
                    await staffer.remove_roles(inactive_role,reason=f"Staffer is active (Set by '{self.bot.user.name}' <@{self.bot.user.id}>)")
                    file['inactive'].pop(stafferid)

def setup(bot : commands.Bot):
    bot.add_cog(StaffCommands(bot))