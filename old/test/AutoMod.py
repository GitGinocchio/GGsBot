from nextcord import utils,Embed,Color,errors
from nextcord.ext import commands,tasks
import os,datetime,json,Levenshtein

class jsonutils:
    def __init__(self,fp: str = None,*,indent: int = 3):
        self.fp = fp
        self.indent = indent

    def content(self):
        with open(self.fp, 'r') as json_file:
            content = json.load(json_file)
            return content

    def save_to_file(self,content,indent: int = 3):
        with open(self.fp, 'w') as json_file:
            json.dump(content,json_file,indent=indent)

def remove_excessive_duplicates(word):
    max_consecutive = 2  # Imposta il numero massimo di caratteri consecutivi da mantenere
    cleaned_word = ""
    consecutive_count = 0

    for char in word:
        if cleaned_word == "" or char != cleaned_word[-1]:
            consecutive_count = 1
            cleaned_word += char
        else:
            consecutive_count += 1
            if consecutive_count <= max_consecutive:
                cleaned_word += char

    return cleaned_word

class Embeds:
    def __init__(self,message):
        self.message = message
        self.BANNED_WORD_TIMEOUT = Embed(
            title="Messaggio rimosso per violazione delle regole:",
            description=f"Messaggio di avvertimento inviato da: **{message.guild.name}**.",
            color=Color.red()
            )
        self.UPPERCASE_LIMIT_TIMEOUT = Embed(
            title="Messaggio rimosso per violazione delle regole:",
            description=f"Messaggio di avvertimento inviato da: **{message.guild.name}**.",
            timestamp=datetime.datetime.now(),
            color=Color.red()
            )
    
    def setup(self):
        pass

class Verification:
    def __init__(self):
        self.datafp = jsonutils('./cogs/data/saved.json')
        self.data = self.datafp.content()
                        #user channel message detected method result
        self.ban_code = "{0}.{1}.{2}.{3}.{4}.{5}"
                               #user channel message lenmessage maxlen
        self.max_lenght_code = "{0}.{1}.{2}.{3}.{4}"

    def levenshteinHardDetect(self,word1 : str,word2 : str):
        distance = Levenshtein.distance(remove_excessive_duplicates(word1), remove_excessive_duplicates(word2),weights=self.data["Automod"]["levenshtein weights"])
        if self.data["Automod"]["levenshtein normalized"]: distance = distance / max(len(word1), len(word2))
        threshold = self.data["Automod"]["threshold of similarity normalized"] if self.data["Automod"]["levenshtein normalized"] else self.data["Automod"]["threshold of similarity"]
        
        if distance < threshold:
            if word1 != word2 and word1 not in self.data["Automod"]['banned']: 
                self.data["Automod"]['banned'].append(word1)
                self.datafp.save_to_file(self.data)
            return (True,distance)
        else:
            return (False,distance)

    def detectbanned(self, message):
        for word in self.data["Automod"]['banned']:
            for message_word in str(message.content.lower()).split():
                result = self.levenshteinHardDetect(message_word,word)
                print(result,message_word,word)


                if word == message_word:
                    ban_code = self.ban_code.format(message.author.name,message.channel.name,message.content.replace('.','< >'),word,0,0)
                    return (True, ban_code.encode().hex())
                if result[0]:
                    ban_code = self.ban_code.format(message.author.name,message.channel.name,message.content.replace('.','< >'),word,1,str(result[1]).replace('.',','))
                    return (True, ban_code.encode().hex())

        return (False,None)
    
    def validatelenght(self,message):
        message_uppercases = sum(1 for char in message.content if char.isupper())

        if message_uppercases > self.data["Automod"]['uppercase limit']:
            ban_code = self.max_lenght_code.format(message.author.name,message.channel.name,message.content,message_uppercases,self.data["Automod"]['uppercase limit'])
            return (True,ban_code.encode().hex())
        else:
            return (False,None)

    def decodetoken(self,hextoken : str):
        token = bytes.fromhex(hextoken).decode('utf-8')
        data = {}

        if token.count('.') == 5:
            raw = token.split('.')
            data = {
                'user' : raw[0],
                'channel' : raw[1],
                'message' : raw[2].replace('< >', '.'),
                'detected' : raw[3],
                'method' : 'word in phrase' if raw[4] == '0' else 'levenshtein',
                'value' : raw[5].replace(',', '.'),
            }
        elif token.count('.') == 4:
            raw = token.split('.')
            data = {
                'user' : raw[0],
                'channel' : raw[1],
                'message' : raw[2],
                'lenmessage' : raw[3],
                'maxlenmessage' : raw[4],
            }

        return data

class AutoMod(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.verify = Verification()
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self,message):
        banned_words_result = self.verify.detectbanned(message)
        lenght_words_result = self.verify.validatelenght(message)
        #print(banned_words_result,lenght_words_result)
        if banned_words_result[1] is not None:
            print(self.verify.decodetoken(banned_words_result[1]))
        if lenght_words_result[1] is not None:
            print(self.verify.decodetoken(lenght_words_result[1]))
"""
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

def setup(bot):
    bot.add_cog(AutoMod(bot))



if __name__ == "__main__":
    os.system("python main.py")