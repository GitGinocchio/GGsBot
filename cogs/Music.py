from nextcord import Embed,Color,utils,channel,Permissions
from nextcord.ext import commands
import asyncio,os
import wavelink
from pathlib import Path
from urllib.parse import urlparse
current_path = Path(__file__).absolute().parent


class API:
    def __init__(self):
        pass

class Music(commands.Cog):
    def __init__(self,bot):
        super().__init__()
        self.bot = bot
        self.api = API()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.node_connect())

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node : wavelink.Node):
        print(f'Node {node.id},{node.players}.{node.uri},{node.password} is ready!')

    async def node_connect(self):
        node: wavelink.Node = wavelink.Node(uri='http://usui-linku.kadantte.moe:443', password='Usui#0256',use_http=True,secure=True) #wavelink.Node(uri='http://lavalinkinc.ml:443',password='incognito')
        await wavelink.NodePool.connect(client=self.bot,nodes=[node])
        #await wavelink.NodePool.create_node(bot=self.bot,host='lavalinkinc.ml',port=443,password='incognito',https=True)
    
    @commands.command(name='play')
    async def play(self,ctx : commands.Context, *, search: str):
        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        if not wavelink.NodePool.available_nodes():
            await ctx.send("Mi dispiace, non sono attualmente connesso a un nodo Wavelink.")
            return

        tracks = await wavelink.YouTubeTrack.search(search)
        if not tracks:
            await ctx.send(f"Mi dispiace, non ho trovato alcuna canzone con la ricerca: `{search}`")
            return

        player = self.bot.get_player(ctx.guild.id)
        if not player:
            player = await self.bot.wavelink.get_player(ctx.guild.id)
        

        await player.play(tracks[0])
        await ctx.send(f"Canzone aggiunta alla coda: `{tracks[0].title}`")
        #track: wavelink.YouTubeTrack = tracks[0]
        #await vc.play(track)



def setup(bot):
    bot.add_cog(Music(bot))

if __name__ == "__main__": os.system("python main.py")