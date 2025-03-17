from nextcord.ext.commands import Bot, Cog
from nextcord.ext import tasks
from nextcord import \
    Permissions,     \
    HTTPException,   \
    NotFound,        \
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
import datetime
import asyncio
import json

from utils.exceptions import ExtensionException, GGsBotException
from utils.terminal import getlogger
from utils.db import Database
from utils.abc import UI, UiPage, UiSubmitPage, Page
from utils.commons import \
    Extensions,           \
    GLOBAL_INTEGRATION,   \
    GUILD_INTEGRATION,    \
    USER_INTEGRATION,     \
    isdeveloper,         \
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
    STEAM =                 (1,  "Steam"              )
    GAMERSGATE =            (2,  "Gamers Gate"        )
    GREENMANGAMING =        (3,  "Green Man Gaming"   )
    AMAZON =                (4,  "Amazon"             )
    GAMESTOP =              (5,  "GameStop"           )
    DIRECT2DRIVE =          (6,  "Direct 2 Drive"     )
    GOG =                   (7,  "GoG"                )
    ORIGIN =                (8,  "Origin"             )
    GETGAMES =              (9,  "Get Games"          )
    SHINYLOOT =             (10, "Shiny Loot"         )
    HUMBLESTORE =           (11, "Humble Store"       )
    DESURA =                (12, "Desura"             )
    UPLAY =                 (13, "Uplay"              )
    INDIEGAMESTAND =        (14, "Indie Games Stand"  )
    FANATICAL =             (15, "Fanatical"          )
    GAMESROCKET =           (16, "Games Rocket"       )
    GAMESREPUBLIC =         (17, "Games Republic"     )
    SILAGAMES =             (18, "Sila Games"         )
    PLAYFIELD =             (19, "Play Field"         )
    IMPERIALGAMES =         (20, "Imperial Games"     )
    WINGAMESTORE =          (21, "Win Game Store"     )
    FUNSTOCKDIGITAL =       (22, "Fun Stock Digital"  )
    GAMEBILLET =            (23, "Game Billet"        )
    VOIDU =                 (24, "Voidu"              )
    EPICGAMESTORE =         (25, "Epic Games Store"   )
    RAZERGAMESTORE =        (26, "Razer Games Store"  )
    GAMESPLANET =           (27, "Games Planet"       )
    GAMESLOAD =             (28, "Games Load"         )
    TWOGAME =               (29, "2Game"              )
    INDIEGALA =             (30, "IndieGala"          )
    BLIZZARDSHOP =          (31, "Blizzard Shop"      )
    ALLYOUPLAY =            (32, "All You Play"       )
    DLGAMER =               (33, "DL Gamer"           )
    NOCTRE =                (34, "Noctre"             )
    DREAMGAME =             (35, "DreamGame"          )

hours_select = [SelectOption(label=f'{h:02}:00 ({h if h == 12 else int(h % 12):02}:00 {"PM" if h > 11 else "AM"}) (UTC)', value=h) for h in range(0, 25)]

# CheapGames Ui 

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
            try:
                if len(self.config.get('channels', [])) == 0:
                    raise GGsBotException(
                        title="Missing Argument",
                        description="You must set at least one Giveaway Channel.",
                        suggestions="Please set a Giveaway Channel and then try again."
                    )
            except GGsBotException as e:
                await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)
            else:
                await super().on_next(interaction)

    class GiveawaySubmitPage(UiSubmitPage):
        def __init__(self, ui : UI):
            UiSubmitPage.__init__(self, ui)
            self.description = "All data saved so far will be saved."

            self.add_field(
                name="Next Update",
                value="The first update will be at minute 0 of the next hour",
                inline=False
            )

class DealsSetupUI(UI):
    def __init__(self, bot : Bot, guild : Guild):
        UI.__init__(self, bot, guild)
        self.config = {
            "channels" : [],
            "saved" : {},
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
            try:
                if self.config['lowerPrice'] > self.config['upperPrice']:
                    raise GGsBotException(
                        title="Invalid Price Range",
                        description="The lower price must be less than or equal to the upper price.",
                        suggestions="Please adjust the price range and try again.",
                    )
            except GGsBotException as e:
                await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)
            else:
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
            try:
                if len(self.config.get('channels', [])) == 0: 
                    raise GGsBotException(
                        title="Missing Argument",
                        description="You must set at least one Deal Channel.",
                        suggestions="Please set a Deal Channel and then try again."
                    )
            except GGsBotException as e:
                await interaction.response.send_message(embed=e.asEmbed(), ephemeral=True, delete_after=5)
            else:
                await super().on_next(interaction)

    class DealSubmitPage(UiSubmitPage):
        def __init__(self, ui : UI):
            UiSubmitPage.__init__(self, ui)
            self.description = "All data saved so far will be saved."

            self.add_field(
                name="Next Update",
                value="The first update will be at minute 0 of the next hour",
                inline=False
            )

# CheapGames Pages

