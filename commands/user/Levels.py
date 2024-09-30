from nextcord.ext import commands
from nextcord import \
    Message,         \
    Member,          \
    SlashOption,     \
    Interaction,     \
    slash_command    \

class Levels(commands.Cog):
    def __init__(self, bot : commands.Bot) -> None:
        self.bot = bot
        self.xp_per_reaction_sent = 30
        self.xp_per_reaction_received = 50
        self.xp_per_message = 20

    @slash_command('level',description='Get user current level',dm_permission=False)
    async def level(self,
                interaction : Interaction, 
                user : Member = SlashOption('user','The user whose level you want to know, if not passed, returns your level',required=False,default=None)
            )->None:
        try:
            await interaction.response.defer(ephemeral=True)
            if not user: user = interaction.user

            xp = 0

            for channel in interaction.guild.text_channels:
                async for message in channel.history(limit=None,oldest_first=True):
                    if message.author.id == user.id:
                        xp += self.xp_per_message

                    for reaction in message.reactions:
                        async for user_reacted in reaction.users():
                            if user_reacted.id == user.id and message.author.id != user.id:
                                xp += self.xp_per_reaction_sent
                            
                            elif message.author.id == user.id and user_reacted.id != user.id:
                                xp += self.xp_per_reaction_received
        except AssertionError as e:
            await interaction.followup.send(e,ephemeral=True)
        else:
            await interaction.followup.send(content=f'{user.mention} is level {xp // 1000:.0f} ({xp} XP)!')

def setup(bot : commands.Bot):
    bot.add_cog(Levels(bot))