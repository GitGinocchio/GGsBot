import nextcord
from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands
import asyncio,os
import socket
import youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from urllib.parse import urlparse, urlunparse



class SongExtractorAPI:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.ytapi = youtube_dl.YoutubeDL({'format': 'bestaudio','quiet': True})
        self.spotifyapi = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials("7fe554bb7974407cb0349fe30d9e5eec","9ab2f8fcafc74b0cb50fdb91a9ba9869"))

    async def get_song(self,queryurl : str):
        valid,platform = self.isvalid_url(queryurl)
        if valid and platform == 'spotify':
            song = self.from_spotify(queryurl)
            data =  await self.from_query("{0} {1}".format(song['artist'],song['track']))
        elif valid and platform == 'youtube':
            data = await self.from_url(queryurl)
        elif valid and platform == 'other':
            return None
        elif not valid:
            data = await self.from_query(queryurl)

        queue = []
        if 'entries' in data and data is not None:
            for entry in data['entries']:
                if 'url' in entry:
                    song_info = {
                        'url': entry['url'],
                        'title': entry.get('title', ''),
                        'duration': entry.get('duration', 0),
                        'thumbnail': entry.get('thumbnail', ''),
                        'uploader': entry.get('uploader', ''),
                        'uploader_url': entry.get('uploader_url', ''),
                        'webpage_url': entry.get('webpage_url', ''),
                    }
                    queue.append(song_info)
        else:
            song_info = {
                'url': data['formats'][0]['url'],
                'title': data.get('title', ''),
                'duration': data.get('duration', 0),
                'thumbnail': data.get('thumbnail', ''),
                'uploader': data.get('uploader', ''),
                'uploader_url': data.get('uploader_url', ''),
                'webpage_url': data.get('webpage_url', ''),
            }
            queue.append(song_info)
        return queue

    def from_spotify(self, url):
        result = self.spotifyapi.search(q=f"track:{self.spotifyapi.track(url)['name']} artist:{self.spotifyapi.track(url)['artists'][0]['name']}", type='track', limit=1)
        return {'track': result['tracks']['items'][0]['name'] if result is not None else None,'artist' : result['tracks']['items'][0]['artists'][0]['name'] if result is not None else None}

    def isvalid_url(self, url):
        if urlparse(url).scheme and urlparse(url).netloc:
            if urlparse(url).netloc.startswith("open.spotify.com"): return True,'spotify'
            elif urlparse(url).netloc.startswith('youtu.be'): return True,'youtube'
            else: return True,'other'
        else: return False, None

    async def from_url(self, url):
        with self.ytapi as api:
            return await self.loop.run_in_executor(None, lambda: api.extract_info(url, download=False))

    async def from_query(self, query):
        with self.ytapi as api:
            return await self.loop.run_in_executor(None, lambda: api.extract_info(f"ytsearch:{query}", download=False))

class CustomEmbeds:
    def __init__(self):
        self.songembed = None

    def seconds_conversion(self,seconds : int):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return hours, minutes, remaining_seconds

    async def songEmbed(self,ctx,song : dict,sec : int):
        embed = Embed(title='Playing {}'.format(song['title']),color=Color.green(),url=song['webpage_url'])
        embed.set_thumbnail(song['thumbnail'])
        embed.add_field(name='Uploader', value=f"[{song['uploader']}]({song['uploader_url']})",inline=False)
        
        progress = min(sec / int(song['duration']), 1.0)
        progress_bar_length = 25
        completed_length = int(progress * progress_bar_length)
        progress_bar = "[ " + " = " * completed_length + " - " * (progress_bar_length - completed_length) + " ]"
        
        
        currentH,currentM,currentS = self.seconds_conversion(sec)
        songH,songM,songS = self.seconds_conversion(song['duration'])
        embed.add_field(name="Progress Bar", value="**{0}**".format(progress_bar),inline=True)
        embed.add_field(name="Time", value="**{0}:{1}:{2} / {3}:{4}:{5}**".format(currentH,currentM,currentS,songH,songM,songS),inline=True)


        try:
            await self.songembed.edit(embed=embed)
        except:
            self.songembed = await ctx.channel.send(embed=embed)
    
    async def queueEmbed(self,ctx,queue : list):
        pass

"""
    NOTE:
    add replay command.
    add voteskip command.

"""

