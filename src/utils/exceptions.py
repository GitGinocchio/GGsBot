from datetime import datetime, timezone
from nextcord import Embed, Colour

from utils.embeds import IconEmbed, ERROR_ICON_ID
from utils.config import exceptions
from utils.commons import hex_to_colour

class GGsBotException(Exception):
    def __init__(self, 
        code : int | str | None = None, 
        title : str | None = None,
        description : str | None = None,
        suggestions : str | None = None,
        icon_id : int | None = None,
        color : Colour | str | None = None,
        *args,
        **kwargs
    ):
        """Base class for GGsBot exceptions."""
        Exception.__init__(self, *args)
        self.type = self.__class__.__name__
        self.code = code
        self.kwargs = kwargs
        self.args = args

        if self.type != 'GGsBotException' and (not self.type in exceptions or self.code not in exceptions[self.type]):
            raise ValueError(f"Invalid exception type {self.type} or code {self.code}")

        data : dict = exceptions.get(self.type, {}).get(str(self.code), {})


        self.title = title if title is not None else data.get('title', 'GGsBotError')
        self.description = description if description is not None else data.get('description', 'GGsBotError')
        self.suggestions = suggestions if suggestions is not None else data.get('suggestions', 'No Suggestions')
        self.icon_id = icon_id if icon_id is not None else data.get('icon_id', ERROR_ICON_ID)
        self.color = (color if type(color) is Colour else hex_to_colour(color)) if color is not None else \
                     hex_to_colour(data.get('color', "0xe74c3c"))
    
    def __str__(self): return f"{self.title} (code: {self.code}): {self.description}"

    def __repr__(self): return f'{self.type}(code:{self.code})'

    @staticmethod
    def formatException(e : Exception) -> 'GGsBotException':
        if isinstance(e, GGsBotException): return e
        return GGsBotException(title=e.__class__.__name__,description=str(e), *e.args)

    def asEmbed(self) -> Embed:
        embed = IconEmbed(
            title=self.title,
            footer_text=f'contact a moderator for more help',
            author_text=self.type,
            description=self.description.format(self.args, self.kwargs),
            icon_id=self.icon_id,
            icon_color=self.color,
            color=self.color
        )

        embed.add_field(name="Suggestions",value=self.suggestions.format(self.args, self.kwargs),inline=True)
        if self.code is not None: embed.add_field(name="Error code: ", value=str(self.code), inline=False)

        return embed

class CloudFlareAIException(GGsBotException):
    def __init__(self, code : int | str = None, *args) -> None:
        """Set of errors that are raised by the cloudflare AI."""
        GGsBotException.__init__(self, code, *args)

class DatabaseException(GGsBotException):
    def __init__(self, code : int | str = None, *args) -> None:
        """Set of errors that are raised by the database."""
        GGsBotException.__init__(self, code, *args)

class ExtensionException(GGsBotException):
    def __init__(self, code : int | str = None, *args) -> None:
        """Set of errors related to GGsBot extensions"""
        GGsBotException.__init__(self, code, *args)

class SlashCommandException(GGsBotException):
    def __init__(self, code : int | str = None, *args, **kwargs) -> None:
        """Set of errors related to GGsBot slash commands"""
        GGsBotException.__init__(self, code, *args, **kwargs)

# Creare altri tipi di Exceptions che possono prendere anche piu' parametri
# E i parametri possono essere utili per rendere piu' dinamiche le Exceptions
# Per esempio "Devi prima inizializzare l'estensione {extension} prima!"