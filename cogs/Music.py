import nextcord
from nextcord import Embed,Color,utils,channel,Permissions,Interaction,slash_command
from nextcord.ext import commands
from pytube import YouTube
import asyncio
import io,os
from urllib.parse import urlparse
import soundfile as sf

"""
import io
import requests

response = requests.get(song['url']) 
filelike = io.BytesIO()             #filelike non e' un file su disco rigido ma su ram (+ velocita' di lettura e scrittura)
filelike.write(response.content)
client.play(nextcord.FFmpegPCMAudio(filelike,executable=".\\ffmpeg\\ffmpeg.exe",**ffmpeg_options))

"""

class CustomEmbeds:
    def __init__(self):
        self.songembed = None

    def seconds_conversion(self,seconds : int):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return hours, minutes, remaining_seconds

    async def songEmbed(self,ctx,song : dict,sec : int):
        try:
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

            if self.songembed is None:
                self.songembed = await ctx.channel.send(embed=embed)
            else:
                await self.songembed.edit(embed=embed)
        except Exception as e:
            print('embed error: ',e)
    
    async def queueEmbed(self,ctx,queue : list):
        pass

class Music(commands.Cog):
    def __init__(self,bot : commands.Bot):
        super().__init__()
        self.bot = bot
        self.embeds = CustomEmbeds()
        self.stopped = False
        self.history = []
        self.queue = []
    
    @commands.command(name='play', help="""
    This command help you adding your tracks to queue and play them instantly using <url> parameter that allows you to send a video or a playlist url from Youtube.
    - If you don't pass a <url> and the queue is not empty will be played the first song in the queue.
    - Call this command only if you are in a voice channel.
    - If you call this command before calling `join` the bot will join your current vocal channel anyway.""")
    async def play(self,ctx,*,query_or_url = None):
        await ctx.message.delete()
        
        try:
            assert ctx.message.author.voice, "{} You are not connected to a voice channel!".format(ctx.message.author.mention)
            if ctx.message.guild.voice_client is None: await ctx.message.author.voice.channel.connect()
            client = ctx.message.guild.voice_client

            if query_or_url is not None:
                if urlparse(query_or_url).scheme and urlparse(query_or_url).netloc:
                    url = query_or_url
                else: 
                    url = "https://www.youtube.com/results?search_query={}".format(query_or_url)

                audio_filelike = io.BytesIO()
                yt = YouTube(url=url)
                video = yt.streams.filter(only_audio=True).get_audio_only()
                video.stream_to_buffer(audio_filelike)
                audio_filelike.seek(0)



                song = {'title' : video.title,'filepath' : '','filelike' : audio_filelike,'thumbnail' : yt.thumbnail_url,'webpage_url': yt.watch_url,'uploader' : yt.author, 'uploader_url' : yt.channel_url,'duration' : yt.length}
                self.queue.append(song)

            if client.is_playing(): return #if is playing another song simply add that new song into the queue
            else:
                for song in self.queue:
                    client.stop()
                    ffmpeg_options = {'before_options': f"-reconnect 1 -reconnected_streamed 1 -reconnect_delay_max 5", 'options': "-vn"}

                    #client.play(nextcord.FFmpegPCMAudio(song['filepath'],executable=r"D:\Desktop\Coding\Python\discord-bot-server-6949\ffmpeg\ffmpeg.exe",**ffmpeg_options))
                    client.play(nextcord.FFmpegPCMAudio(song['filelike'],executable=r"D:\Desktop\Coding\Python\discord-bot-server-6949\ffmpeg\ffmpeg.exe",pipe=True,**ffmpeg_options))

                    sec = 0
                    while client.is_playing():
                        sec+=1
                        print('playing')
                        await self.embeds.songEmbed(ctx,song,sec)
                        await asyncio.sleep(1)
                    
                    self.history.append(song)
                    if song in self.queue:
                        self.queue.remove(song)

        except AssertionError as e: await ctx.channel.send(embed=Embed(title="Error:",description=e,color=Color.red()),delete_after=5)



def setup(bot):
    bot.add_cog(Music(bot))
