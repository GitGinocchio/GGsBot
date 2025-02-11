from datetime import datetime, timezone
from nextcord import Embed, Colour

SUCCESS_ICON_ID = "59850"

class SuccessEmbed(Embed):
    def __init__(self, 
        title : str = "Success",
        description : str = None, 
        author : str = None,
        author_url : str = None,
        footer_text : str = None,
        color : Colour = Colour.green(),
        url : str = None
    ):
        Embed.__init__(self,
            title=title,
            colour=color,
            description=description,
            timestamp=datetime.now(timezone.utc),
            url=url
        )

        icon_url = f"https://img.icons8.com/?size=100&id={SUCCESS_ICON_ID}&format=png&color={str(color).replace('#', '')}"
        self.set_author(name=author,icon_url=icon_url, url=author_url)
        self.set_footer(text=footer_text, icon_url=icon_url)