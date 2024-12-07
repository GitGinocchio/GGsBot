from nextcord.ext import commands
from nextcord import \
    WebhookMessage,  \
    slash_command,   \
    Interaction,     \
    SlashOption,     \
    Permissions,     \
    TextChannel,     \
    NotFound,        \
    Member,          \
    Role
import random

from utils.db import Database
from utils.commons import Extensions
from utils.exceptions import ExtensionException
from .VerificationUis import *

permissions = Permissions(
    administrator=True
)

class Verify(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.db = Database()
        self.bot = bot

        self.modes : dict[VerificationTypes, VerificationUI] = {
            VerificationTypes.BUTTON : ButtonVerificationUi,
            VerificationTypes.QUESTION : QuestionVerificationUi
        }

    @slash_command(name="verify", description="Set of verifications commands", dm_permission=False)
    async def verify(self,
            interaction : Interaction,
            mode : str | None = SlashOption(description="Choose verification mode", choices=VerificationTypes, required=False, default=None)
        ):
        try:
            message : WebhookMessage = None
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                config, enabled = await self.db.getExtensionConfig(interaction.guild, Extensions.VERIFY)
            assert enabled, "Extension is not enabled"

            verified_role = interaction.guild.get_role(config['verified_role'])

            if mode:
                assert mode in config['modes'], f'Mode {mode} is not a valid verification mode for this server'
            else:
                mode = random.choice(config['modes'])

            ui_type : VerificationUI = self.modes.get(VerificationTypes(mode), None)

            ui : VerificationUI = ui_type(
                bot=self.bot,
                verified=verified_role,
            )

            if ui_type == QuestionVerificationUi:
                await ui.async_init()

            message = await interaction.followup.send(embed=ui, view=ui, wait=True)
            assert not await ui.wait(), f'The verification process has expired'

        except AssertionError as e:
            if message:
                await message.edit(e, view=None, embed=None)
            else:
                await interaction.followup.send(e, ephemeral=True)
        except ExtensionException as e:
            if message:
                await message.edit(content=None, embed=e.asEmbed(), view=None)
            else:
                await interaction.followup.send(embed=e.asEmbed(), ephemeral=True)
        else:
            if ui.status == VerificationStatus.ALREADY_VERIFIED:
                await message.edit('You have already been verified!', view=None, embed=None, delete_after=5)
            elif ui.status == VerificationStatus.NOT_VERIFIED:
                await message.edit('Verification failed!', view=None, embed=None, delete_after=5)
            else:
                await message.edit(f'Verification completed successfully!', view=None, embed=None, delete_after=5)

def setup(bot : commands.Bot):
    bot.add_cog(Verify(bot))