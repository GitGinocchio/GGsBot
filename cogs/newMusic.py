import nextcord
from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands
import threading
import asyncio,os
import youtube_dl
from pathlib import Path
from urllib.parse import urlparse
current_path = Path(__file__).absolute().parent

class YTapi:
    def __init__(self):
        super().__init__()
        self.ytdl_options = {'format': 'bestaudio','quiet': True}
        self.queue = []

    async def from_url_with_ffmpeg(self, url):
        async def get_song_info(url):
            loop = asyncio.get_event_loop()
            with youtube_dl.YoutubeDL(self.ytdl_options) as ydl:
                if bool(urlparse(url).scheme):
                    return await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                else:
                    return await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch:{url} video_type:music lyrics category:10", download=False))

        
        try:
            info = await get_song_info(url)

            if 'entries' in info:
                # È una playlist, ottieni i link di tutte le tracce
                for entry in info['entries']:
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
                        self.queue.append(song_info)
            else:
                # Non è una playlist, restituisci solo il link della canzone
                if info is not None:
                    song_info = {
                        'url': info['formats'][0]['url'],
                        'title': info.get('title', ''),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'uploader': info.get('uploader', ''),
                        'uploader_url': info.get('uploader_url', ''),
                        'webpage_url': info.get('webpage_url', ''),
                    }
                    self.queue.append(song_info)
        except Exception as e: 
            print(e)
        return self.queue

    def from_search_with_ffmpeg(self,search, queue):
        pass

    def from_url(self, url):
        pass

    def from_queue(self, queue):
        pass

class Spotifyapi:
    pass




class newMusic(commands.Cog):
    def __init__(self,bot):
        super().__init__()
        self.bot = bot
        self.queue = []
        self.stopped = False
        self.ytAPI = YTapi()
    
    @commands.command(name='play', help="""
    This command help you adding your tracks to queue and play them instantly using <url> parameter that allows you to send a video or a playlist url from Youtube.
    - If you don't pass a <url> and the queue is not empty will be played the first song in the queue.
    - Call this command only if you are in a voice channel.
    - If you call this command before calling `join` the bot will join your current vocal channel anyway.""")
    async def play(self,ctx,url = None):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True)] #Permissions(administrator=True),Permissions(manage_messages=True)

        try:
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)

            await ctx.message.delete()
            if ctx.message.guild.voice_client is None:
                voice_channel = ctx.message.author.voice.channel
                await voice_channel.connect()
            voice_client = ctx.message.guild.voice_client

            if url is not None: 
                queue = await self.ytAPI.from_url_with_ffmpeg(url)
                if queue is not None:
                    self.queue.extend(queue)
                else: 
                    pass
                    #error song not added to queue
            
            
            if voice_client.is_playing(): return #if is playing another song simply add that new song into the queue
            async def play_song(song : dict,start_at : int = 0):
                try:
                    def seconds_to_hms(seconds):
                        hours = seconds // 3600
                        minutes = (seconds % 3600) // 60
                        remaining_seconds = seconds % 60
                        return hours, minutes, remaining_seconds
                    h,m,s = seconds_to_hms(start_at)
                    voice_client.play(nextcord.FFmpegPCMAudio(song['url'],executable=".\\ffmpeg\\ffmpeg.exe",options=f"-reconnect 1 -ss {h}:{m}:{s}"))
                    sec = start_at
                    
                    while voice_client.is_playing():
                        sec+=1
                        await asyncio.sleep(1)
                    
                    if sec < int(song['duration']) and not self.stopped:
                        self.stopped = False
                        print('stopped unexpectedly at seconds: {}'.format(sec))
                        print('restarting at seconds: {}'.format(sec))
                        await play_song(song,sec)
                    else:
                        sec = 0
                        print('song finished successfully!')
                        if song in self.queue: self.queue.remove(song)
                        print(self.queue)
                except Exception as e:
                    print(e)


            for song in self.queue:
                try:
                    embed = Embed(
                        title='Playing: {}!'.format(song['title']),
                        color=Color.green(),
                        url=song['webpage_url'])

                    embed.set_image(url=song['thumbnail'])
                    embed.add_field(name='Duration', value=f"{song['duration']} secondi",inline=True)
                    embed.add_field(name='Uploader', value=f"[{song['uploader']}]({song['uploader_url']})",inline=True)
                    playing_message = await ctx.channel.send(embed=embed)

                    #print('playing ',song['title'])
                    voice_client.stop()
                    await play_song(song)
                except Exception as e:
                    print(f"Error sending message:{e}")
                else:
                    embed = Embed(title='{} Finished!'.format(song['title']),color=Color.green(),url=song['webpage_url'])
                    embed.set_thumbnail(song['thumbnail'])
                    embed.add_field(name='Uploader', value=f"[{song['uploader']}]({song['uploader_url']})",inline=True)
                    await asyncio.sleep(int(song['duration']))
                    if playing_message is not None: await playing_message.delete()
                    await ctx.channel.send(embed=embed)
        
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)

    @commands.command(name='skip', help="""
    This command help you skipping tracks in the bot queue list.
    - Call this command only if you are in a voice channel.
    - If you call this command and the queue is empty your songs will be added to the queue but not played.
    - This command has no parameters.""")
    async def skip(self,ctx):
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
    async def add(self,ctx,url):
        command_roles = [(1122918623120457849,'mod')]
        command_permissions = [Permissions(administrator=True)] #Permissions(administrator=True),Permissions(manage_messages=True)

        try:
            assert any(ctx.channel.permissions_for(ctx.author).value & permission.value == permission.value for permission in command_permissions) or any(role in command_roles for role in [(role.id,role.name) for role in ctx.author.roles]), f"""
                You do not have the following permissions or roles to use this command.
                - Roles: {command_roles}\n
                - Command permissions: {command_permissions}
                
                """
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)
            assert ctx.message.guild.voice_client is not None, "{} Bot is not connected to a voice channel!".format(ctx.message.author.mention)

            await ctx.message.delete()
            queue = await self.ytAPI.from_url_with_ffmpeg(url)
            if queue is not None:
                self.queue.extend(queue)
            else: 
                pass
                #error song not added to queue
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

    @commands.command(name='stop', help="""
    Stops the song""")
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
                self.stopped = True
                if self.queue: self.queue.pop(0)
                voice_client.stop()
            else: raise AssertionError("The bot is not playing anything at the moment.")
        except AssertionError as e:
            await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)
        except Exception as e:
            print(e)








def setup(bot):
    bot.add_cog(newMusic(bot))

if __name__ == "__main__": os.system("python main.py")