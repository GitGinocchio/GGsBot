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
from nextcord.ui import View, Button
from enum import StrEnum
from io import BytesIO
import re

from utils.commons import safe_asyncget, asyncget

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
            self.tags : list = await asyncget(f'{self.baseurl}/api/tags')

    @slash_command(name="cats", description="Set of commands to get cat images")
    async def cats(self, interaction : Interaction): pass

    @cats.subcommand(name="tags",description="Get all available tags")
    async def get_tags(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            assert self.tags is not None, "Tags are not loaded at the moment"


            embed = Embed(
                title="Available Tags",
                description="You can see the available tags below",
                color=Color.green()
            )
            
            view =  View(timeout=3)
            link = Button(style=ButtonStyle.url, label="All available tags", url=f"{self.baseurl}/api/tags")
            view.add_item(link)

        except AssertionError as e:
            await interaction.followup.send(e, ephemeral=True, delete_after=5)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @cats.subcommand(name="randomcat",description="Get a random cat image")
    @commands.cooldown(1, 60, commands.BucketType.user)
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

            tags_pattern = r"^\S+(?:,\S+)*$" # comma separated list of strings regex
            assert re.match(tags_pattern, tags), "Tags must be a comma separated list of strings"
            for tag in tags.split(','): assert tag in self.tags, f"Tag \'{tag}\' is not an available tag"

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

            url = f'{self.baseurl}/cat/{tags}/says/{text.replace(' ','%20')}?{'&'.join(params)}'

            print(url)

            content_type, content, status, reason = await safe_asyncget(url)

            assert status != 404, f"Cat not found with tags {tags} "
            assert status == 200 and content_type.startswith("image/"), f"An unexpected error occurred: {reason}"
            
            ext = content_type.split('/')[1]
            filelike = BytesIO(content)
            filelike.seek(0)

            file = File(filelike, filename=f"cat.{ext}", description=f"Cat says {text}", spoiler=spoiler)
        except AssertionError as e:
            await interaction.followup.send(e, ephemeral=True, delete_after=5)
        else:
            await interaction.followup.send(file=file, ephemeral=ephemeral)

def setup(bot : commands.Bot):
    bot.add_cog(RandomCats(bot))