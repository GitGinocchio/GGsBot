from nextcord.ext.commands import Bot
from nextcord import Embed, Interaction, Guild, Colour, ButtonStyle
from nextcord.ui import View, Item, Button, button
from datetime import datetime, timezone
from typing import Callable
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

    @button(label="Back", style=ButtonStyle.secondary, row=4)
    async def prev_page(self, button: Button, interaction: Interaction):
        if self.ui.current_page <= 0: return
        
        self.ui.current_page -= 1

        back_page = self.ui.pages[self.ui.current_page]

        await interaction.response.edit_message(embed=back_page, view=back_page)

    @button(label="Next", style=ButtonStyle.primary, row=4)
    async def next_page(self, button: Button, interaction: Interaction):
        if self.ui.current_page >= len(self.ui.pages): return

        self.ui.current_page += 1

        next_page = self.ui.pages[self.ui.current_page]

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

        self.button = Button(label=submit_title, style=ButtonStyle.success, row=4)
        self.button.callback = self.submit
        self.add_item(self.button)

    async def submit(self, interaction : Interaction):
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
        self.current_page = 0
        self._config = {}
        self._guild = guild
        self._bot = bot

        self.pages : list[Page | SubmitPage] = [cls(self, extension) for _, cls in inspect.getmembers(self, lambda x: inspect.isclass(x) and issubclass(x, Page))]

        submit_pages = inspect.getmembers(self, lambda x: inspect.isclass(x) and issubclass(x, SubmitPage))
        if (len_submit_pages:=len(submit_pages)) == 1:
            self.pages.append(submit_pages[0][1](self, extension))
        elif len_submit_pages > 1:
            raise ValueError("There should be only one SubmitPage class in the UI")
        else:
            self.pages.append(SubmitPage(self, extension))

    @property
    def bot(self): return self._bot

    @property
    def guild(self): return self._guild

    @property
    def config(self): return self._config

    @config.setter
    def config(self, config : dict): self._config = config

    def get_current_page(self) -> Page:
        return self.pages[self.current_page]
    
    def get_submit_page(self) -> SubmitPage: 
        return self.pages[-1]
