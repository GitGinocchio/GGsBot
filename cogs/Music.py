import nextcord
from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands
import asyncio,os
import youtube_dl
from pathlib import Path
from urllib.parse import urlparse
current_path = Path(__file__).absolute().parent


youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_options = {
    'format': 'bestaudio',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # bind to ipv4 since ipv6 addresses cause issues sometimes
    'outtmpl': '.\cogs\music_temp\%(title)s.%(ext)s'
}
ffmpeg_options = {'before_options' : '-reconnect 1 -reconnect_streamed 1 - reconnect_delay_max 5','options': '-vn'}
ytdl = youtube_dl.YoutubeDL(ytdl_options)

class YTDLSource(nextcord.PCMVolumeTransformer):
    def __init__(self, source):
        super().__init__(source)

    @classmethod
    async def from_url(self,url, *, loop=None):
        loop = loop if loop is not None else asyncio.get_event_loop()

        if bool(urlparse(url).scheme):
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
        else:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{url} video_type:music lyrics category:10", download=True))
        
        #ADD SUPPORT OF SPOTIFY API'S.
        """
        Se desideri supportare anche i link di Spotify nel tuo codice, puoi utilizzare la libreria spotipy per ottenere informazioni sulle tracce o le playlist di Spotify utilizzando gli URL di Spotify. Ecco un esempio di come puoi ottenere il nome e l'artista di una traccia utilizzando un link di Spotify:

        python
        Copy code
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials

        # Crea un'istanza di Spotipy utilizzando le tue credenziali
        client_credentials_manager = SpotifyClientCredentials(client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET')
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        def get_track_info_from_spotify_url(url):
            # Ottieni l'ID della traccia dal link di Spotify
            track_id = url.split('/')[-1].split('?')[0]

            # Ottieni le informazioni sulla traccia utilizzando l'ID
            track_info = sp.track(track_id)

            # Estrai il nome e l'artista della traccia
            track_name = track_info['name']
            artist_name = track_info['artists'][0]['name']

            return track_name, artist_name

        # Esempio di utilizzo con un link di Spotify
        spotify_url = 'https://open.spotify.com/track/0vqkz1lSP3iKp5Z4aQhTtU?si=abc123'
        track_name, artist_name = get_track_info_from_spotify_url(spotify_url)
        print('Track:', track_name)
        print('Artist:', artist_name)
        Nell'esempio sopra, la funzione get_track_info_from_spotify_url() accetta un link di Spotify come input e restituisce il nome della traccia e l'artista associati. Viene utilizzata la libreria spotipy per interagire con l'API di Spotify e ottenere le informazioni sulla traccia.

        Assicurati di aver installato la libreria spotipy eseguendo pip install spotipy. Inoltre, dovrai ottenere le tue credenziali client da Spotify per utilizzarle nel tuo codice. Puoi registrarle su https://developer.spotify.com/dashboard/.

        Ricorda che le operazioni che puoi eseguire con i link di Spotify dipenderanno dalla disponibilità di dati e funzionalità forniti dall'API di Spotify.
        """

        if 'entries' in data: data = data['entries'][0]
        filename = ytdl.prepare_filename(data)
        return filename,data

