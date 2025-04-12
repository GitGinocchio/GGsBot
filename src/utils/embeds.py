from datetime import datetime, timezone
from nextcord import Embed, Colour
from functools import partial

SUCCESS_ICON_ID = "59850"
ERROR_ICON_ID = "82813"
ALERT_ICON_ID = "12116"

class IconEmbed(Embed):
    def __init__(self, 
        title : str = None,
        description : str = None, 
        author_text : str = None,
        author_url : str = None,
        footer_text : str = None,
        color : Colour = Colour.green(),
        icon_id : str = SUCCESS_ICON_ID,
        icon_color : Colour = Colour.green(),
        url : str = None
    ):
        Embed.__init__(self,
            title=title,
            colour=color,
            description=description,
            timestamp=datetime.now(timezone.utc),
            url=url
        )

        icon_url = f"https://img.icons8.com/?size=100&id={icon_id}&format=png&color={str(icon_color).replace('#', '')}"
        self.set_author(name=author_text,icon_url=icon_url, url=author_url)
        self.set_footer(text=footer_text, icon_url=icon_url)

SuccessEmbed = partial(IconEmbed, icon_id="SUCCESS_ICON_ID", icon_color=Colour.green())
ErrorEmbed = partial(IconEmbed, icon_id="ERROR_ICON_ID", icon_color=Colour.red())
WarningEmbed = partial(IconEmbed, icon_id="WARNING_ICON_ID", icon_color=Colour.yellow())