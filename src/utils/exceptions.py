from datetime import datetime, timezone
from nextcord import Embed, Colour

from utils.config import exceptions

class GGsBotException(Exception):
    def __init__(self, code : int | str = None, *args):
        """Base class for GGsBot exceptions."""
        Exception.__init__(self, *args)
        self.type = self.__class__.__name__
        self.code = str(code)
        self.data : dict

        if self.type in exceptions and self.code in exceptions[self.type]:
            self.data = exceptions[self.type][self.code]
        else:
            raise ValueError(f"Invalid exception type {self.type} or code {self.code}")
    
    def __str__(self): return f"{self.data['title']} ({self.code}): {self.data['description']}"

    def asEmbed(self) -> Embed:
        embed = Embed(
            title=self.data['title'],
            colour=Colour.red(),
            description=self.data['description'],
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Suggestions",value=self.data['suggestions'],inline=True)
        embed.add_field(name="Error code: ", value=self.code, inline=False)
        embed.set_author(name=self.type,icon_url="https://img.icons8.com/?size=100&id=82813&format=png&color=e74c3c")
        embed.set_footer(text=f'contact a moderator for more help')

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
    def __init__(self, code : int | str = None, *args) -> None:
        """Set of errors related to GGsBot slash commands"""
        GGsBotException.__init__(self, code, *args)

# Creare altri tipi di Exceptions che possono prendere anche piu' parametri
# E i parametri possono essere utili per rendere piu' dinamiche le Exceptions
# Per esempio "Devi prima inizializzare l'estensione {extension} prima!"