class Music(commands.Cog):
    def __init__(self,bot):
        super().__init__()
        self.bot = bot
        self.current_track_path = ''
        self.queue = []

    @commands.command(name='play', help="""
    This command help you adding your tracks to queue and play them using <url> parameter that allows you to send a video url from Youtube.
    - Call this command only if you are in a voice channel.
    - If you call this command before calling `join` the bot will join your current vocal channel anyway.""")
    async def play(self,ctx,url):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True),Permissions(manage_messages=True)] #Permissions(administrator=True),Permissions(manage_messages=True)


        try:
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)
            if ctx.message.guild.voice_client is None:
                voice_channel = ctx.message.author.voice.channel
                await voice_channel.connect()

            await ctx.message.delete()
            voice_channel = ctx.message.guild.voice_client
            assert url is not None, 'url is a required argument that is missing.'

            async with ctx.typing():
                filename,data = await YTDLSource.from_url(url, loop=self.bot.loop)

                embed = Embed(
                    title='Playing: {}!'.format(data['title']),
                    color=Color.green(),
                    url=data['webpage_url'])

                embed.set_image(url=data['thumbnail'])
                embed.add_field(name='Duration', value=f"{data['duration']} secondi",inline=True)
                embed.add_field(name='Uploader', value=f"[{data['uploader']}]({data['uploader_url']})",inline=True)
                playing_message = await ctx.channel.send(embed=embed)

                #source = await nextcord.FFmpegOpusAudio.from_probe(data['formats'][0]['url'],**ffmpeg_options)
                #voice_channel.play(nextcord.PCMVolumeTransformer(source,1))
                voice_channel.play(nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(executable=".\\ffmpeg\\ffmpeg.exe", source=filename,**ffmpeg_options),volume=0.7))
                #voice_channel.play(nextcord.FFmpegPCMAudio(executable=".\\ffmpeg\\ffmpeg.exe", source=filename, options='-vn')) #options='-vn'
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        else:
            embed = Embed(title='{} Finished!'.format(data['title']),color=Color.green(),url=data['webpage_url'])
            embed.set_thumbnail(data['thumbnail'])
            embed.add_field(name='Uploader', value=f"[{data['uploader']}]({data['uploader_url']})",inline=True)
            await asyncio.sleep(int(data['duration']))
            await playing_message.delete()
            await ctx.channel.send(embed=embed)
        finally:
            os.remove(filename)

    @commands.command(name='join', help="""
    This command can be used to autorize the bot to join your specific vocal channel.
    - Call this command only if you are in a voice channel.
    - This is the first command you should use to play music in a vocal channel.
    - This command has no parameters""")
    async def join(self,ctx):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True),Permissions(manage_messages=True)] #Permissions(administrator=True),Permissions(manage_messages=True)

        try:
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            
            await ctx.message.delete()

            if not ctx.message.author.voice:
                raise AssertionError("{} You are not connected to a voice channel!".format(ctx.message.author.mention))
            elif ctx.guild.voice_client is not None:
                raise AssertionError("I am currently in a voice channel!")
            else:
                voice_channel = ctx.message.author.voice.channel
                await voice_channel.connect()
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)

    @commands.command(name='pause', help="""
    This command pauses the current song playing session.
    - Make sure that the bot and you are in a vocal channel to use this command.
    - This command has no parameters, this command only works while the bot rest in a voice channel and.""")
    async def pause(self,ctx):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True),Permissions(manage_messages=True)] #Permissions(administrator=True),Permissions(manage_messages=True)

        try:
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            assert ctx.message.guild.voice_client is not None, 'The bot is not connected to a voice channel!'
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)

            voice_client = ctx.message.guild.voice_client
            if voice_client.is_playing():
                voice_client.pause()
            else:
                raise AssertionError("The bot is not playing anything at the moment.")
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)

    @commands.command(name='resume', help="""
    This command resumes the current song playing session.
    - Make sure that the bot and you are in a vocal channel to use this command.
    - This command has no parameters, this command only works while the bot rest in a voice channel.""")
    async def resume(self,ctx):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True),Permissions(manage_messages=True)] #Permissions(administrator=True),Permissions(manage_messages=True)

        try:
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            assert ctx.message.guild.voice_client is not None, 'The bot is not connected to a voice channel!'
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)

            voice_client = ctx.message.guild.voice_client
            if voice_client.is_paused():
                voice_client.resume()
            else:
                raise AssertionError("The bot was not playing anything before this. Use `play` command")
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)

    @commands.command(name='leave', help="""
    To make the bot leave the voice channel""")
    async def leave(self,ctx):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True),Permissions(manage_messages=True)] #Permissions(administrator=True),Permissions(manage_messages=True)

        try:
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            assert ctx.message.guild.voice_client is not None, 'The bot is not connected to a voice channel!'
            assert ctx.message.guild.voice_client.is_connected(),'The bot is not connected to a voice channel!'

            voice_client = ctx.message.guild.voice_client
            await voice_client.disconnect()
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)

    @commands.command(name='stop', help="""Stops the song""")
    async def stop(self,ctx):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True),Permissions(manage_messages=True)] #Permissions(administrator=True),Permissions(manage_messages=True)

        try:
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            assert ctx.message.guild.voice_client is not None, 'The bot is not connected to a voice channel!'
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)

            voice_client = ctx.message.guild.voice_client
            if voice_client.is_playing():
                voice_client.stop()
            else:
                raise AssertionError("The bot is not playing anything at the moment.")
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)

def setup(bot):
    bot.add_cog(Music(bot))

if __name__ == "__main__": os.system("python main.py")