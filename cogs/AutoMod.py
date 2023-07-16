from nextcord import utils,Embed,Color,errors
from nextcord.ext import commands,tasks
import os,datetime



class AutoMod(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.BANNED_WORDS = ['nigga','negro','gay','nero']
        self.UPPERCASE_LIMIT = 25
        self.warnings = []
        self.bans = []

    @commands.Cog.listener()
    async def on_message(self,message):
        try:
            #print(message.content.lower())
            for word in self.BANNED_WORDS:
                if word in message.content.lower():
                    await message.delete()
                    # Invia un messaggio privato all'autore con i dettagli
                    embed = Embed(
                        title="Messaggio rimosso per violazione delle regole:",
                        description=f"Messaggio di avvertimento inviato da: **{message.guild.name}**.",
                        color=Color.red()
                    )
                    embed.add_field(name="Reason:",value="Se ottieni questo avvertimento significa che hai utilizzato delle parole che non dovrebbero essere utilizzate nel server.")
                    embed.add_field(name="Canale testuale:", value=f'{message.channel.mention}', inline=False)
                    embed.add_field(name="Messaggio incriminato:", value=f'{message.author.mention} : `"{message.content}"`', inline=False)
                    embed.add_field(name="Penalita:", value=f'** - Otterai un timeout di 2 minuti**', inline=False)
                    embed.set_footer(text="Si prega di rispettare le regole del server.")
                
                    await message.author.send(embed=embed)
                    await message.channel.send(f"{message.author.mention} ha ottenuto un timeout per aver violato le regole del server.")
                    await message.author.edit(timeout=utils.utcnow()+datetime.timedelta(seconds=120))
        
        except errors.Forbidden as e:
            await message.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except AssertionError as e:
            await message.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            await message.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)


    """
    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            message_uppercases = sum(1 for char in message.content if char.isupper())
            
            if message_uppercases > self.UPPERCASE_LIMIT:
                await message.delete()
                # Invia un messaggio privato all'autore con i dettagli
                embed = Embed(
                    title="Messaggio rimosso per violazione delle regole:",
                    description=f"Messaggio di avvertimento inviato da: **{message.guild.name}**.",
                    color=Color.red()
                )
                embed.add_field(name="Reason:",value="Se ottieni questo avvertimento significa che hai superato il numero massimo di caratteri maiuscoli all'interno di un messaggio.")
                embed.add_field(name="Canale testuale:", value=f'{message.channel.mention}', inline=False)
                embed.add_field(name="Messaggio incriminato:", value=f'{message.author.mention} : `"{message.content}"`', inline=False)
                embed.add_field(name="Penalita:", value=f'** - Otterai un timeout di 2 minuti**', inline=False)
                embed.set_footer(text="Si prega di rispettare le regole del server.")
                
                await message.author.send(embed=embed)
                await message.channel.send(f"{message.author.mention} ha ottenuto un timeout per aver violato le regole del server.")
                await message.author.edit(timeout=utils.utcnow()+datetime.timedelta(seconds=120))
        
        except errors.Forbidden as e:
            await message.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except AssertionError as e:
            await message.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            await message.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
    """

    @tasks.loop(hours=24,reconnect=True)
    async def delete_warnings(self):
        self.warnings.clear()





def setup(bot):
    bot.add_cog(AutoMod(bot))



if __name__ == "__main__":
    os.system("python main.py")