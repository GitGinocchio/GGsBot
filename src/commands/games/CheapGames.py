# Se dopo aver fatto una fetch al al database e' presente lo stesso:
# - gameid
# - publish_datetime

# allora non e' necessario inviare il messaggio

"""
updates : {
    name : {
        "channels" : [],
        "api" : "DEALS"
        "stores" : "Steam" | etc.
        "lowerPrice" : 0 | None        # ritorna tutti i deal con prezzo superiore a lowerPrice
        "upperPrice" : 0 | None        # ritorna tutti i deal con prezzo inferiore ad upperPrice
        "steamAppID" : 0 | None        # guarda per determinati giochi di steam in base al loro ID
        "saved" : {
            gameID : publish_time
        },
        "on" : "hour"
    },
    name2 : {
        "channels" : [],
        "api" : "GIVEAWAYS"
        "type" : "game" | "loot" | "beta" | "all"
        "stores" : "Steam" | etc.
        "saved" : {
            gameID : publish_time
        },
        "on" : "hour"
    },
}
"""
from nextcord.ext.commands import Bot, Cog
from nextcord.ext import tasks
from nextcord import \
    Permissions,     \
    HTTPException,   \
    Forbidden,       \
    ButtonStyle,     \
    SelectOption,    \
    ChannelType,     \
    SlashOption,     \
    Interaction,     \
    Colour,          \
    Guild,           \
    Embed,           \
    Role,            \
    slash_command
from nextcord.ui import \
    RoleSelect,         \
    ChannelSelect,      \
    StringSelect,       \
    Item,               \
    View,               \
    button,             \
    Button,             \
    string_select,      \
    channel_select,     \
    role_select

from enum import StrEnum, Enum
from functools import reduce
import datetime
import asyncio
import json

from utils.exceptions import ExtensionException
from utils.terminal import getlogger
from utils.db import Database
from utils.abc import UI, UiPage, UiSubmitPage, Page
from utils.commons import \
    Extensions,           \
    GLOBAL_INTEGRATION,   \
    GUILD_INTEGRATION,    \
    USER_INTEGRATION,     \
    asyncget

logger = getlogger()

# Enums

class Api(StrEnum):
    DEALS =                 "deals"
    GIVEAWAYS =             "giveaways"

class GiveawayType(StrEnum):
    GAME =                  "game"
    LOOT =                  "dlc"
    BETA =                  "early access"

class GiveawayStore(StrEnum):
    PC =                    "pc"
    STEAM =                 "steam"
    EPIC =                  "epic games store"
    UBISOFT =               "ubisoft"
    GOG =                   "gog"
    ITCHIO =                "itch.io"
    PS4 =                   "playstation 4"
    PS5 =                   "playstation 5"
    XBOX_ONE =              "xbox one"
    XBOX_SERIES_XS =        "xbox series x|s"
    SWITCH =                "nintendo switch"
    ANDROID =               "android"
    IOS =                   "ios"
    VR =                    "vr"
    BATTLENET =             "battlenet"
    ORIGIN =                "origin"
    DRM_FREE =              "drm-free"
    XBOX_360 =              "xbox 360"

class DealStore(Enum):
    STEAM =                 (1,  "Steam")
    GAMERSGATE =            (2,  "Gamers Gate")
    GREENMANGAMING =        (3,  "Green Man Gaming")
    AMAZON =                (4,  "Amazon")
    GAMESTOP =              (5,  "GameStop")
    DIRECT2DRIVE =          (6,  "Direct 2 Drive")
    GOG =                   (7,  "GoG")
    ORIGIN =                (8,  "Origin")
    GETGAMES =              (9,  "Get Games")
    SHINYLOOT =             (10, "Shiny Loot")
    HUMBLESTORE =           (11, "Humble Store")
    DESURA =                (12, "Desura")
    UPLAY =                 (13, "Uplay")
    INDIEGAMESTAND =        (14, "Indie Games Stand")
    FANATICAL =             (15, "Fanatical")
    GAMESROCKET =           (16, "Games Rocket")
    GAMESREPUBLIC =         (17, "Games Republic")
    SILAGAMES =             (18, "Sila Games")
    PLAYFIELD =             (19, "Play Field")
    IMPERIALGAMES =         (20, "Imperial Games")
    WINGAMESTORE =          (21, "Win Game Store")
    FUNSTOCKDIGITAL =       (22, "Fun Stock Digital")
    GAMEBILLET =            (23, "Game Billet")
    VOIDU =                 (24, "Voidu")
    EPICGAMESTORE =         (25, "Epic Games Store")
    RAZERGAMESTORE =        (26, "Razer Games Store")
    INDIEGALA =             (30, "IndieGala")
    BLIZZARDSHOP =          (31, "Blizzard Shop")
    ALLYOUPLAY =            (32, "All You Play")
    DLGAMER =               (33, "DL Gamer")
    NOCTRE =                (34, "Noctre")
    DREAMGAME =             (35, "DreamGame")

