from nextcord.ext import commands
from nextcord import (
    ChannelType,
    TextChannel,
    SlashOption,
    Interaction,
    slash_command
)
from nextcord.guild import GuildChannel
import nextcord
import traceback

from utils.terminal import getlogger

logger = getlogger()

#1374114447177683096
class Messages(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.bot = bot

    @slash_command(description="Clone a message with its embeds and file attachments.")
    async def copy(self, 
            interaction : Interaction,
            message_id : int = SlashOption(description="The ID of the message you want to copy.", required=True),
            channel : GuildChannel | None = SlashOption(
                description="The text channel containing the message to copy.",
                channel_types=[ChannelType.forum, ChannelType.group, ChannelType.news, ChannelType.private, 
                               ChannelType.private_thread, ChannelType.public_thread, ChannelType.text],
                default=None
            )
        ):
        try:
            await interaction.response.defer()

            if not channel: channel = interaction.channel

            

            pass
        except Exception as e:
            logger.error(traceback.format_exc())

def setup(bot : commands.Bot):
    bot.add_cog(Messages(bot))