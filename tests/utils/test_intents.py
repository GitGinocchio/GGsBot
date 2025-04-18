import pytest

from src.utils.intents import getintents
from nextcord import Intents

@pytest.mark.parametrize('flags, expected', [
    (None,                  Intents.default()),
    (0,                     Intents.none()),
    ('guilds',              Intents(guilds=True)),
    (Intents(bans=True),    Intents(bans=True)),
    (['guilds', 'bans'],    Intents(guilds=True, bans=True))
])
def test_getintents(flags, expected):
    assert getintents(flags) == expected