hours_select = [SelectOption(label=f'{h:02}:00 ({h if h == 12 else int(h % 12):02}:00 {"PM" if h > 11 else "AM"}) (UTC)', value=h) for h in range(0, 25)]

# Add Update Ui

class GiveawaysSetupUI(UI):
    def __init__(self, bot :  Bot, guild : Guild):
        UI.__init__(self, bot, guild)
        self.config = {'channels' : [], 'types' : [], 'stores' : [], 'role' : None, 'api' : Api.GIVEAWAYS.value, 'saved' : {}}
        self.add_pages(self.GiveawayPage)
        self.set_submit_page(self.GiveawaySubmitPage)

    class GiveawayPage(UiPage):
        giveaway_types = [SelectOption(label=type.value.capitalize(), value=type.value) for type in GiveawayType]
        store_types = [SelectOption(label=type.value.capitalize(), value=type.value) for type in GiveawayStore]
        def __init__(self, ui : UI):
            UiPage.__init__(self, ui)
            self.description = "This command allows you to add an update whenever games for different platforms become free"

            self.add_field(
                name="1. Giveaway Channel(s)",
                value="Select the channel(s) where giveaways will be posted.",
                inline=False
            )
            self.add_field(
                name="2. Giveaway Type",
                value="Select the type of giveaway.",
                inline=False
            )
            self.add_field(
                name="3. Store",
                value="Select the game store you would like to giveaways from.",
                inline=False 
            )
            
            self.add_field(
                name="4. Update Role",
                value="Select the role that will receive notifications after an update",
                inline=False
            )

        @channel_select(placeholder="1. Giveaway Channel(s) [Required]",max_values=3, channel_types=[ChannelType.text, ChannelType.news])
        async def giveaway_channel(self, select: ChannelSelect, interaction : Interaction):
            self.config['channels'] = ([channel.id for channel in select.values.channels] if len(select.values.channels) > 0 else [])

        @string_select(placeholder="2. Giveaway Type [Optional] (no choice: all types)", options=giveaway_types, min_values=0,max_values=len(giveaway_types))
        async def giveaway_type(self, select: StringSelect, interaction : Interaction):
            self.config['types'] = select.values

        @string_select(placeholder="3. Store [Optional] (no choice: all shops)", options=store_types, min_values=0,max_values=len(store_types))
        async def giveaway_store(self, select: StringSelect, interaction : Interaction):
            self.config['stores'] = select.values

        @role_select(placeholder="4. Update Role [Optional] (no choice: no role)", min_values=0, max_values=1)
        async def giveaway_role(self, select: RoleSelect, interaction : Interaction):
            self.config['role'] = select.values[0].id if len(select.values) > 0 else None

        async def on_next(self, interaction : Interaction):
            if len(self.config.get('channels', [])) == 0: 
                await interaction.response.send_message("You must set at least one Deal Channel.", ephemeral=True, delete_after=5)
                return
            
            await super().on_next(self, interaction)

    class GiveawaySubmitPage(UiSubmitPage):
        def __init__(self, ui : UI):
            UiSubmitPage.__init__(self, ui)

