from nextcord import Embed,Color,Permissions
from nextcord.ext import commands

from nextcord.ext.commands import Cog
from nextcord import \
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
    File,            \
    slash_command
from nextcord.ui import View, Button, button
from datetime import datetime, timezone
from enum import StrEnum
from io import BytesIO
import json
import re

from utils.commons import asyncget
from utils.terminal import getlogger
from utils.abc import Page

logger = getlogger()

class Font(StrEnum):
    AndaleMono = "Andale Mono"
    Impact = "Impact"
    Arial = "Arial"
    ArialBlack = "Arial Black"
    ComicSansMS = "Comic Sans MS"
    CourierNew = "Courier New"
    Georgia = "Georgia"
    TimesNewRoman = "Times New Roman"
    Verdana = "Verdana"
    Webdings = "Webdings"

class ImageType(StrEnum):
    SQUARE = "square"
    MEDIUM = "medium"
    SMALL = "small"
    XSMALL = "xsmall"

class Filter(StrEnum):
    MONO = "mono"
    NEGATE = "negate"
    CUSTOM = "custom"

class Fit(StrEnum):
    COVER = "cover"
    CONTAIN = "contain"
    FILL = "fill"
    INSIDE = "inside"
    OUTSIDE = "outside"

class Position(StrEnum):
    TOP = "top"
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    BOTTOM = "bottom"

    LEFT_TOP = "left top"
    LEFT_BOTTOM = "left bottom"

    RIGHT_TOP = "right top"
    RIGHT_BOTTOM = "right bottom"

