import nextcord
from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands,tasks
import random,asyncio,os
from jsonutils import jsonfile


class New_custom_voice_channels(commands.Cog):
    def __init__(self,bot):
        self.content = jsonfile('cogs/data/saved.json')
        self.bot = bot
        self.custom_channels = []

    """
    Evento di entrata o di uscita di un utente da un canale vocale x.

    1. Controllare se e' presente un utente nel canale di setup dei canali vocali custom.
    2. Renderizzarte l'utente in un canale appena creato.
    3. Salvare le info del canale, come id dell'utente che lo ha creato, id del canale (trovare il modo per salvare i dati della chat del canale.).
    4. Rinominare il canale con il nome dell'utente
    5. Dare i poteri per quel canale all'utente.

    """
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:

            if after.channel is not None:
                if after.channel.id == self.content["Custom Channels"]["setup_channel_id"]:
                    vocal_channel = await after.channel.category.create_voice_channel(f'{str(member.name).capitalize()}\'s Vocal Channel')
                    await member.move_to(vocal_channel)
                    self.custom_channels.append(vocal_channel)
                    #self.content["Custom Channels"]["custom_channels"].append(vocal_channel)
                    

                    overwrites = {
                        member: nextcord.PermissionOverwrite(
                            connect=True,
                            speak=True,
                            manage_channels=True,
                            # Altri permessi desiderati
                        )
                    }
                    await vocal_channel.edit(overwrites=overwrites)
                    _ = asyncio.create_task(self.delete_channel(vocal_channel))

                if before.channel is not None:
                    if before.channel.id != after.channel.id:
                        if before.channel in self.custom_channels or before.channel in self.content["Custom Channels"]["custom_channels"]:
                            _ = asyncio.create_task(self.delete_channel(before.channel))
            else:
                if before.channel in self.custom_channels or before.channel in self.content["Custom Channels"]["custom_channels"]:
                    _ = asyncio.create_task(self.delete_channel(before.channel))

        except AssertionError as e:
            pass
        except Exception as e:
            print(e)

    async def delete_channel(self,channel):
        try:
            await asyncio.sleep(self.content["Custom Channels"]['timeout'])

            if len(channel.members) == 0 and (channel in self.custom_channels or channel in self.content["Custom Channels"]["custom_channels"]):
                #self.content["Custom Channels"]["custom_channels"].remove(channel)
                self.custom_channels.remove(channel)
                await channel.delete()
        except AssertionError as e:
            pass
        except Exception as e:
            print('delete_channel error:',e)

def setup(bot):
    bot.add_cog(New_custom_voice_channels(bot))

if __name__ == "__main__":
    pass