class DealsSetupUI(UI):
    def __init__(self, bot : Bot, guild : Guild):
        UI.__init__(self, bot, guild)
        self.config = {
            "channels" : [],
            "saved" : {},
            "shoplastchange" : {},
            "api" : Api.DEALS.value,
            "role" : None,

            "storeIDs1" : [],
            "storeIDs2" : [],
            "AAA" : True,
            "steamworks" : False,
            
            "upperPrice" : 50,
            "lowerPrice" : 0,
            "minSteamRating" : 0,
            "minMetacriticRating" : 0,
        }

        self.add_pages(self.DealSettingsPage, self.DealConditionsPage, self.DealGuildSettingsPage)
        self.set_submit_page(self.DealSubmitPage)

    class DealSettingsPage(UiPage):
        availables_stores = [SelectOption(label=store.value[1], value=store.value[0]) for store in DealStore]
        boolean_options = [SelectOption(label=option, value=(True if option == "Yes" else False)) for option in ["Yes","No"]]

        def __init__(self, ui : UI):
            UiPage.__init__(self, ui)
            self.title = "Deal Types"
            self.description = "Choose the game types or game stores you would like to get deals from."

            self.add_field(
                name="1. Deals Stores",
                value="Select the game store you would like to get deals from.",
                inline=False
            )

            self.add_field(
                name="1. Other Deals Stores",
                value="Select the game store you would like to get deals from.",
                inline=False
            )

            self.add_field(
                name="2. Triple A Games",
                value="Select whether you want to include triple A games in deals.",
                inline=False
            )

            self.add_field(
                name="3. Steam redeemable games",
                value="Select whether you want to include only Steam redeemable games deals.",
                inline=False
            )

        @string_select(placeholder="1. Deals Stores [Optional] (no choice=all shops)", options=availables_stores[0:24], min_values=0, max_values=len(availables_stores[0:24]))
        async def select_deals_store(self, select: StringSelect, interaction : Interaction):
            self.config['storeIDs1'] = [int(value) for value in select.values]

        @string_select(placeholder="2. Other Deals Stores [Optional] (no choice=all shops)", options=availables_stores[24::], min_values=0, max_values=len(availables_stores[24::]))
        async def select_other_deals_store(self, select: StringSelect, interaction : Interaction):
            self.config['storeIDs2'] = [int(value) for value in select.values]

        @string_select(placeholder="3. Triple A Games [Optional] (no choice=Yes)", options=boolean_options, min_values=0)
        async def select_triple_a_games(self, select: StringSelect, interaction : Interaction):
            self.config['AAA'] = (True if select.values[0] == 'True' else False) if len(select.values) > 0 else True

        @string_select(placeholder="4. Steam Redeemable games [Optional] (no choice=No)", options=boolean_options, min_values=0)
        async def select_steam_redeemable_games(self, select: StringSelect, interaction : Interaction):
            self.config['steamworks'] = (True if select.values[0] == 'True' else False) if len(select.values) > 0 else False

    class DealConditionsPage(UiPage):
        def __init__(self, ui : UI):
            UiPage.__init__(self, ui)
            self.title = "Game Conditions"
            self.description = "Choose the conditions for your game deals."

            self.add_field(
                name="1. Upper Price",
                value="Only returns deals with a price less than or equal to this value",
                inline=False
            )

            self.add_field(
                name="2. Lower Price",
                value="Only returns deals with a price greater than this value",
                inline=False
            )

            self.add_field(
                name="3. Minimum Steam Rating",
                value="Only returns deals with a Steam rating percentage greater than this value",
                inline=False
            )

            self.add_field(
                name="4. Minimum Metacritic Rating",
                value="Only returns deals with a metacritic rating percentage greater than this value",
                inline=False
            )

        @string_select(placeholder="1. Upper Price [Optional] (no choice = no limit = 50)", min_values=0, options=[SelectOption(label=value, value=value) for value in range(0, 50, 2)])
        async def select_upper_price(self, select : StringSelect, interaction : Interaction):
            self.config['upperPrice'] = int(select.values[0]) if len(select.values) > 0 else 50

        @string_select(placeholder="2. Lower Price [Optional] (no choice = 0)", min_values=0, options=[SelectOption(label=value, value=value) for value in range(0, 50, 2)])
        async def select_lower_price(self, select : StringSelect, interaction : Interaction):
            self.config['lowerPrice'] = int(select.values[0]) if len(select.values) > 0 else 0

        @string_select(placeholder="3. Minimum Steam Rating [Optional] (no choice = 0)", min_values=0, options=[SelectOption(label=value, value=value) for value in range(0, 100, 4)])
        async def select_min_steam_rating(self, select : StringSelect, interaction : Interaction):
            self.config['minSteamRating'] = int(select.values[0]) if len(select.values) > 0 else 0

        @string_select(placeholder="4. Minimum Metacritic Rating [Optional] (no choice = 0)", min_values=0, options=[SelectOption(label=value, value=value) for value in range(0, 100, 4)])
        async def select_min_metacritic_rating(self, select : StringSelect, interaction : Interaction):
            self.config['minMetacriticRating'] = int(select.values[0]) if len(select.values) > 0 else 0

        async def on_next(self, interaction : Interaction):
            if self.config['lowerPrice'] > self.config['upperPrice']:
                await interaction.response.send_message("The lower price must be less than or equal to the upper price.", ephemeral=True, delete_after=5)
                return

            await super().on_next(interaction)

    class DealGuildSettingsPage(UiPage):
        def __init__(self, ui : UI):
            UiPage.__init__(self, ui)
            self.title = "Guild Settings"
            self.description = "Choose where deals messages will be sent and who will be mentioned"

            self.add_field(
                name="1. Deals Channel(s)",
                value="Select the channel(s) where deals will be posted.",
                inline=False
            )

            self.add_field(
                name="2. Update Role",
                value="Select the role that will receive notifications after an update",
                inline=False
            )

        @channel_select(placeholder="1. Deals Channel(s) [Required]",max_values=3, channel_types=[ChannelType.text, ChannelType.news])
        async def giveaway_channel(self, select: ChannelSelect, interaction : Interaction):
            self.config['channels'] = ([channel.id for channel in select.values.channels] if len(select.values.channels) > 0 else [])

        @role_select(placeholder="2. Update Role [Optional]", min_values=0, max_values=1)
        async def giveaway_role(self, select: RoleSelect, interaction : Interaction):
            self.config['role'] = select.values[0].id if len(select.values) > 0 else None

        async def on_next(self, interaction : Interaction):
            if len(self.config.get('channels', [])) == 0: 
                await interaction.response.send_message("You must set at least one Deal Channel.", ephemeral=True, delete_after=5)
                return
            
            await super().on_next(interaction)

    class DealSubmitPage(UiSubmitPage):
        def __init__(self, ui : UI):
            UiSubmitPage.__init__(self, ui)

