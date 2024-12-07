from nextcord.ui import \
    channel_select,     \
    Item,               \
    View

from nextcord import    \
    ChannelType,        \
    Interaction,        \
    VoiceChannel,       \
    Colour,             \
    Embed

from datetime import datetime, timezone

class AddUi(View, Embed):
    def __init__(self):
        View.__init__(self, timeout=120)
        Embed.__init__(self)
        self.color = Colour.green()
        self.description = 'This command allows you to turn a voice channel into a "generator" of temporary voice channels in a specific category'
        self.timestamp = datetime.now(timezone.utc)
        self._config = {'channel' : []}

        self.add_field(
            name="1. Channel",
            value="Select the channel you want to turn into a channel generator",
            inline=False
        )

        self.add_field(
            name='2. Category',
            value="Select the category in which temporary voice channels will be created",
            inline=False
        )

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

    @channel_select(placeholder="1. Channel", channel_types=[ChannelType.voice], min_values=1, max_values=1)
    async def select_channel(self, interaction: Interaction, channel: VoiceChannel):
        self.channel = channel

    @channel_select(placeholder="2. Category", channel_types=[ChannelType.category], min_values=1, max_values=1)
    async def select_channel(self, interaction: Interaction, channel: VoiceChannel):
        self.channel = channel

class DelUi(View, Embed):
    def __init__(self):
        View.__init__(self, timeout=120)
        Embed.__init__(self)
