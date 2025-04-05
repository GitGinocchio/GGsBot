from nextcord import Colour
from nextcord.ui import Button
from nextcord import ButtonStyle

from utils.abc import Page

class NowPlayingPage(Page):
    def __init__(self, title : str, popularity : int, duration_str : str, album_name : str, album_url : str, album_img : str, artists : list[dict]):
        Page.__init__(self, timeout=0)
        self.url = album_url
        self.title = f"**{title}**"
        self.colour = Colour.green()
        self.description = f"in `{album_name}`\nby {', '.join("*" + artist['name'] + "*" for artist in artists)}"

        self.add_field(name="Duration", value=f'`{duration_str}`', inline=True)
        self.add_field(name="Popularity", value=f"`{popularity}%`", inline=True)

        self.set_thumbnail(album_img)
        self.set_author(name="Now Playing")

class FinishedPlayingPage(Page):
    def __init__(self, title : str, popularity : int, duration_str : str, album_name : str, album_url : str, album_img : str, artists : list[dict]):
        Page.__init__(self, timeout=0)
        self.url = album_url
        self.title = f"**{title}**"
        self.colour = Colour.green()
        self.description = f"in `{album_name}`\nby {', '.join("*" + artist['name'] + "*" for artist in artists)}"

        self.add_field(name="Duration", value=f'`{duration_str}`', inline=True)
        self.add_field(name="Popularity", value=f"`{popularity}%`", inline=True)

        self.set_thumbnail(album_img)
        self.set_author(name="Song Finished")

class NothingToPlayPage(Page):
    def __init__(self):
        Page.__init__(self, timeout=0)
        self.description = "There is nothing in the queue to play."
        self.color = Colour.red()