# Game Pages

class GiveawayGamePage(Page):
    def __init__(self, game_data : dict, role : Role | None = None): # NOTE: Sostituire role : Role | None = None con role : list[Role] | None = None
        Page.__init__(self, 
            title=game_data['title'], 
            timestamp=datetime.datetime.now(datetime.UTC),
            description=f"{game_data['description']}\nMentions: {role.mention if role else ""}",
            url=game_data['gamerpower_url'],
            colour=Colour.green(),
            timeout=0
        )
        self.set_image(url=game_data['image'])
        self.add_field(name="Platform(s)", value=game_data['platforms'], inline=True)
        self.add_field(name="Type", value=game_data['type'], inline=True)
        self.add_field(name="Users", value=game_data["users"], inline=True)

        self.add_field(name="Price", value=f'~~{game_data['worth']}~~  :free:', inline=False)

        start_dt = datetime.datetime.strptime(game_data["published_date"], "%Y-%m-%d %H:%M:%S")
        self.add_field(name="Published", value=f"<t:{int(start_dt.timestamp())}>", inline=True)

        if (end_date_str:=game_data["end_date"]) != "N/A":
            end_dt = datetime.datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
            self.add_field(name="Expires", value=f"<t:{int(end_dt.timestamp())}:R>", inline=True)
        else:
            self.add_field(name="Expires", value=end_date_str, inline=True)

        self.add_field(name="Instructions", value=game_data['instructions'], inline=False)

        self.open_giveaway = Button(
            label=("Get Giveaway" if game_data['type'] == "Game" else "Get Loot") if game_data['type'] != "Early Access" else "Get Beta", 
            style=ButtonStyle.link,
            url=game_data["open_giveaway"]
        )
        self.add_item(self.open_giveaway)

        self.view_giveaway = Button(
            label=("View Giveaway" if game_data['type'] == "Game" else "View Loot") if game_data['type'] != "Early Access" else "View Beta", 
            style=ButtonStyle.link,
            url=game_data["gamerpower_url"]
        )
        self.add_item(self.view_giveaway)

        self.set_author(name="GamerPower", icon_url="https://www.gamerpower.com/assets/images/logo.png")
        self.set_footer(text=f"Powered by GamerPower", icon_url="https://www.gamerpower.com/assets/images/logo.png")

