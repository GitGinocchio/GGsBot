from nextcord.ext.commands import Bot
from nextcord import Embed, Interaction, Guild, Colour, ButtonStyle, Emoji, PartialEmoji
from nextcord.ui import View, Item, Button, button
from nextcord.types.embed import EmbedType
from datetime import datetime, timezone
from typing import Callable, Type
from functools import wraps

from .terminal import getlogger

logger = getlogger()

# Pages

class BasePage(Embed, View):
    def __init__(self, **kwargs):
        Embed.__init__(self, 
            colour=kwargs.get("colour", Colour.green()),
            title=kwargs.get("title", None),
            type=kwargs.get("type", "rich"),
            url=kwargs.get("url", None),
            description=kwargs.get("description", None),
            timestamp=datetime.now(timezone.utc)
        )
        View.__init__(self, 
            timeout=kwargs.get("timeout", 180), 
            auto_defer=kwargs.get("auto_defer",True),
            prevent_update=kwargs.get("prevent_update", True)
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        logger.debug(f"Checking interaction for page {self}:\nGuild:{interaction.guild}\nChannel:{interaction.channel}\nExpires in:{interaction.expires_at}")
        return await super().interaction_check(interaction)

    async def on_error(self, item : Item, interaction : Interaction):
        await interaction.followup.delete_message(interaction.message.id)
        logger.error(f"An error occurred in page: {self} in item {item} (type: {item.type})")
        self.stop()

    async def on_timeout(self):
        logger.warning(f"Page: {self} timed out")

class Page(BasePage):
    def __init__(self, colour : Colour = None, title : 'str' = None, type : EmbedType = 'rich', url : str = None, description : str = None, timestamp : datetime = None):
        BasePage.__init__(self,colour=colour,title=title,type=type,url=url,description=description,timestamp=timestamp)

# Buttons

class UiBaseButton(Button):
    def __init__(self, 
        page : 'UiPage', 
        *, 
        style: ButtonStyle = ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | Emoji | PartialEmoji | None = None,
        row: int | None = None,
        callback : Callable[[Interaction], None] | None = None
    ):
        Button.__init__(self, style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        if callback: self.callback = callback
        self.page = page

def on_back_button(func : Callable[['UiBasePage', Interaction], bool | None]):
    @wraps(func)
    async def wrapper(self : 'UiBasePage', interaction: Interaction):
        try:
            result : bool | None = await func(self, interaction)
            
            if (isinstance(result, bool) and not result) or result != None:
                return

            if self.num_page <= 0:
                await interaction.response.send_message("This is the first page!",ephemeral=True)
                return
        
            self.num_page -= 1

            back_page = self.current_page

            await interaction.response.edit_message(embed=back_page, view=back_page)
        except Exception as e:
            raise e

    return wrapper

def on_next_button(func : Callable[['UiBasePage', Interaction], bool | None]):
    @wraps(func)
    async def wrapper(self : 'UiBasePage', interaction: Interaction):
        try:
            result : bool | None = await func(self, interaction)
            
            if (isinstance(result, bool) and not result) or result != None:
                return

            if self.num_page > self.num_pages:
                await interaction.response.send_message("This is the last page!", ephemeral=True)
                return

            self.num_page += 1

            next_page = self.current_page

            await interaction.response.edit_message(embed=next_page, view=next_page)
        except Exception as e:
            raise e

    return wrapper

def on_cancel_button(func : Callable[['UiBasePage', Interaction], bool | None]):
    @wraps(func)
    async def wrapper(self : 'UiBasePage', interaction: Interaction):
        try:
            result : bool | None = await func(self, interaction)
            
            if (isinstance(result, bool) and not result) or result != None:
                return

            await interaction.response.defer(ephemeral=True)

            await interaction.delete_original_message()
        except Exception as e:
            raise e

    return wrapper

def on_submit_button(func : Callable[['UiBasePage', Interaction], bool | None]):
    @wraps(func)
    async def wrapper(self : 'UiBasePage', interaction: Interaction):
        try:
            result : bool | None = await func(self, interaction)
            
            if (isinstance(result, bool) and not result) or result != None:
                return
            
            if not self.is_finished():
                self.stop()
        except Exception as e:
            raise e

    return wrapper

# Ui Pages

class UiBasePage(BasePage):
    def __init__(self, ui : 'UI', **kwargs):
        BasePage.__init__(self, **kwargs)
        self.ui = ui

        self.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)

    @property
    def bot(self): return self.ui.bot
    @property
    def guild(self): return self.ui.guild
    @property
    def config(self): return self.ui.config
    @config.setter
    def config(self, config : dict): self.ui.config = config
    @property
    def pages(self) -> list['UiPage','UiSubmitPage']: return self.ui.pages
    @property
    def num_pages(self) -> int: return self.ui.num_pages
    @property
    def num_page(self) -> int: return self.ui.num_page
    @num_page.setter
    def num_page(self, num_page : int): self.ui.num_page = num_page
    @property
    def current_page(self) -> 'UiBasePage': return self.ui.current_page
    @property
    def submit_page(self) -> 'UiBasePage': return self.ui.submit_page

class UiPage(UiBasePage):
    def __init__(self, ui : 'UI', **kwargs):
        UiBasePage.__init__(self, ui, **kwargs)
        self.add_item(UiBaseButton(
            self, 
            style=ButtonStyle.secondary, 
            label="Back", 
            row=4, 
            callback=self.on_back
        ))
        self.add_item(UiBaseButton(
            self, 
            style=ButtonStyle.danger, 
            label="Cancel", 
            row=4, 
            callback=self.on_cancel
        ))
        self.add_item(UiBaseButton(
            self, 
            style=ButtonStyle.primary, 
            label="Next", 
            row=4, 
            callback=self.on_next
        ))

    @on_back_button
    async def on_back(self, interaction : Interaction):
        """Callback for the back button. This can be overrided."""

    @on_cancel_button
    async def on_cancel(self, interaction : Interaction):
        """Callback for the cancel button. This can be overrided."""

    @on_next_button
    async def on_next(self, interaction : Interaction):
        """Callback for the next button. This can be overrided."""

class UiSubmitPage(UiBasePage):
    def __init__(self, ui : 'UI', **kwargs):
        UiBasePage.__init__(self, ui, **kwargs)
        self.add_item(UiBaseButton(
            self, 
            style=ButtonStyle.secondary, 
            label="Back", 
            row=4, 
            callback=self.on_back
        ))
        self.add_item(UiBaseButton(
            self, 
            style=ButtonStyle.danger, 
            label="Cancel", 
            row=4, 
            callback=self.on_cancel
        ))
        self.add_item(UiBaseButton(
            self, 
            style=ButtonStyle.success, 
            label=kwargs.get('submit_title', "Submit"), 
            row=4, 
            callback=self.on_submit
        ))

    @on_back_button
    async def on_back(self, interaction : Interaction):
        """Callback for the back button. This can be overrided."""

    @on_cancel_button
    async def on_cancel(self, interaction : Interaction):
        """Callback for the cancel button. This can be overrided."""

    @on_submit_button
    async def on_submit(self, interaction : Interaction):
        """Callback for the submit button. This can be overrided."""

# Ui 

class UI(object):
    def __init__(self, 
            bot : Bot,
            guild : Guild
        ):
        self._guild = guild
        self._config = {}
        self._bot = bot
        self._npage = 0
        self._npages = 0

        self._pages : list[tuple[UiPage, dict]] = []
        self._submit_page : tuple[UiSubmitPage, dict] = None
    
    def init_pages(self, **params):
        if self.num_pages == 0: raise IndexError("No pages")
        for i in range(0,self._npages):
            page_params = params
            page_params.update(self._pages[i][1])
            self._pages[i] = self._pages[i][0](self, **page_params)

        submit_page_params = params
        submit_page_params.update(self._submit_page[1])

        
        self._submit_page = self._submit_page[0](self, **params)

    def add_pages(self, *pages : UiPage, **params):
        for page in pages:
            self._pages.append((page, params))
            self._npages+=1

    def set_submit_page(self, submit_page : UiSubmitPage, **params):
        self._submit_page = (submit_page, params)

    @property
    def bot(self): return self._bot

    @property
    def guild(self): return self._guild

    @property
    def config(self): return self._config

    @config.setter
    def config(self, config : dict): self._config = config

    @property
    def pages(self) -> list[UiPage | UiSubmitPage]: return self._pages + [self._submit_page]

    @property
    def num_pages(self) -> int: return self._npages + 1

    @property
    def num_page(self) -> int: return self._npage

    @num_page.setter
    def num_page(self, num_page : int): self._npage = num_page

    @property
    def current_page(self) -> UiPage | UiSubmitPage:
        if self.num_page > self.num_pages: 
            raise IndexError(f"Page {self.num_page} does not exist")
        
        return self.pages[self.num_page]

    @property
    def submit_page(self) -> UiSubmitPage: return self._submit_page