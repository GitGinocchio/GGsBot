from nextcord.ext import commands
from nextcord import \
    Interaction,     \
    SlashOption,     \
    slash_command
from cachetools import LRUCache
from datetime import datetime
from uuid import UUID
import json

from utils.commons import asyncget
from utils.terminal import getlogger

logger = getlogger()

from .ValorantQuizUtils import Levels, MapModes
from .ValorantQuizSession import MapQuizSession, QuizSession

class ValorantQuiz(commands.Cog):
    def __init__(self, bot : commands.Bot) -> None:
        commands.Cog.__init__(self)
        self.baseurl = 'https://valorant-api.com/v1'
        self.cache = LRUCache(100)
        self.sessions : dict[UUID, QuizSession] = {}
        self.bot = bot

    @slash_command("valquiz", description="Valorant Quiz")
    async def valquiz(self, interaction : Interaction): pass

    @valquiz.subcommand(name='maps', description="Valorant Quiz with ingame maps")
    async def maps(self, 
                interaction : Interaction,
                level = SlashOption(description=f"Level of the map quiz. default: Hard", required=False, choices=Levels, default=Levels.HARD),
                mode = SlashOption(description="Mode of the map quiz. default: Normal", required=False, choices=MapModes, default=MapModes.NORMAL),
                rounds : int = SlashOption(description=f"Number of rounds to play (1-100). default: 3", min_value=1, max_value=100, default=3),
                time_per_round : float = SlashOption(description=f"Time per round (in minutes). default: 1.0", required=False, default=1.0),
                deathmatch_maps : bool = SlashOption(description=f'Whether to include deathmatch mode maps as well. default: false', required=False, default=False)
            ):
        try:
            await interaction.response.defer(ephemeral=False)

            if not 'maps' in self.cache:
                content_type, content, code, reason = await asyncget(f'{self.baseurl}/maps')
                assert content_type == 'application/json' and code == 200, f"Error while fetching game info (code: {code}): {reason}"
                self.cache['maps'] = json.loads(content)["data"]

            session = MapQuizSession(
                level=Levels(level),
                mode=mode,
                num_rounds=rounds,
                time_per_round=time_per_round,
                deathmatch_maps=deathmatch_maps,
                cache=self.cache,
                interaction=interaction
            )
            self.sessions[session.id] = session

            embed, view = await session.start()

            await interaction.followup.send(embed=embed,view=view)
        except AssertionError as e:
            logger.error(e)

def setup(bot : commands.Bot) -> None:
    bot.add_cog(ValorantQuiz(bot))