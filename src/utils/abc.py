from nextcord.ext.commands import Bot
from nextcord import Embed, Interaction, Guild, Colour, ButtonStyle
from nextcord.ui import View, Item, Button, button
from datetime import datetime, timezone
from typing import Callable, Type
import inspect

from .terminal import getlogger

logger = getlogger()

"""
class SetupUI(Embed, View):
    def __init__(self, 
            bot : Bot, 
            guild : Guild, 
            title : str, 
            submit_callback : Callable[[Interaction], None],
            submit_title : str = "Submit",
            timeout : int = 120
        ):
        Embed.__init__(self, title=title)
        View.__init__(self, timeout=timeout)
        self._bot = bot
        self._guild = guild
        self._submit_callback = submit_callback
        self._config = {}

        self.colour = Colour.green()

        self.button = Button(label=submit_title, style=ButtonStyle.primary, row=4)
        self.button.callback = self.__setup
        self.add_item(self.button)
    
    @property
    def bot(self): return self._bot

    @property
    def guild(self): return self._guild

    @property
    def config(self): return self._config

    @config.setter
    def config(self, config : dict): self._config = config

    async def interaction_check(self, interaction: Interaction) -> bool:
        return await super().interaction_check(interaction)

    async def on_error(self, item : Item, interaction : Interaction):
        await interaction.followup.delete_message(interaction.message.id)
        self.stop()

    async def on_timeout(self):
        print('timedout-interaction')

    async def __setup(self, interaction : Interaction):
        try:
            await self._submit_callback(interaction)
        except Exception as e:
            raise e
"""

class BasePage(Embed, View):
    def __init__(self, ui : 'UI', extension : str, timeout : int = 180):
        Embed.__init__(self, timestamp=datetime.now(timezone.utc))
        View.__init__(self, timeout=timeout)
        self.extension = extension
        self.ui = ui

        self.set_author(name=self.ui.bot.user.name, icon_url=self.ui.bot.user.avatar.url)

    @property
    def bot(self): return self.ui.bot
    @property
    def guild(self): return self.ui.guild
    @property
    def config(self): return self.ui.config
    @config.setter
    def config(self, config : dict): self.ui.config = config
    @property
    def pages(self) -> list['Page','SubmitPage']: return self.ui.pages
    @property
    def num_pages(self) -> int: return self.ui.num_pages
    @property
    def num_page(self) -> int: return self.ui.num_page
    @num_page.setter
    def num_page(self, num_page : int): self.ui.num_page = num_page
    @property
    def current_page(self) -> 'BasePage': return self.ui.current_page
    @property
    def submit_page(self) -> 'SubmitPage': return self.ui.submit_page

    async def interaction_check(self, interaction: Interaction) -> bool:
        logger.debug(f"Checking interaction for extension {self.extension} ({self.ui})")
        return await super().interaction_check(interaction)

    async def on_error(self, item : Item, interaction : Interaction):
        await interaction.followup.delete_message(interaction.message.id)
        logger.error(f"An error occurred in extension {self.extension} ({self.ui}) in item {item}")
        self.stop()

    async def on_timeout(self):
        logger.error(f"Extension {self.extension} ({self.ui}) timed out")

class Page(BasePage):
    def __init__(self, ui : 'UI', extension : str, timeout : int = 180):
        BasePage.__init__(self, ui, extension, timeout)

        #self.prev_page = Button(label="Back", style=ButtonStyle.secondary, row=4, disabled=(True if self.num_page == 0 else False))
        #self.prev_page.callback = self.on_prev_page
        #self.add_item(self.prev_page)

        #self.next_page = Button(label="Next", style=ButtonStyle.primary, row=4, disabled=(True if self.num_page == self.num_pages - 1 else False))
        #self.next_page.callback = self.on_next_page
        #self.add_item(self.next_page)

    @button(label="Back", style=ButtonStyle.secondary, row=4)
    async def on_prev_page(self, button: Button, interaction: Interaction):
        if self.num_page <= 0: 
            return
        
        self.num_page -= 1

        back_page = self.current_page

        await interaction.response.edit_message(embed=back_page, view=back_page)

    @button(label="Next", style=ButtonStyle.primary, row=4)
    async def on_next_page(self, button: Button, interaction: Interaction):
        if self.num_page > self.num_pages: 
            return

        self.num_page += 1

        next_page = self.current_page

        await interaction.response.edit_message(embed=next_page, view=next_page)

class SubmitPage(BasePage):
    def __init__(self, 
            ui : 'UI',
            extension : str,
            submit_title : str = "Submit",
            submit_callback : Callable[[Interaction], None] = None,
            timeout : int = 180
        ):
        BasePage.__init__(self, ui, extension, timeout)
        self.submit_title = submit_title
        self._submit_callback = submit_callback

        self.back_button = Button(label="Back", style=ButtonStyle.secondary, row=4, disabled=(True if self.num_pages == 1 else False))
        self.back_button.callback = self.on_back
        self.add_item(self.back_button)

        self.cancel_button = Button(label="Cancel", style=ButtonStyle.danger, row=4)
        self.cancel_button.callback = self.on_cancel
        self.add_item(self.cancel_button)

        self.submit_button = Button(label=submit_title, style=ButtonStyle.success, row=4)
        self.submit_button.callback = self.on_submit
        self.add_item(self.submit_button)

    async def on_back(self, interaction : Interaction):
        if self.num_page <= 0: return
        
        self.num_page -= 1

        back_page = self.current_page

        await interaction.response.edit_message(embed=back_page, view=back_page)
    
    async def on_cancel(self, interaction : Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            await interaction.delete_original_message()
        except Exception as e:
            raise e

    async def on_submit(self, interaction : Interaction):
        try:
            if self._submit_callback:
                await self._submit_callback(interaction)
            else:
                self.stop()
        except Exception as e:
            raise e



class UI(object):
    def __init__(self, 
            bot : Bot,
            guild : Guild, 
            extension : str,
        ):
        self.extension = extension
        self._guild = guild
        self._config = {}
        self._bot = bot
        self._npage = 0
        self._npages = 0

        self._pages : list[Page] = []
        self._submit_page : SubmitPage = None
    
    def init(self):
        if self.num_pages == 0: raise IndexError("No pages")
        for i in range(0,self._npages):
            self._pages[i] = self._pages[i](self, self.extension)

        self._submit_page = self._submit_page(self, self.extension)

    def add_pages(self, *pages : Page):
        for page in pages:
            self._pages.append(page)
            self._npages+=1

    def set_submit_page(self, submit_page : SubmitPage):
        self._submit_page = submit_page

    @property
    def bot(self): return self._bot

    @property
    def guild(self): return self._guild

    @property
    def config(self): return self._config

    @config.setter
    def config(self, config : dict): self._config = config

    @property
    def pages(self) -> list[Page | SubmitPage]: return self._pages + [self._submit_page]

    @property
    def num_pages(self) -> int: return self._npages + 1

    @property
    def num_page(self) -> int: return self._npage

    @num_page.setter
    def num_page(self, num_page : int): self._npage = num_page

    @property
    def current_page(self) -> Page | SubmitPage:
        if self.num_page > self.num_pages: 
            raise IndexError(f"Page {self.num_page} does not exist")
        
        return self.pages[self.num_page]

    @property
    def submit_page(self) -> SubmitPage: return self._submit_page