class CheapGamePage(Page):
    def __init__(self, deal_data : dict, role : Role | None = None):
        Page.__init__(self, 
            colour=Colour.green(),
            title=deal_data['title'],
            url=f"https://www.cheapshark.com/redirect?dealID={deal_data['dealID']}",
            description=f"{role.mention if role else ''} Take a look at this deal!",
            timestamp=datetime.datetime.now(datetime.UTC),
            timeout=0
        )
        self.set_image(url=deal_data['thumb'])
        self.set_author(name="CheapShark", icon_url="https://www.cheapshark.com/img/logo_image.png?v=1.0")

        self.add_field(
            name="Ratings",
            value=
            f"""Steam Rating: {"**" + steamRatingText + "**" if (steamRatingText:=deal_data['steamRatingText']) != None else ''} **{deal_data['steamRatingPercent']}%** of the {deal_data['steamRatingCount']} user reviews for this game are positive
            Metacritic Score: **{deal_data['metacriticScore']}%**
            Deal Rating: **{deal_data['dealRating']}**
            """.replace('\t', ''),
            inline=False
        )

        self.add_field(name="Price", value=f'~~{deal_data["normalPrice"]}$~~ **{deal_data["salePrice"]}$** (**{float(deal_data["savings"]):.2f}% less**)', inline=False)
       
        if deal_data['releaseDate'] != 0:
            self.add_field(name="Release Date", value=f"<t:{deal_data['releaseDate']}:D>", inline=False)

        if deal_data['cheapestPrice'].get('price', None) != None:
            self.add_field(
                name="Cheapest Price",
                value=f"**{deal_data['cheapestPrice']['price']}$** on <t:{deal_data['cheapestPrice']['date']}:D>",
                inline=False
            )

        cheaperStores = ""
        for store in deal_data.get('cheapStores', []):
            store = [store.value[1] for store in DealStore if store.value[0] == int(store['storeID'])][0]
            cheaperStores += f"**{store}**: ~~{deal_data["retailPrice"]}$~~ **{deal_data["salePrice"]}$**\n"

        if cheaperStores != '':
            self.add_field(
                name="Cheaper Stores",
                value=cheaperStores,
                inline=False
            )

        button =  Button(
            style=ButtonStyle.url, 
            label="View Deal", 
            url=f"https://www.cheapshark.com/redirect?dealID={deal_data['dealID']}",
        )
        self.add_item(button)

permissions = Permissions(
    administrator=True
)

