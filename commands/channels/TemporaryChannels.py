from nextcord.ext import commands
from utils.jsonfile import JsonFile
from utils.terminal import clear, F, B
import asyncio,os
import nextcord

class TemporaryChannels(commands.Cog):
    def __init__(self,bot : commands.Bot):
        self.bot = bot

    @nextcord.slash_command("setup_temporary_channels","Set up temporary channels in the server.",default_member_permissions=2147483664,dm_permission=False)
    async def setup_temporary_channels(self, interaction : nextcord.Interaction, setup_channel : nextcord.VoiceChannel, temporary_channels_category : nextcord.CategoryChannel, timeout : float):
        try:
            os.makedirs(f'./data/guilds/{interaction.guild_id}/TemporaryChannels',exist_ok=True)
        except OSError as e:
            await interaction.response.send_message(f"Error occurred while creating directory: {e}", ephemeral=True)
        else:
            file = JsonFile(f'./data/guilds/{interaction.guild_id}/TemporaryChannels/setup.json')
            file['temporary_channels_category_id'] = temporary_channels_category.id
            file['setup_channel_id'] = setup_channel.id
            file['temporary_channels'] = []
            file['timeout'] = timeout
            file.save()
            await interaction.response.send_message("Temporary channels setup completed successfully!", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"\n🚀  {F.YELLOW}Initializing clearing temporary channels sequence...{F.RESET}")
        for i,guild_id in enumerate(guilds_ids:=os.listdir('./data/guilds/')):
            if os.path.isfile(f'./data/guilds/{guild_id}/TemporaryChannels/setup.json'):
                print(f' │\n{" ├──" if not i == len(guilds_ids) - 1 else " └──" } 🔍  {F.BLUE}Fetching data.guilds.{guild_id}...{F.RESET}')
                file = JsonFile(f'./data/guilds/{guild_id}/TemporaryChannels/setup.json')
                if len(temporary_channels:=file['temporary_channels']) == 0:
                    print(f' {"│" if not i == len(guilds_ids) - 1 else " " }    └── ✅  {F.GREEN}No temporary channels were found.{F.RESET}')
                for j,channel_id in enumerate(temporary_channels):
                    channel = self.bot.get_channel(channel_id)
                    if channel is not None:
                        print(f' {"│" if not j == len(temporary_channels) - 1 else " " }    {"├──" if not j == len(temporary_channels) - 1 else "└──" } ⚠️  {F.YELLOW}Found channel \"{channel.name}\" (id:{channel.id}){F.RESET}')
                        if len(channel.members) == 0:
                            await channel.delete(reason='Temporary Channel Deleted')
                            print(f' {"│" if not j == len(temporary_channels) - 1 else " "}         └── ✅  {F.GREEN}Temporary channel deleted{F.RESET}')
                            file['temporary_channels'].remove(channel_id)
                        else:
                            print(f' {"│" if not j == len(temporary_channels) - 1 else " "}         └── ⚠️  {F.YELLOW}Temporary channel not deleted, there is/are {len(channel.members)} user/s inside the channel...{F.RESET}')
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member : nextcord.Member, before : nextcord.VoiceChannel, after : nextcord.VoiceChannel):
        try:
            setup_path = f'./data/guilds/{after.channel.guild.id if after.channel is not None else before.channel.guild.id}/TemporaryChannels/setup.json'
            assert os.path.exists(setup_path)
            setup = JsonFile(setup_path)

            if after.channel is not None and after.channel.id == setup['setup_channel_id']:
                overwrites = {
                    member: nextcord.PermissionOverwrite(
                        view_channel=True,
                        connect=True,
                        speak=True,
                        stream=True,
                        manage_channels=True,
                        manage_permissions=True,
                        move_members=True,
                        mute_members=True,
                        deafen_members=True,
                        priority_speaker=True
                    )
                }
                vocal_channel : nextcord.VoiceChannel = await member.guild.create_voice_channel(
                    name=f'{str(member.name).capitalize()}\'s Vocal Channel',
                    category=self.bot.get_channel(setup["temporary_channels_category_id"]),
                    overwrites=overwrites)
                
                await member.move_to(vocal_channel,reason='Temporary Channel Created')
                setup["temporary_channels"].append(vocal_channel.id)
                _ = asyncio.create_task(self.delete_channel(vocal_channel,setup))

            if before.channel is not None:
                if after.channel is not None:
                    if before.channel.id != after.channel.id and before.channel.id in setup['temporary_channels']:
                        _ = asyncio.create_task(self.delete_channel(before.channel,setup))
                else:
                    if before.channel.id in setup["temporary_channels"]:
                        _ = asyncio.create_task(self.delete_channel(before.channel,setup))

        except AssertionError: pass
        except nextcord.errors.HTTPException as e: print(e)

    async def delete_channel(self,channel : nextcord.VoiceChannel, setup : JsonFile):
        try:
            await asyncio.sleep(setup["timeout"])
            assert channel is not None and len(channel.members) <= 0
            
            await channel.delete(reason='Temporary Channel Deleted')
            setup["temporary_channels"].remove(channel.id)
        except AssertionError as e: pass
        except Exception as e: print('delete_channel error:',e,e.args)

def setup(bot: commands.Bot):
    bot.add_cog(TemporaryChannels(bot))