from nextcord.ext.commands import \
    Cog,                          \
    Bot
from nextcord import              \
    ButtonStyle,                  \
    Interaction,                  \
    SlashOption,                  \
    slash_command,                \
    Colour,                       \
    Embed                         \

from nextcord.ui import           \
    Button,                       \
    View,                         \
    button

from enum import StrEnum
from datetime import datetime, timezone

from utils.terminal import getlogger
from utils.commons import asyncget

logger = getlogger()

# Forse non servono gli enum bastano delle liste di stringhe

class FreeGamesPlatform(StrEnum):
    BROWSER = "browser"
    PC = "pc"
    ALL = "all"

class FreeGamesTags(StrEnum):
    MMORPG =                "mmorpg"
    SHOOTER =               "shooter"
    STRATEGY =              "strategy"
    MOBA =                  "moba"
    RACING =                "racing"
    SPORTS =                "sports"
    SOCIAL =                "social"
    SANDBOX =               "sandbox"
    OPEN_WORLD =            "open-world"
    SURVIVAL =              "survival"
    PVP =                   "pvp"
    PVE =                   "pve"
    PIXEL =                 "pixel"
    VOXEL =                 "voxel"
    ZOMBIE =                "zombie"
    TURN_BASED =            "turn-based"
    FIRST_PERSON =          "first-person"
    THIRD_PERSPECTIVE =     "third-perspective"
    TOP_DOWN =              "top-down"
    TANK =                  "tank"
    SPACE =                 "space"
    SAILING =               "sailing"
    SIDE_SCROLLER =         "side-scroller"
    SUPERHERO =             "superhero"
    PERMATEDEATH =          "permatedeath"
    CARD =                  "card"
    BATTLE_ROYALE =         "battle-royale"
    MMO =                   "mmo", 
    MMOFPS =                "mmofps",
    MMOTPS =                "mmotps",
    D3 =                    "3d",
    D2 =                    "2d",
    ANIME =                 "anime",
    FANTASY =               "fantasy",
    SCIFI =                 "sci-fi",
    FIGHTING =              "fighting",
    ACTION_RPG =            "action-rpg",
    ACTION =                "action",
    MILITARY =              "military",
    MUSLIMAR_ARTS =         "martial-arts",
    FLIGHT =                "flight",
    LOW_SPEC =              "low-spec",
    TOWER_DEFENSE =         "tower-defense",
    HORROR =                "horror",
    MMORTS =                "mmorts"

class FreeGamesSortPolicy(StrEnum):
    RELEASEDATE = "release-date"
    POPULARITY = "popularity"
    ALPHABETICAL = "alphabetical"
    RELEVANCE = "relevance"



class GameEmbed(Embed):
    def __init__(self, game : dict, game_num : int, total_games : int):
        Embed.__init__(self,
            url=game['game_url'],
            title=f"{game['title']} (Game {game_num+1}/{total_games})",
            description=game['short_description'],
            timestamp=datetime.now(timezone.utc),
            colour=Colour.green()
        )

        self.set_image(game['thumbnail'])
        self.add_field(name="Genre",value=game['genre'],inline=True)
        self.add_field(name="Platform",value=game['platform'],inline=False)
        self.add_field(name="Publisher", value=game['publisher'], inline=True)
        self.add_field(name="Developer", value=game['developer'], inline=True)
        self.add_field(name="Release Date",value=game['release_date'],inline=True)

        self.set_footer(text=f'Api offered by: www.freetogame.com', icon_url='https://www.freetogame.com/assets/images/logo-footer.png')

class GameInfoEmbed(Embed):
    def __init__(self, info : dict, image : str):
        Embed.__init__(self,
            url=info['game_url'],
            title=info['title'],
            colour=Colour.green(),
            description=info['description'],
            timestamp=datetime.now(timezone.utc)
        )
        self.set_image(image)

        self.add_field(name="Genre",value=info['genre'],inline=True)
        self.add_field(name="Platform",value=info['platform'],inline=True)
        self.add_field(name="Publisher", value=info['publisher'], inline=True)
        self.add_field(name="Developer", value=info['developer'], inline=True)
        self.add_field(name="Release Date",value=info['release_date'],inline=True)
        self.add_field(name="Status", value=info['status'], inline=True)

        self.set_footer(text=f'Api offered by: www.freetogame.com', icon_url='https://www.freetogame.com/assets/images/logo-footer.png')

        requirements = info.get('minimum_system_requirements',None)

        if requirements:
            self.add_field(
                name="System Requirements",
                value=f"\n- OS: {requirements['os']}\n- CPU: {requirements['processor']}\n- RAM: {requirements['memory']}\n- GPU: {requirements['graphics']}\n- STORAGE: {requirements['storage']}",
                inline=False
            )