class CheapGames(Cog):
    def __init__(self, bot: Bot):
        Cog.__init__(self)
        self.db = Database()

        self.giveaways : set[dict] = set()
        self.deals : set[dict] = set()
        self.bot = bot

        self.gp_baseurl = "https://gamerpower.com"
        self.cs_baseurl = "https://www.cheapshark.com"

    @Cog.listener()
    async def on_ready(self):
        if not self.update_giveaways_and_deals.is_running():
            self.update_giveaways_and_deals.start()

    @slash_command(description="Set of commands to create updates whenever a game is on sale or becomes free", default_member_permissions=permissions, integration_types=GUILD_INTEGRATION)
    async def cheapgames(self, interaction : Interaction): pass

    @cheapgames.subcommand(name="add-update", description="Command that allows the addition of an automatic update when a game is on discount or becomes free")
    async def add_update(self, 
            interaction : Interaction,
            update_name : str = SlashOption(description="The name of the update",required=True, min_length=1),
            update_type : str = SlashOption(description="The type of update to add",required=True,choices=Api),
        ):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                config, enabled = await self.db.getExtensionConfig(interaction.guild, Extensions.CHEAPGAMES)

            assert update_name not in config["updates"], f'Update  with name \'{update_name}\' already exists'

            if Api(update_type) == Api.DEALS:
                ui = DealsSetupUI(self.bot,interaction.guild)
            else:
                ui = GiveawaysSetupUI(self.bot,interaction.guild)

            ui.init_pages()

            message = await interaction.followup.send(embed=ui.current_page,view=ui.current_page, wait=True)
            assert not await ui.submit_page.wait(), f'The configuration process has expired'

            config['updates'][update_name] = ui.config

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.CHEAPGAMES, config)

        except AssertionError as e:
            await message.delete()
            await interaction.followup.send(e, ephemeral=True)
        else:
            await message.edit(f"{update_type.capitalize()} update named \'{update_name}\' added successfully!", view=None, embed=None)

    @cheapgames.subcommand(name="del-update", description="Command that allows the removal of an automatic update")
    async def del_update(self, interaction : Interaction):
        pass

    @cheapgames.subcommand(name="list-updates", description="Command that lists all the automatic updates")
    async def list_updates(self, interaction : Interaction):
        pass

    @cheapgames.subcommand(name="trigger-update", description="Command that triggers an update manually")
    async def trigger_update(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                config, enabled = await self.db.getExtensionConfig(interaction.guild, Extensions.CHEAPGAMES)
            assert enabled, f'The extension is not enabled'

            configuration = await self.handle_server_updates((interaction.guild.id, Extensions.CHEAPGAMES.value, enabled, config))

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.CHEAPGAMES, configuration[3])
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed(), ephemeral=True)
        except AssertionError as e:
            await interaction.followup.send(e, ephemeral=True)
        else:
            await interaction.followup.send("Update triggered successfully", ephemeral=True)

    @tasks.loop(time=[datetime.time(hour=h, minute=0, second=0) for h in range(0, 24)])
    async def update_giveaways_and_deals(self):
        try:
            async with self.db:
                configurations = await self.db.getAllExtensionConfig(Extensions.CHEAPGAMES)
            
            tasks : list[asyncio.Task] = []
            for guild_id, ext_id, enabled, config in configurations:
                if not enabled: continue

                coro = self.handle_server_updates((guild_id, ext_id, enabled, config))

                task = asyncio.create_task(coro)
                tasks.append(task)

            completed = await asyncio.gather(*tasks)

            async with self.db:
                await self.db.editAllExtensionConfig(completed)
        except AssertionError as e:
            pass
        except Exception as e:
            logger.error(e)
            raise e

    async def handle_server_updates(self, configuration : tuple[int, str, bool, dict[str, dict[str, dict]]]) -> dict:
        guild_id, _, _, config = configuration
        for update_name, update_config in config['updates'].items():
            if Api(update_config["api"]) == Api.GIVEAWAYS:
                await self.send_giveaway_update(guild_id, update_config)
            else:
                await self.send_deal_update(guild_id,update_config)

        return configuration

    async def send_giveaway_update(self, guild_id : int, update_config : dict):
        giveaway_types : list = update_config["types"]
        giveaway_stores : list = update_config["stores"]
        giveaway_channels : list = update_config["channels"]
        giveaway_role_id : int = update_config["role"]
        saved_giveaways : dict = update_config["saved"]

        # NOTE: Quando ottengo i nuovi giveaway non devo sostituirli con quelli precedenti ma aggiungere quelli nuovi alla lista

        content_type, content, code, reason = await asyncget(f"{self.gp_baseurl}/api/giveaways")
        assert content_type == 'application/json' and code == 200, f'Error while fetching new giveaways (code: {code}): {reason}'

        self.giveaways =json.loads(content)

        guild = self.bot.get_guild(guild_id)
        if guild: role = guild.get_role(giveaway_role_id)
        else: role = None

        n_send : int = 0  # Number of games to send
        for game in self.giveaways:
            str_game_id = str(game["id"])

            if len(giveaway_stores) > 0 and not any(store in str(game["platforms"]).lower().split(", ") for store in giveaway_stores): 
                continue
            if len(giveaway_types) > 0 and not str(game["type"]).lower() in giveaway_types:
                continue

            current_dt = datetime.datetime.strptime(game["published_date"], "%Y-%m-%d %H:%M:%S").astimezone(datetime.UTC)

            if current_dt < datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1):
                # Here we are checking if the date of this giveaway is older than one day
                continue

            current_dt = datetime.datetime.strptime(game["published_date"], "%Y-%m-%d %H:%M:%S").astimezone(datetime.UTC)
            saved_dt = datetime.datetime.strptime(saved_giveaways[str(game["id"])], "%Y-%m-%d %H:%M:%S").astimezone(datetime.UTC) if saved_giveaways.get(str_game_id, None) else None

            if str_game_id in saved_giveaways and ((current_dt <= saved_dt) if saved_dt else False):
                print('already registered')
                # Here we are checking if this giveaway is already registered
                continue
            

            n_send += 1

            saved_giveaways[str_game_id] = game["published_date"]

            for channel in giveaway_channels:
                if (channel:=self.bot.get_channel(channel)) is None:
                    continue

                ui = GiveawayGamePage(game, role)

                message = await channel.send(embed=ui, view=ui)

                if message.channel.is_news():
                    try:
                        await message.publish()
                    except Exception as e:
                        logger.exception(e)

            if n_send >= 10: # Send only 10 games at a tine
                break

    async def send_deal_update(self, guild_id : int, update_config : dict):
        """
        content_type, content, code, reason = await asyncget(f"{self.cs_baseurl}/api/1.0/stores?lastChange=")
        if content_type == 'application/json' or code == 200:
            shops_lastchange = json.loads(content)
        else:
            logger.error(f'Failed to get stores last changes: {reason}')
            shops_lastchange = {}

        for store_id, shop in shops_lastchange.items():
            pass
        """

        # NOTE: Per implementare i deals non dovrei tenere conto solo della data di pubblicazione del deal insieme all'id del deal
        #       Ma dovrei anche tenere in considerazione un enpoint fornito dall'api:
        #
        #       https://www.cheapshark.com/api/1.0/stores?lastChange=
        #
        #       Endpoint che permette di vedere l'ultima modifica effettuata ad ogni store
        #       Cosi' da sapere quali store devo andare a controllare per aggiornare i deals
        #       Inoltre non mi devo limitare ad ottenere i dati dei deals ma devo fare anche:
        #
        #       https://www.cheapshark.com/api/1.0/games?id={id}
        #
        #       per ottenere dati piu' specifici per ogni negozio
        #       il parametro onSale deve essere sempre settato su on quando vado a fare le query
        #       per evitare di ottenere deal che non sono in vendita

        channels : list[int] = update_config.get('channels', [])
        saved : dict = update_config.get('saved', {})
        role_id = update_config.get("role", None)

        storeids = ','.join(update_config.get("storeIDs1", []) + update_config.get("storeIDs2", []))
        tripleA = update_config.get('AAA', True)
        steamworks = update_config.get('steamworks', False)
        upper_price = update_config.get("upperPrice", 50)
        lower_price = update_config.get('lowerPrice', 0)
        minSteamRating = update_config.get("minSteamRating", 0)
        minMetacriticRating = update_config.get("minMetacriticRating", 0)

        params = {
            'AAA' : tripleA,
            'upperPrice' : upper_price,
            'lowerPrice' : lower_price,
            'steamworks' : steamworks,
            'onSale' : True,
            "minSteamRating": minSteamRating,
            "minMetacriticRating": minMetacriticRating
        }
        if len(storeids) > 0:
            params.update(storeID=storeids)

        url = f"{self.cs_baseurl}/api/1.0/deals?{'&'.join(f"{key}={value}" for key, value in params.items())}"

        content_type, content, code, reason = await asyncget(url)
        if content_type != 'application/json' or code != 200:
            logger.error(f'Error while fetching new giveaways (code: {code}): {reason}')
        else:
            self.deals = json.loads(content)

        guild = self.bot.get_guild(guild_id)
        if guild and role_id: 
            role = guild.get_role(role_id)
        else: 
            role = None

        n_send = 0
        for deal in self.deals:
            str_game_id = str(deal["gameID"])

            current_dt = datetime.datetime.fromtimestamp(deal["lastChange"],datetime.UTC)

            if current_dt < datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1):
                print('older than one day')
                # Here we are checking if the date of this giveaway is older than one day
                continue

            saved_dt = datetime.datetime.fromtimestamp(saved[str_game_id], datetime.UTC) if saved.get(str_game_id, None) else None

            if str_game_id in saved and ((current_dt <= saved_dt) if saved_dt else False):
                print('already registered')
                # Here we are checking if this giveaway is already registered
                continue

            deal_url = f"{self.cs_baseurl}/api/1.0/deals?id={deal['dealID']}"
            content_type, content, code, reason = await asyncget(deal_url)
            deal_info = json.loads(content)

            print(deal_info)

            if content_type == 'application/json' or code == 200:
                deal['cheaperStores'] = deal_info.get('cheaperStores', [])
                deal['cheapestPrice'] = deal_info.get('cheapestPrice', {})

            n_send += 1

            saved[str_game_id] = deal["lastChange"]

            for channel in channels:
                if (channel:=self.bot.get_channel(channel)) is None:
                    # Eliminare i canali non piu' validi dalla configurazione
                    continue

                page = CheapGamePage(deal, role)

                message = await channel.send(embed=page, view=page)

                if message.channel.is_news():
                    try:
                        await message.publish()
                    except Exception as e:
                        logger.exception(e)
            
            if n_send >= 10: # Send only 10 games at a tine
                break

def setup(bot : Bot):#
    bot.add_cog(CheapGames(bot))
