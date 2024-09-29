from nextcord.ext import commands
from nextcord import \
    Embed, \
    Color, \
    utils, \
    channel, \
    Permissions, \
    Interaction, \
    SlashOption, \
    TextChannel, \
    Role, \
    slash_command
import nextcord
import os

from commands.ai import ChatBot
from commands.general import Greetings
from commands.staff import StaffCommands
from utils.jsonfile import JsonFile, _JsonDict
from utils.terminal import getlogger

logger = getlogger()

permissions = Permissions(
    administrator=True
)

class CommandsManager(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.sync_all_application_commands()
        await self.bot.discover_application_commands(guild_id=os.environ['DEVELOPER_GUILD_ID'])
    
    @slash_command(name='setup', description='Setup a bot extension',default_member_permissions=permissions,dm_permission=False)
    async def setup(self, interaction : Interaction): pass

    @setup.subcommand(name='aichatbot', description='Initialize AiChatBot extension on this server')
    async def setup_aichatbot(self, 
                    interaction : Interaction,
                    textchannel : TextChannel = SlashOption("textchannel","The text channel where the bot can be used and all public or private chats will be created",required=True),
                    delay : int = SlashOption("delay","The number of seconds a user must wait before sending another prompt",required=True,default=5)
                ):
        await interaction.response.defer(ephemeral=True)
        workingdir = f'./data/guilds/{interaction.guild.id}/{ChatBot.__name__}'
        try:
            os.makedirs(workingdir,exist_ok=True)
        
            file = JsonFile(f'{workingdir}/config.json')
            file['aichatbot-text-channel'] = textchannel.id
            file['aichatbot-chat-delay'] = delay
            file['threads'] = _JsonDict({},file)
        
        except AssertionError as e:
            await interaction.followup.send(e)
        except OSError as e:
            await interaction.followup.send(f"Error occurred while creating directory: {e}", ephemeral=True)
        else:
            await interaction.followup.send('AiChatBot extension installed successfully')

    @setup.subcommand(name='greetings',description='Initialize Greetings extension on this server')
    async def setup_greetings(self, 
                interaction : Interaction, 
                welcome_channel : TextChannel = SlashOption("welcome-channel","The channel where the welcome messages will be sent",required=False,default=None),
                goodbye_channel : TextChannel = SlashOption("goodbye-channel","The channel where the goodbye messages will be sent",required=False,default=None),
            ):
        try:
            await interaction.response.defer(ephemeral=True)
            assert welcome_channel or goodbye_channel, "You must provide at least one channel for welcome or goodbye messages to be sent in"

            workingdir = f'./data/guilds/{interaction.guild_id}/{Greetings.__name__}'

            os.makedirs(workingdir,exist_ok=True)
            
            file = JsonFile(f'{workingdir}/config.json')
            file['welcome_channel_id'] = (welcome_channel.id if welcome_channel else None)
            file['goodbye_channel_id'] = (goodbye_channel.id if goodbye_channel else None)
            file.save()
        
        except AssertionError as e:
            await interaction.followup.send(e,ephemeral=True)
        except OSError as e:
            await interaction.followup.send(f"Error occurred while creating directory: {e}", ephemeral=True)
        else:
            await interaction.followup.send("Server Messages setup completed successfully!", ephemeral=True)

    @setup.subcommand(name='staff', description='Initialize Staff extension on this server')
    async def setup_staff(self,
                interaction : Interaction,
                staffer_role : Role = SlashOption(description="The role assigned to each staffer",required=True,autocomplete=True),
                inactive_role : Role = SlashOption(description="The role assigned to each staffer who is inactive",required=True,autocomplete=True)
                #staffer_commands_accessible_by : list[nextcord.Role] = nextcord.SlashOption(description="...",required=True,autocomplete=True)
            ): 
        try:
            await interaction.response.defer(ephemeral=True)
            workingdir = f'./data/guilds/{interaction.guild.id}/{StaffCommands.__name__}'
            assert not os.path.exists(f'{workingdir}/config.json'), "Staff extension already configured for this server"

            os.makedirs(workingdir,exist_ok=True)
            
            file = JsonFile(f'{workingdir}/config.json')
            file['active_role'] = staffer_role.id
            file['inactive_role'] = inactive_role.id
            file['inactive'] = _JsonDict({},file)
        except AssertionError as e:
            await interaction.followup.send(e,ephemeral=True)
        else:
            await interaction.followup.send("Staff setup completed successfully!",ephemeral=True)



    @slash_command(name='teardown', description='Teardown a bot extension',default_member_permissions=permissions,dm_permission=False)
    async def teardown(self, interaction : Interaction): pass

    @teardown.subcommand(name='aichatbot', description='Teardown AiChatBot extension on this server')
    async def teardown_aichatbot(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            workingdir = f'./data/guilds/{interaction.guild.id}/{ChatBot.__name__}'
            assert os.path.exists(workingdir), "AiChatBot is not installed on this server"

            os.remove(f'{workingdir}/config.json')
            os.rmdir(workingdir)

        except AssertionError as e:
            await interaction.followup.send(e, ephemeral=True)
        else:
            await interaction.followup.send("AiChatBot teardown completed successfully!", ephemeral=True)

    @teardown.subcommand(name='greetings', description='Teardown Greetings extension on this server')
    async def teardown_greetings(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            workingdir = f'./data/guilds/{interaction.guild.id}/{Greetings.__name__}'
            assert os.path.exists(workingdir), "Greetings is not installed on this server"

            os.remove(f'{workingdir}/config.json')
            os.rmdir(workingdir)

        except AssertionError as e:
            await interaction.followup.send(e, ephemeral=True)
        else:
            await interaction.followup.send("Greetings teardown completed successfully!", ephemeral=True)

    @teardown.subcommand(name='staff', description='Teardown Staff extension on this server')
    async def teardown_staff(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            workingdir = f'./data/guilds/{interaction.guild.id}/{StaffCommands.__name__}'
            assert os.path.exists(f'{workingdir}/config.json'), "There is no configuration for staffers"

            os.remove(f'{workingdir}/config.json')
            os.rmdir(workingdir)

        except AssertionError as e: 
            await interaction.followup.send(e,ephemeral=True)
        except OSError as e: 
            logger.error(e)
        else: 
            await interaction.followup.send("Staff teardown completed successfully!",ephemeral=True)

def setup(bot : commands.Bot):
    bot.add_cog(CommandsManager(bot))