class Music(commands.Cog):
    def __init__(self,bot):
        super().__init__()
        self.bot = bot
        self.embeds = CustomEmbeds()
        self.extractor = SongExtractorAPI()
        self.stopped = False
        self.history = []
        self.queue = []
    
    async def conditions(self,ctx): #concept
        """
        if user pass all conditions return True else False

        use this method like:
        assert self.conditions(ctx)
        """
        pass

    @commands.command(name='play', help="""
    This command help you adding your tracks to queue and play them instantly using <url> parameter that allows you to send a video or a playlist url from Youtube.
    - If you don't pass a <url> and the queue is not empty will be played the first song in the queue.
    - Call this command only if you are in a voice channel.
    - If you call this command before calling `join` the bot will join your current vocal channel anyway.""")
    async def play(self,ctx,*,query_or_url = None):
        await ctx.message.delete()

        def seconds_conversion(seconds : int):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            remaining_seconds = seconds % 60
            return hours, minutes, remaining_seconds

        async def _play(song : dict,start : int = 0):
            h,m,s = seconds_conversion(start)
            client.stop()
            ffmpeg_options = {'before_options': f"-reconnect 1 -reconnected_streamed 1 -reconnect_delay_max 5 -ss {h}:{m}:{s}", 'options': "-vn"}

            client.play(nextcord.FFmpegPCMAudio(fr"{song['url']}",executable=".\\ffmpeg\\ffmpeg.exe",**ffmpeg_options))
            sec = start

            #message = await ctx.channel.send(embed=embed)
            while client.is_playing():
                sec+=1
                await self.embeds.songEmbed(ctx,song,sec)
                await asyncio.sleep(1)
            
            if sec < int(song['duration']) and not self.stopped:
                self.stopped = False
                await _play(song,sec)
            else:
                if song in self.queue:
                    self.history.append(song)
                    self.queue.remove(song)
                await self.play(ctx)

        try:
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)
            if ctx.message.guild.voice_client is None: await ctx.message.author.voice.channel.connect()
            client = ctx.message.guild.voice_client

            if query_or_url is not None:
                queue = await self.extractor.get_song(query_or_url)
                if queue is not None:
                    self.queue.extend(queue)
                else:
                    raise AssertionError('Could not add this song to the queue, try again or type the title and the artist name instead of a link.')
            if client.is_playing(): return #if is playing another song simply add that new song into the queue
            else:
                for song in self.queue:
                    client.stop()
                    await _play(song)

        except AssertionError as e: await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e: print(e)

    @commands.command(name='skip', help="""
    This command help you skipping tracks in the bot queue list.
    - Call this command only if you are in a voice channel.
    - If you call this command and the queue is empty your songs will be added to the queue but not played.
    - This command has no parameters.""")
    async def skip(self,ctx):
        try:
            assert ctx.message.guild.voice_client is not None, 'The bot is not connected to a voice channel!'
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)

            voice_client = ctx.message.guild.voice_client
            if voice_client.is_playing():
                self.stopped = True
                voice_client.stop()
                if self.queue: self.queue.pop(0)
                await self.play(ctx)

            else:
                raise AssertionError("The bot is not playing anything at the moment.")
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)

    @commands.command(name='add', help="""
    This command help you skipping tracks in the bot queue list.
    - Call this command only if you are in a voice channel.
    - If you call this command and the queue is empty nothing changes.""")
    async def add(self,ctx,query_or_url):
        try:
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)
            assert ctx.message.guild.voice_client is not None, "{} Bot is not connected to a voice channel!".format(ctx.message.author.mention)

            await ctx.message.delete()
            queue = await self.extractor.get_song(query_or_url)
            if queue is not None:
                self.queue.extend(queue)
            else: 
                raise AssertionError('Could not add this song to the queue, try again or type the title and the artist name instead of a link.')
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)

    @commands.command(name='join', help="""
    This command can be used to autorize the bot to join your specific vocal channel.
    - Call this command only if you are in a voice channel.
    - This is the first command you should use to play music in a vocal channel.
    - This command has no parameters""")
    async def join(self,ctx):
        try:
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
        try:
            voice_client = ctx.message.guild.voice_client
            if voice_client.is_playing():
                self.stopped = True
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
        try:
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
        try:
            assert ctx.message.guild.voice_client is not None, 'The bot is not connected to a voice channel!'
            assert ctx.message.guild.voice_client.is_connected(),'The bot is not connected to a voice channel!'

            voice_client = ctx.message.guild.voice_client
            await voice_client.disconnect()
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)

    @commands.command(name='stop', help="""
    Stops the song""")
    async def stop(self,ctx):
        try:
            assert ctx.message.guild.voice_client is not None, 'The bot is not connected to a voice channel!'
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)

            voice_client = ctx.message.guild.voice_client
            if voice_client.is_playing():
                self.stopped = True
                if self.queue: self.queue.pop(0)
                voice_client.stop()
            else: raise AssertionError("The bot is not playing anything at the moment.")
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)



def setup(bot):
    bot.add_cog(Music(bot))


