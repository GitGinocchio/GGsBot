from nextcord.ext.commands import Bot
from nextcord import Embed, Interaction, Guild, Colour, ButtonStyle
from nextcord.ui import View, Item, Button
from typing import Callable
import inspect


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
        
class GGsBotPage:#(Embed, View):
    def __init__(self, ui : 'GGsBotUI'):
        #Embed.__init__(self)
        #View.__init__(self)
        self.ui = ui



class GGsBotUI:
    def __init__(self):
        self.pages = [cls(self) for _, cls in inspect.getmembers(MyUI, lambda x: inspect.isclass(x) and issubclass(x, GGsBotPage))]
        print(self.pages)

    @property
    def bot(self): return self._bot

    @property
    def guild(self): return self._guild

    @property
    def config(self): return self._config

    @config.setter
    def config(self, config : dict): self._config = config



class MyUI(GGsBotUI):
    def __init__(self):
        GGsBotUI.__init__(self)

    class MyFirstPage(GGsBotPage):
        def __init__(self, ui : GGsBotUI):
            GGsBotPage.__init__(self, ui)

    class MySecondPage(GGsBotPage):
        def __init__(self, ui : GGsBotUI):
            GGsBotPage.__init__(self, ui)

MyUI()