from cachetools import LRUCache
from nextcord.ext import commands
from nextcord.ext.commands import \
    cooldown
from nextcord import \
    TextChannel,     \
    User,            \
    Guild,           \
    Member,          \
    Message,         \
    Member,          \
    SlashOption,     \
    Interaction,     \
    slash_command    \

class Levels(commands.Cog):
    def __init__(self, bot : commands.Bot) -> None:
        self.bot = bot
        self.messages_cache : dict[Guild,dict[TextChannel, set[Message]]] = LRUCache(maxsize=10)
        self.xp_per_reaction_sent = 30
        self.xp_per_reaction_received = 50
        self.xp_per_message = 20

        """
        cache = {
            {guild} : {
                {channel} : [{message},...],
                ...
            },
            ...
           },
        }
        """
    
    async def calculate_xp(self, message : Message, user : User | Member):
        if message.author.id == user.id: 
            xp = self.xp_per_message
        else: 
            xp = 0

        for reaction in message.reactions:
            async for user_reacted in reaction.users():
                if user_reacted.id == user.id and message.author.id != user.id:
                    xp += self.xp_per_reaction_sent
                
                elif message.author.id == user.id and user_reacted.id != user.id:
                    xp += self.xp_per_reaction_received
        return xp

    @slash_command('level',description='Get user current level',dm_permission=False)
    @cooldown(1,25.0)
    async def level(self,
                interaction : Interaction, 
                user : Member = SlashOption('user','The user whose level you want to know, if not passed, returns your level',required=False,default=None)
            )->None:
        try:
            await interaction.response.defer(ephemeral=True)
            if not user: user = interaction.user

            assert user, "No valid user passed."

            totalxp = 0

            if interaction.guild not in self.messages_cache:
                self.messages_cache[interaction.guild] =  {}

            for channel in interaction.guild.text_channels:
                if channel not in self.messages_cache[interaction.guild]:
                    self.messages_cache[interaction.guild][channel] = set()
                    after = None
                else:
                    totalxp += sum([await self.calculate_xp(message,user) for message in self.messages_cache[interaction.guild][channel].copy()])

                    after: Message | None = sorted(iterable,
                                            key=lambda message: (message.edited_at if message.edited_at else message.created_at),
                                            reverse=True)[0] \
                                            if len(iterable:=self.messages_cache[interaction.guild][channel]) > 0 else None

                async for message in channel.history(limit=None,after=(after.edited_at if after.edited_at else after.created_at) if after else None,oldest_first=True):
                    self.messages_cache[interaction.guild][channel].add(message)
                    totalxp += await self.calculate_xp(message,user)
        except AssertionError as e:
            await interaction.followup.send(e,ephemeral=True)
        else:
            await interaction.followup.send(content=f'{user.mention} is level {totalxp // 1000:.0f} ({totalxp} XP)!')

def setup(bot : commands.Bot):
    bot.add_cog(Levels(bot))