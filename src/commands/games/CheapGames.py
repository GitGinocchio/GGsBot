# Se dopo aver fatto una fetch al al database e' presente lo stesso:
# - gameid
# - publish_datetime

# allora non e' necessario inviare il messaggio

"""
updated : [
    {
        "name" : "",
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
    {
        "name" : "",
        "channels" : [],
        "api" : "GIVEAWAYS"
        "type" : "game" | "loot" | "beta" | "all"
        "stores" : "Steam" | etc.
        "saved" : {
            gameID : publish_time
        },
        "on" : "hour"
    },

]

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
    SelectOption,    \
    ChannelType,     \
    SlashOption,     \
    Interaction,     \
    Guild,           \
    Embed,           \
    slash_command
from nextcord.ui import \
    ChannelSelect,      \
    StringSelect,       \
    Item,               \
    View,               \
    button,             \
    string_select,      \
    channel_select,     \
    role_select

from enum import StrEnum
import datetime
import asyncio
import time

from utils.commons import Extensions, asyncget
from utils.terminal import getlogger
from utils.db import Database
from utils.abc import SetupUI

logger = getlogger()

class Api(StrEnum):
    DEALS =                 "deals"
    GIVEAWAYS =             "giveaways"

class GiveawayType(StrEnum):
    GAME =                  "game"
    LOOT =                  "loot"
    BETA =                  "beta"

class GiveawayStore(StrEnum):
    PC =                    "pc"
    STEAM =                 "steam"
    EPIC =                  "epic-games-store"
    UBISOFT =               "ubisoft"
    GOG =                   "gog"
    ITCHIO =                "itchio"
    PS4 =                   "ps4"
    PS5 =                   "ps5"
    XBOX_ONE =              "xbox-one"
    XBOX_SERIES_XS =        "xbox-series-xs"
    SWITCH =                "switch"
    ANDROID =               "android"
    IOS =                   "ios"
    VR =                    "vr"
    BATTLENET =             "battlenet"
    ORIGIN =                "origin"
    DRM_FREE =              "drm-free"
    XBOX_360 =              "xbox-360"

hours_select = [SelectOption(label=f'{h:02}:00 ({h if h == 12 else int(h % 12):02}:00 {"PM" if h > 11 else "AM"}) (UTC)', value=h) for h in range(0, 25)]

class GiveawaysUI(SetupUI):
    giveaway_types = [SelectOption(label=type.value.capitalize(), value=type.value) for type in GiveawayType]
    store_types = [SelectOption(label=type.value.capitalize(), value=type.value) for type in GiveawayStore]
    def __init__(self, bot : Bot, guild : Guild):
        SetupUI.__init__(self, bot, guild, "Add Giveaway Update", self.on_submit,"Setup")
        self.config = {'channels' : [], 'types' : [], 'stores' : [], 'api' : Api.GIVEAWAYS.value, 'on' : None, 'saved' : {}}
        self.description = "This command allows you to add an update whenever games for different platforms become free"

        self.add_field(
            name="1. Giveaway Channel(s)",
            value="Select the channel(s) where giveaways will be posted.",
            inline=False
        )
        self.add_field(
            name="2. Giveaway Type",
            value="Select the type of giveaway.\n(no choice=all types)",
            inline=False
        )
        self.add_field(
            name="3. Store",
            value="Select the game store you would like to giveaways from.\n(no choice=all shops)",
            inline=False 
        )
        self.add_field(
            name="4. Update hour",
            value="Specify the hour (UTC) of day you would like to update giveaways at.",
            inline=False 
        )

    @channel_select(placeholder="1. Select the channels where giveaways will be posted.",max_values=3, channel_types=[ChannelType.text, ChannelType.news])
    async def giveaway_channel(self, select: ChannelSelect, interaction : Interaction):
        self.config['channels'] = ([channel.id for channel in select.values.channels] if len(select.values.channels) > 0 else [])

    @string_select(placeholder="2. Select the type of giveaway.", options=giveaway_types, min_values=0,max_values=len(giveaway_types))
    async def giveaway_type(self, select: StringSelect, interaction : Interaction):
        self.config['types'] = select.values

    @string_select(placeholder="3. Select the game store you would like to giveaways from.", options=store_types, min_values=0,max_values=len(store_types))
    async def giveaway_store(self, select: StringSelect, interaction : Interaction):
        self.config['stores'] = select.values

    @string_select(placeholder="4. Select the hour (UTC) of the day you would like to receive giveaways.",options=hours_select)
    async def giveaway_hour(self, select: StringSelect, interaction : Interaction):
        self.config['on'] = int(select.values[0]) if len(select.values) > 0 else None

    async def on_submit(self, interaction : Interaction):
        try:
            assert len(self.config.get('channels',[])) > 0, f'You must set at least one channel for the giveaway.'
            assert self.config.get('on', None) is not None, f'You must set the hour you would like to receive giveaways.'
        except AssertionError as e:
            await interaction.response.send_message(e, ephemeral=True, delete_after=5)
        except Exception as e:
            print(e)
        else:
            self.stop()

class DealsUI(SetupUI):
    def __init__(self, bot : Bot, guild : Guild, name : str):
        SetupUI.__init__(self, bot, guild, "Add Deals Update", self.on_submit, "Setup")

    async def on_submit(self, interaction : Interaction):
        pass

class CheapGames(Cog):
    def __init__(self, bot: Bot):
        Cog.__init__(self)
        self.db = Database()
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.update_deals.is_running():
            self.update_deals.start()

    @slash_command(description="Set of commands to create updates whenever a game is on sale or becomes free")
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
                ui = DealsUI(self.bot,interaction.guild)
            else:
                ui = GiveawaysUI(self.bot,interaction.guild)

            message = await interaction.followup.send(embed=ui,view=ui, wait=True)
            assert not await ui.wait(), f'The configuration process has expired'

            config['updates'][update_name] = ui.config

            async with self.db:
                await self.db.editExtensionConfig(interaction.guild, Extensions.CHEAPGAMES, config)

        except AssertionError as e:
            if message: 
                await message.edit(e, view=None, embed=None)
            else:
                await interaction.followup.send(e, ephemeral=True)
        else:
            await message.edit(f"{update_type.capitalize()} update named \'{update_name}\' added successfully!", view=None, embed=None)

    @cheapgames.subcommand(name="del-update", description="Command that allows the removal of an automatic update")
    async def del_update(self, interaction : Interaction):
        pass

    @tasks.loop(time=[datetime.time(hour=h, minute=0, second=0, tzinfo=datetime.timezone.utc) for h in range(0, 24)])
    async def update_deals(self):
        try:
            async with self.db:
                configurations = await self.db.getAllExtensionConfig(Extensions.CHEAPGAMES)

            tasks : list[asyncio.Task] = []
            for guild_id, extension_id, enabled, config in configurations:
                config : dict[str, dict[str, dict]]

                if not enabled: continue

                for update_name, update_config in config['updates'].items():
                    if time.localtime().tm_hour != int(update_config["on"]):
                        continue

                    if Api(update_config["api"]) == Api.GIVEAWAYS:
                        coro = self.send_giveaway_update(update_name, update_config)
                    else:
                        coro = self.send_deal_update(update_name, update_config)

                    task = asyncio.create_task(coro)
                    tasks.append(task)
                
            # TODO: 
            # 1. Creare tante task quanti sono i server (o gli updates) e devono inviare gli embed dei giochi gratuiti ecc.
            # 2. modificare la configurazioni se bisogna
            # 3. Fare la query al database (solo alla fine di tutte le task)

        except AssertionError as e:
            pass

    async def send_giveaway_update(self, update_name : str, update_config : dict):
        baseurl = "https://gamerpower.com/api"
        endpoint = "/giveaways"
        params = []

        giveaway_types : list = update_config.get("types", [])
        giveaway_stores : list = update_config.get("stores", [])


        if (len_types:=len(giveaway_types)) > 0:
            params.append(f"type={".".join(giveaway_types)}")

        if (len_stores:=len(giveaway_stores)) > 0:
            params.append(f"platform={".".join(giveaway_stores)}")

        if len_stores > 1 or len_types > 1:
            endpoint = "/filter"

        url = f'{baseurl}{endpoint}{'?' if len(params) > 0 else ''}{'&'.join(params)}'

        games : list[dict] = await asyncget(url)

        for game in games:
            if game["id"] in update_config['saved']:
                pass
            #saved[game.get('id', None)] = game.get("published_date", None)


        return update_name, update_config

    async def send_deal_update(self, update_name : str, update_config : dict):
        return ""


def setup(bot : Bot):
    bot.add_cog(CheapGames(bot))
