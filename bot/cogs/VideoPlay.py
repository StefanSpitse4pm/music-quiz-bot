import discord
from discord.ext import commands
import yt_dlp
from collections import deque
from cogs.musicHandler import Musichandler

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class Videoplaying(commands.Cog, Musichandler):
    def __init__(self, bot):
        self.bot = bot
        self.queue = deque()
        self.song = None
        self.loopstate = "off"

    async def start_song(self, ctx):
        if self.queue:
            ffmpeg_options = {
                'options': '-vn',
            }
            if self.loopstate == "all":
                self.queue.append(self.song)
            if self.loopstate != "one":
                self.song = self.queue.popleft()
            duration = divmod(self.song['duration'], 60) 

            embed = discord.Embed(title="Now playing", color=discord.Color.purple())
            embed.add_field(name="", value=f"{self.song['title']}", inline=False)
            embed.add_field(name="", value=f"`[0:00 / {int(duration[0])}:{int(duration[1])}]`", inline=False)
            if self.loopstate != "off":
                embed.add_field(name="", value=f":repeat: looping{self.loopstate}")
            embed.set_thumbnail(url=self.song['thumbnails'][0]['url'])
        
            audio_url = await self.get_audio_url(self.song)
            await ctx.send(embed=embed)
            await self.play_audio_url(ctx, audio_url, ffmpeg_options)
        else:
            self.song = None            

    @commands.command()
    async def play(self, ctx, *, query:str = None):
        if not ctx.author.voice:
            await ctx.send("You should be in a voice channel")
            return
        if not query:
            await ctx.send("THE BILSTER DOES NOT KNOW WHAT YOU WANT PLEASE PUT IN WHAT YOU WANT!")
            return
        if not ctx.voice_client:
            await self.join_channel(ctx)

        if ctx.voice_client.is_playing():
            video_url = await self.search_video(query)
            self.queue.append(video_url)
            embed = discord.Embed(title="Queued", color=discord.Color.purple())
            embed.add_field(name="", value=f"{video_url['title']}", inline=False)
            embed.add_field(name="", value=f"In Position #{len(self.queue)}",inline=False)
            embed.set_thumbnail(url=video_url['thumbnails'][0]['url'])
            await ctx.send(embed=embed)

        else:
            
            video_url = await self.search_video(query)
            self.queue.append(video_url)
            await self.start_song(ctx)    
            
    @commands.command()
    async def join(self, ctx):
        await self.join_channel(ctx)

    @commands.command()
    async def queue(self, ctx):
        if ctx.voice_client.is_playing():
            embed = discord.Embed(title="Queue", color=discord.Color.purple())
            if not self.song:
                embed.add_field(name="", value="**Now playing**: Nothing.", inline=False)
            else:
                embed.add_field(name="", value=f"**Now playing**: {self.song['title']}", inline=False)
            i = 0
            for song in self.queue:
                i += 1
                embed.add_field(name="", value=f"#{i}: {song['title']}", inline=False)    
            await ctx.send(embed=embed)
    @commands.command()
    async def loop(self, ctx, state:str | None):
        if ctx.voice_client.is_playing() and ctx.author.voice:
            if state not in ["off", "one", "all"]:
                await ctx.send("You need to choose one of these commands `off`, `one` or `all`")
                return
            await ctx.send(f":repeat:Looping {state}")
            self.loopstate = state
            
    @commands.command()
    async def skip(self, ctx):
        if not ctx.author.voice or not ctx.voice_client or not ctx.voice_client.is_playing():
            return
        await ctx.send("the bilster is skipping the song...")
        ctx.voice_client.stop()
        await Videoplaying.next_song(ctx)
    
    @commands.command()
    async def leave(self, ctx):
        if not ctx.author.voice or not ctx.voice_client:
            return
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()