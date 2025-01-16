from nextcord.ext.commands import Bot
from nextcord import Embed, Interaction, Guild, Colour, ButtonStyle
from nextcord.ui import View, Item, Button, button
from nextcord.types.embed import EmbedType
from datetime import datetime, timezone
from typing import Callable, Type

from .terminal import getlogger

logger = getlogger()

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
        #self.back_button = self.BackButton(self)
        #self.next_button = self.NextButton(self)
        #self.add_item(self.back_button)
        #self.add_item(self.next_button)

    @button(style=ButtonStyle.secondary, label="Back", row=4)
    async def on_back(self, button: Button, interaction: Interaction):
        try:
            if self.num_page <= 0: 
                await interaction.response.send_message("Already at the first page!", ephemeral=True)
                return
        
            self.num_page -= 1

            back_page = self.current_page

            await interaction.response.edit_message(embed=back_page, view=back_page)
        except Exception as e:
            raise e

    @button(style=ButtonStyle.primary, label="Next", row=4)
    async def on_next(self, button: Button, interaction: Interaction):
        try:
            if self.num_page > self.num_pages: 
                await interaction.response.send_message("Already at the last page!", ephemeral=True)
                return

            self.num_page += 1

            next_page = self.current_page

            await interaction.response.edit_message(embed=next_page, view=next_page)
        except Exception as e:
            raise e

    class BackButton(Button):
        def __init__(self, page : 'UiPage'):
            Button.__init__(self, style=ButtonStyle.secondary, label="Back", row=4, disabled=(True if page.num_page == 0 else False))
            self.page = page
        
        async def callback(self, button: Button, interaction: Interaction):
            try:
                if self.page.num_page <= 0: 
                    return
            
                self.page.num_page -= 1

                back_page = self.page.current_page

                await interaction.response.edit_message(embed=back_page, view=back_page)
            except Exception as e:
                raise e

    class NextButton(Button):
        def __init__(self, page : 'UiPage'):
            Button.__init__(self, style=ButtonStyle.primary, label="Next", row=4, disabled=(True if page.num_page == page.num_pages - 1 else False))
            self.page = page
        
        async def callback(self, button: Button, interaction: Interaction):
            try:
                if self.page.num_page > self.page.num_pages: 
                    return

                self.page.num_page += 1

                next_page = self.page.current_page

                await interaction.response.edit_message(embed=next_page, view=next_page)
            except Exception as e:
                raise e

class UiSubmitPage(UiBasePage):
    def __init__(self, ui : 'UI', **kwargs):
        UiBasePage.__init__(self, ui, **kwargs)
        self.submit_title : str = kwargs.get('submit_title', "Submit")

        self.back_button = self.BackButton(self)
        self.cancel_button = self.CancelButton(self)
        self.submit_button = self.SubmitButton(self)

        self.add_item(self.back_button)
        self.add_item(self.cancel_button)
        self.add_item(self.submit_button)

    class BackButton(Button):
        def __init__(self, page : 'UiSubmitPage'):
            Button.__init__(self, style=ButtonStyle.secondary, label="Back", row=4, disabled=(True if page.num_page == page.num_pages - 1 else False))
            self.page = page

        async def callback(self, interaction : Interaction):
            if self.page.num_page <= 0: return
            
            self.page.num_page -= 1

            back_page = self.page.current_page

            await interaction.response.edit_message(embed=back_page, view=back_page)
    
    class CancelButton(Button):
        def __init__(self, page : 'UiSubmitPage'):
            Button.__init__(self, style=ButtonStyle.danger, label="Cancel", row=4)
            self.page = page

        async def callback(self, interaction : Interaction):
            try:
                await interaction.response.defer(ephemeral=True)

                await interaction.delete_original_message()
            except Exception as e:
                raise e

    class SubmitButton(Button):
        def __init__(self, page : 'UiSubmitPage'):
            Button.__init__(self, style=ButtonStyle.success, label=page.submit_title, row=4)
            self.page = page

        async def callback(self, interaction : Interaction):
            try:
                self.stop()
            except Exception as e:
                raise e
            



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