class GameInfoView(View):
    def __init__(self, parent_view : 'FreeGamesView', info : dict):
        View.__init__(self)
        self.parent_view = parent_view
        self.info = info
        self.image_num = 0

        self.images = [self.info["thumbnail"]] + [screenshot['image'] for screenshot in self.info['screenshots']]

        self.embed = GameInfoEmbed(self.info,self.images[0])

        self.game_page = Button(style=ButtonStyle.url, label="Game Page", url=self.info['freetogame_profile_url'])
        self.add_item(self.game_page)

    @button(label="Prev. Image", style=ButtonStyle.secondary)
    async def prev_image(self, button : Button,  interaction : Interaction):
        try:
            assert self.image_num > 0, "This is the first page!"
            self.image_num -= 1

            self.embed.set_image(self.images[self.image_num])
        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True, delete_after=5)
        else:
            await interaction.response.edit_message(embed=self.embed)

    @button(label="Next Image", style=ButtonStyle.primary)
    async def next_image(self, button : Button, interaction : Interaction):
        try:
            assert self.image_num < len(self.images) - 1, "This is the last page!"
            self.image_num += 1

            self.embed.set_image(self.images[self.image_num])
        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True, delete_after=5)
        else:
            await interaction.response.edit_message(embed=self.embed)

    @button(label="Back", style=ButtonStyle.red)
    async def back(self, button : Button, interaction : Interaction):
        try:
            embed = await self.parent_view._getnext()
        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True, delete_after=5)
        else:
            await interaction.response.edit_message(embed=embed,view=self.parent_view)

class FreeGamesView(View):
    def __init__(self, data : dict):
        View.__init__(self)
        self.data = data
        self.n = 0

        self.game_page = Button(style=ButtonStyle.url, label="Game Page", url=self.data[self.n]['freetogame_profile_url'])
        self.add_item(self.game_page)

    async def _getnext(self) -> Embed:
        self.game_page.url = self.data[self.n]['freetogame_profile_url']
        return GameEmbed(self.data[self.n],self.n,len(self.data))

    @button(label="Previous", style=ButtonStyle.secondary)
    async def previous_button(self, button: Button, interaction: Interaction):
        try:
            assert self.n > 0, "Page already at the beginning!"
            self.n -= 1
            embed = await self._getnext()
        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True, delete_after=5)
        else:
            await interaction.response.edit_message(embed=embed,view=self)

    @button(label="Next", style=ButtonStyle.secondary)
    async def next_button(self, button: Button, interaction: Interaction):
        try:
            assert self.n < len(self.data) - 1, "Page already at the end!"
            self.n += 1
            embed = await self._getnext()
        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True, delete_after=5)
        else:
            await interaction.response.edit_message(embed=embed,view=self)

    @button(label="Info", style=ButtonStyle.primary)
    async def more_information(self, button: Button, interaction: Interaction):
        try:
            info = await asyncget(f'https://www.freetogame.com/api/game?id={self.data[self.n]['id']}')

            view = GameInfoView(self, info)
            embed = GameInfoEmbed(info, view.images[view.image_num])
        except AssertionError as e:
            await interaction.response.send_message(e,ephemeral=True, delete_after=5)
        else:
            await interaction.response.edit_message(embed=embed,view=view)

# Aggiungere la possibilita' di cercare un gioco attraverso il titolo in un embed

class FreeGames(Cog):
    def __init__(self, bot : Bot):
        self.baseurl = "https://www.freetogame.com/api"
        self.cache = []
        self.bot = bot

    @slash_command(description="Get all free games")
    async def freegames(self, interaction : Interaction): pass

    @freegames.subcommand("get", description="Get all free games")
    async def get(self, 
        interaction : Interaction,
        tags : str = SlashOption(description="Retrieve a list of all available games from a specific genre. es. \"3d.mmorpg.fantasy.pvp\"", default=None, required=False),
        platform : str = SlashOption(description="Retrieve a list of all available games from a specific platform.", choices=FreeGamesPlatform, default=None, required=False),
        sort_by : str = SlashOption(description="Sort games by release date, alphabetical or relevance.", choices=FreeGamesSortPolicy, default=None, required=False),
        ephemeral : bool = SlashOption(description="Whether the response should be ephemeral or not", default=True, required=False)
    ):
        try:
            await interaction.response.defer(ephemeral=ephemeral)
            endpoint = '/games'
            params = []

            if tags is not None:
                tags_list = tags.split('.')

                if len(tags_list) == 1:
                    assert tags_list[0] in FreeGamesTags, f'Invalid tag {tags}, use one of the following: \n{" ".join(FreeGamesTags)}'
                    params.append(f'category={tags}')
                else:
                    assert all((tag_:=tag) in FreeGamesTags for tag in tags_list), f'Invalid tag {tag_}, use one of the following: \n{" ".join(FreeGamesTags)}'
                    endpoint = '/filter'
                    params.append(f'tag={tags}')

            if platform: params.append(f'platform={platform}')
            
            if sort_by: params.append(f'sort_by={sort_by}')

            url = f'{self.baseurl}{endpoint}{'?' if len(params) > 0 else ''}{'&'.join(params)}'
            print(url)
            data = await asyncget(url)

        except AssertionError as e:
            await interaction.followup.send(e)
        else:
            await interaction.followup.send(embed=GameEmbed(data[0], 0, len(data)), view=FreeGamesView(data))

    @freegames.subcommand("tags", description="Get all available game tags")
    async def tags(self,
        interaction: Interaction
    ):
        try:
            await interaction.response.defer(ephemeral=True)

            tags = ",".join(f"`{tag.value}`" for tag in FreeGamesTags)

            embed = Embed(
                colour=Colour.green(),
                description="Here is a list of all available tags.\nYou can use multiple tags by inserting a dot between one tag and another.\nes. `shooter.3d.pvp`",
                title="Available Tags",
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(
                name="Available Tags",
                value=tags
            )
        except AssertionError as e:
            pass
        else:
            await interaction.followup.send(embed=embed)

def setup(bot : Bot):
    bot.add_cog(FreeGames(bot))