class TagsPage(Page):
    def __init__(self, tags : list):
        Page.__init__(self,
            title="Random Cats | Tags",
            colour=Colour.green(),
            description="Here are all the tags available for random cats. You can use these tags to filter the results.",
            timestamp=datetime.now(timezone.utc)
        )
        self.tags = tags
        self.page = 0
        self.max_page = (len(self.tags) // 25) + 1
        
        self.add_field(
            name=f"Tags (Page {self.page+1}/{self.max_page})",
            value="\n".join([f"{i+1}) {tags[i]}" for i in range(self.page*25, min(len(self.tags),(self.page+1)*25), 1)]),
            inline=False
        )

    @button(label="Previous", style=ButtonStyle.secondary)
    async def prev(self, button : Button, interaction : Interaction):
        if self.page - 1 < 0:
            await interaction.send("You are already on the first page", delete_after=5, ephemeral=True) 
            return
        self.page -= 1

        self.set_field_at(0,
            name=f"Tags (Page {self.page+1}/{self.max_page})",
            value="\n".join([f"{i+1}) {self.tags[i]}" for i in range(self.page*25, min(len(self.tags),(self.page+1)*25), 1)]),
            inline=False
        )

        await interaction.response.edit_message(embed=self, view=self)

    @button(label="Next", style=ButtonStyle.primary)
    async def next(self, button : Button, interaction : Interaction):
        if self.page + 1 >= self.max_page: 
            await interaction.send("You are already on the last page", delete_after=5, ephemeral=True) 
            return
        self.page += 1

        self.set_field_at(0,
            name=f"Tags (Page {self.page+1}/{self.max_page})",
            value="\n".join([f"{i+1}) {self.tags[i]}" for i in range(self.page*25, min(len(self.tags),(self.page+1)*25), 1)]),
            inline=False
        )

        await interaction.response.edit_message(embed=self, view=self)



class RandomCats(commands.Cog):
    def __init__(self, bot : commands.Bot):
        commands.Cog.__init__(self)
        self.baseurl = "https://cataas.com"
        self.bot = bot
        self.tags = None
        self.fetched_tags = False

    @Cog.listener()
    async def on_ready(self):
        if not self.fetched_tags:
            try:
                content_type, content, code, reason = await asyncget(f'{self.baseurl}/api/tags')
                if content_type != 'application/json' or code != 200:
                    raise ValueError(f'Error while fetching tags (code: {code}): {reason}')
                self.tags : list = json.loads(content)
                self.fetched_tags = True
            except (ValueError, TimeoutError) as e:
                self.tags = []
                logger.error(e)

    @slash_command(name="cats", description="Set of commands to get cat images")
    async def cats(self, interaction : Interaction): pass

    @cats.subcommand(name="tags",description="Get all available tags")
    async def get_tags(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            page = TagsPage(self.tags)

        except ValueError as e:
            await interaction.followup.send(e, ephemeral=True, delete_after=5)
        else:
            await interaction.followup.send(embed=page, view=page, ephemeral=True)

    @cats.subcommand(name="randomcat",description="Get a random cat image")
    async def randomcat(self, 
        interaction : Interaction,
        tags : str = SlashOption(description="send a random image of a cat based on tags e.g. gif,cute", default="", required=False),
        text : str = SlashOption(description="Text to be displayed on the image", default=" ", required=False),
        font : str  = SlashOption(description="Font of the text (default: Impact)", default=Font.Impact.value, choices=Font, required=False),
        fontsize : int = SlashOption(description="Size of the font (min: 10, max: 100, default: 30)", default=30, required=False, max_value=100, min_value=10),
        fontcolor : str = SlashOption(description="Color of the font e.g. #fffffff or white (default: white)", default="white", required=False),
        fontbackground : str = SlashOption(description="Background color of the font e.g. #fffffff or white", default=None, required=False),
        type : str = SlashOption(description="Type of the image (default: square)", choices=ImageType, default=ImageType.SQUARE, required=False),
        filter : str | None = SlashOption(description="Filter of the image", choices=Filter, default=None, required=False),
        fit : str | None = SlashOption(description="Fit of the image", choices=Fit, default=None, required=False),
        position : str = SlashOption(description="Position of the text (default: bottom)", default=Position.BOTTOM, choices=Position, required=False),
        width : int | None = SlashOption(description="Width of the image (min: 100, max: 1920)", default=None, required=False, min_value=100, max_value=1920),
        height : int | None = SlashOption(description="Height of the image (min: 100, max: 1080)", default=None, required=False, min_value=100, max_value=1080),
        blur : int | None = SlashOption(description="Blur of the image (min: 0, max: 10, default: None)", default=None, required=False, min_value=0, max_value=10),
        red : int | None = SlashOption(description="Red value of the image (min: 0, max: 255, default: 255)", default=None, required=False, min_value=0, max_value=255),
        green : int | None = SlashOption(description="Green value of the image (min: 0, max: 255, default: 255)", default=None, required=False, min_value=0, max_value=255),
        blue : int | None = SlashOption(description="Blue value of the image (min: 0, max: 255, default: 255)", default=None, required=False, min_value=0, max_value=255),
        brightness : float | None = SlashOption(description="Brightness multiplier of the image (min: -100.0, max: 100.0, default: None)", default=None, required=False, min_value=-100, max_value=100),
        saturation : float | None = SlashOption(description="Saturation multiplier of the image (min: -100.0, max: 100.0, default: None)", default=None, required=False, min_value=-100, max_value=100),
        hue : int | None = SlashOption(description="Hue rotation of the image (min: -360, max: 360, default: 0)", default=None, required=False, min_value=-360, max_value=360),
        lightness : int | None = SlashOption(description="Lightness addend of the image (min: -100, max: 100, default: 0)", default=None, required=False, min_value=-100, max_value=100),
        spoiler : bool = SlashOption(description="Send the image as a spoiler", default=False, required=False),
        ephemeral : bool = SlashOption(description="Send the image as ephemeral", default=False, required=False)
    ):
        try:
            await interaction.response.defer(ephemeral=ephemeral)

            if len(self.tags) == 0: raise ValueError("Tags are not loaded at the moment")

            if tags != "":
                tags_pattern = r"^([_,]+(?:,[_,]+)*$" # comma separated list of strings regex
                assert re.match(tags_pattern, tags) if tags else True, "Tags must be a comma separated list of strings"
                for tag in tags.split(','): 
                    if not tag in self.tags: raise ValueError(f"Tag \'{tag}\' is not an available tag")
            
            params = [
                f'font={font}',
                f'fontSize={fontsize}',
                f'fontColor={fontcolor}',
                f'type={type}',
                f'position={position}',
            ]

            if filter: params.append(f'filter={filter}')
            if fit: params.append(f'fit={fit}')
            if width: params.append(f'width={width}')
            if height: params.append(f'height={height}')
            if brightness: params.append(f'brightness={brightness}')
            if saturation: params.append(f'saturation={saturation}')
            if red: params.append(f'red={red}')
            if green: params.append(f'green={green}')
            if blue: params.append(f'blue={blue}')
            if hue: params.append(f'hue={hue}')
            if lightness: params.append(f'lightness={lightness}')
            if blur: params.append(f'blur={blur}')
            if fontbackground: params.append(f'fontBackground={fontbackground}')

            url = f'{self.baseurl}/cat{f"/{tags}/" if tags else "/"}says/{text.replace(' ','%20')}?{'&'.join(params)}'
            content_type, content, status, reason = await asyncget(url)

            print(url)

            if status == 404: 
                raise ValueError(f"Cat not found with tags {tags}")
            elif status != 200 or not content_type.startswith("image/"): 
                raise ValueError(f"An unexpected error occurred: {reason}")
            
            ext = content_type.split('/')[1]
            filelike = BytesIO(content)
            filelike.seek(0)

            file = File(filelike, filename=f"cat.{ext}", description=f"Cat says {text}", spoiler=spoiler)
        except ValueError as e:
            await interaction.followup.send(e, ephemeral=True, delete_after=5)
        else:
            await interaction.followup.send(file=file, ephemeral=ephemeral)

def setup(bot : commands.Bot):
    bot.add_cog(RandomCats(bot))