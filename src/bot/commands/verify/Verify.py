from nextcord.ext.commands import Bot, Cog
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
from .VerificationUis import StartVerificationUI

permissions = Permissions(
    administrator=True
)

class Verify(Cog):
    def __init__(self, bot : Bot):
        Cog.__init__(self)
        self.db = Database()
        self.bot = bot
        self.persistent_views_added = False

    @Cog.listener()
    async def on_ready(self):
        if not self.persistent_views_added:
            view = StartVerificationUI(self.bot)
            self.bot.add_view(view)
            self.persistent_views_added = True

def setup(bot : Bot):
    bot.add_cog(Verify(bot))