class ViewUpdatesPage(Page):
    def __init__(self, bot : Bot, data : dict):
        Page.__init__(self,
            title="CheapGames Updates",
            timestamp = datetime.datetime.now(datetime.UTC),
            colour=Colour.green(),
            timeout=0
        )
        self.description = "Here are a list of all CheapGames updates created for this server:" \
                            if len(data['updates']) > 0 else                                    \
                           "There are no updates created for this server."

        for update, config in data['updates'].items():
            channels = [f'{channel.mention}' for channel_id in config['channels'] if (channel:=bot.get_channel(channel_id))]
            self.add_field(
                name=f"Name: {update}",
                value=f"Type: {config['api']}\nChannel(s): {','.join(channels)}\n",
                inline=False
            )

        self.set_author(name=bot.user.display_name, icon_url=(bot.user.avatar if bot.user.avatar else bot.user.default_avatar).url)

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

        if deal_data['releaseDate'] != 0:
            self.add_field(name="Release Date", value=f"<t:{deal_data['releaseDate']}:D>", inline=False)

        deal_shop_names = [s.value[1] for s in DealStore if s.value[0] == int(deal_data['storeID'])]

        if len(deal_shop_names) > 0:
            self.add_field(
                name="Shop",
                value=deal_shop_names[0],
                inline=False
            )

        self.add_field(
            name="Ratings",
            value=
            f"""Steam Rating: {"**" + steamRatingText + "**" if (steamRatingText:=deal_data['steamRatingText']) != None else ''} **{deal_data['steamRatingPercent']}%** of the {deal_data['steamRatingCount']} user reviews for this game are positive
            Metacritic Score: **{deal_data['metacriticScore']}%**
            Deal Rating: **{deal_data['dealRating']}**
            """.replace('\t', ''),
            inline=False
        )

        self.add_field(
            name="Price", 
            value=f'~~{deal_data["normalPrice"]}$~~ **{deal_data["salePrice"]}$** (**{float(deal_data["savings"]):.2f}% less**)', 
            inline=False
        )

        cheaperStores = ""
        for store in deal_data.get('cheaperStores', []):
            cheaper_store_names = [s.value[1] for s in DealStore if s.value[0] == int(store['storeID'])]

            if len(cheaper_store_names) == 0:
                logger.error(f"Could not find game with id: {store['storeID']}")
                continue

            cheaperStores += f"**{cheaper_store_names[0]}**: ~~{store["retailPrice"]}$~~ **{store["salePrice"]}$**\n"

        if cheaperStores != '':
            self.add_field(
                name="Cheaper Stores",
                value=cheaperStores,
                inline=False
            )

        if deal_data['cheapestPrice'].get('price', None) != None:
            self.add_field(
                name="Cheapest Price",
                value=f"**{deal_data['cheapestPrice']['price']}$** on <t:{deal_data['cheapestPrice']['date']}:D>",
                inline=False
            )

        button = Button(
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

        self.giveaways : list[dict] = []
        self.deals : list[dict] = []
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

            if update_name in config['updates']: raise ValueError(f'Update  with name \'{update_name}\' already exists')

            if Api(update_type) == Api.DEALS:
                ui = DealsSetupUI(self.bot,interaction.guild)
            else:
                ui = GiveawaysSetupUI(self.bot,interaction.guild)

            ui.init_pages()

            message = await interaction.followup.send(embed=ui.current_page,view=ui.current_page, wait=True)
            expired = await ui.submit_page.wait()

            if expired:
                try:
                    await message.delete()
                except (Forbidden, NotFound, HTTPException) as e:
                    logger.exception(e)

                raise TimeoutError(f'The configuration process has expired')


            config['updates'][update_name] = ui.config

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.CHEAPGAMES, config)

        except (ValueError, TimeoutError) as e:
            await interaction.followup.send(e, ephemeral=True)
        else:
            await message.edit(f"{update_type.capitalize()} update named \'{update_name}\' added successfully!", view=None, embed=None)

    @cheapgames.subcommand(name="del-update", description="Command that allows the removal of an automatic update")
    async def del_update(self, 
            interaction : Interaction, 
            update_name : str = SlashOption(description="Name of the update to be deleted", required=True, min_length=1)
        ):
        try:
            await interaction.response.defer(ephemeral=True)
            
            async with self.db:
                config, enabled = await self.db.getExtensionConfig(interaction.guild, Extensions.CHEAPGAMES)

            if update_name not in config['updates']:
                raise ValueError(f"CheapGames update with name \'{update_name}\' does not exist.")

            config['updates'].pop(update_name)

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.CHEAPGAMES, config)

        except (HTTPException,ExtensionException) as e:
            logger.exception(e)
        except (ValueError, TimeoutError) as e:
            await interaction.followup.send(e, ephemeral=True)
        else:
            await interaction.followup.send(f"Update named \'{update_name}\' removed successfully!", ephemeral=True)

    @cheapgames.subcommand(name="list-updates", description="Command that lists all the automatic updates")
    async def list_updates(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            async with self.db:
                config, enabled = await self.db.getExtensionConfig(interaction.guild, Extensions.CHEAPGAMES)

            page = ViewUpdatesPage(self.bot, config)

        except (HTTPException,ExtensionException) as e:
            logger.exception(e)
        else:
            await interaction.followup.send(embed=page, ephemeral=True)

    @cheapgames.subcommand(name="trigger-update", description="Command that triggers an update manually")
    @isdeveloper()
    async def trigger_update(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            async with self.db:
                config, enabled = await self.db.getExtensionConfig(interaction.guild, Extensions.CHEAPGAMES)
            if not enabled: raise ExtensionException("Not Enabled")

            await self.retrive_giveaways_data()

            configuration = await self.handle_server_updates((interaction.guild.id, Extensions.CHEAPGAMES.value, enabled, config))

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.CHEAPGAMES, configuration[3])
        except ExtensionException as e:
            await interaction.followup.send(embed=e.asEmbed(), ephemeral=True)
        else:
            await interaction.followup.send("Update triggered successfully", ephemeral=True)


    async def retrive_giveaways_data(self):
        try:
            content_type, content, code, reason = await asyncget(f"{self.gp_baseurl}/api/giveaways")
            
            if content_type != "application/json" or code != 200:
                raise ValueError(f'Error while fetching new giveaways (code: {code}): {reason}')
            
            self.giveaways = json.loads(content)
        except Exception as e:
            logger.exception(e)

    @tasks.loop(time=[datetime.time(hour=h, minute=0, second=0) for h in range(0, 24)])
    async def update_giveaways_and_deals(self):
        try:
            async with self.db:
                configurations = await self.db.getAllExtensionConfig(Extensions.CHEAPGAMES)

            await self.retrive_giveaways_data()

            tasks : list[asyncio.Task] = []
            for guild_id, ext_id, enabled, config in configurations:
                if not enabled: continue

                coro = self.handle_server_updates((guild_id, ext_id, enabled, config))

                task = asyncio.create_task(coro)
                tasks.append(task)

            completed = await asyncio.gather(*tasks)

            async with self.db:
                await self.db.editAllExtensionConfig(completed)
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

        if content_type != 'application/json' or code != 200:
            logger.exception(f'Error while fetching new giveaways (code: {code}): {reason}')
        else:
            self.giveaways = json.loads(content)

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

                try:
                    if message.channel.is_news(): await message.publish()
                except HTTPException as e:
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
            "minMetacriticRating": minMetacriticRating,
            "maxAge" : 1 # Get only latest deals (1 hour)
        }
        if len(storeids) > 0: params.update(storeID=storeids)

        # Sostituire questo metodo per ottenere i dati con uno piu' centralizzato
        # Per come funziona ora, vengono ottenuti i deal per ogni update impostato dall'utente, il che e' poco efficente
        # Dovrei ottenere i dati solo una volta e poi utilizzarli per tutti gli update

        url = f"{self.cs_baseurl}/api/1.0/deals?{'&'.join(f"{key}={value}" for key, value in params.items())}"
        content_type, content, code, reason = await asyncget(url)
        if content_type != 'application/json' or code != 200:
            logger.error(f'Error while fetching new giveaways (code: {code}): {reason}')
        else:
            self.deals = json.loads(content)

        # ---

        guild = self.bot.get_guild(guild_id)
        role = guild.get_role(role_id) if role_id and guild else None

        n_send = 0
        for deal in self.deals:
            str_game_id = str(deal["gameID"])

            current_dt = datetime.datetime.fromtimestamp(deal["lastChange"],datetime.UTC)

            if current_dt < datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1):
                # Here we are checking if the date of this giveaway is older than one hour
                continue

            saved_dt = datetime.datetime.fromtimestamp(saved[str_game_id], datetime.UTC) if saved.get(str_game_id, None) else None

            if str_game_id in saved and ((current_dt <= saved_dt) if saved_dt else False):
                # Here we are checking if this giveaway is already registered
                continue

            deal_url = f"{self.cs_baseurl}/api/1.0/deals?id={deal['dealID']}"
            content_type, content, code, reason = await asyncget(deal_url)

            if code == 200:
                deal_info = json.loads(content)

                deal['cheaperStores'] = deal_info.get('cheaperStores', [])
                deal['cheapestPrice'] = deal_info.get('cheapestPrice', {})

            saved[str_game_id] = deal["lastChange"]

            n_send += 1

            for channel_id in channels.copy():
                if (channel:=self.bot.get_channel(channel_id)) is None:
                    channels.remove(channel_id)
                    continue

                page = CheapGamePage(deal, role)

                message = await channel.send(embed=page, view=page)

                try:
                    if message.channel.is_news(): await message.publish()
                except HTTPException as e:
                    pass
            
            if n_send >= 10: # Send only 10 games at a tine
                break

def setup(bot : Bot):
    bot.add_cog(CheapGames(bot))
