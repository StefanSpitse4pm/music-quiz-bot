import yt_dlp
import discord
from functools import partial


class Musichandler():
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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

    ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


    @staticmethod
    async def search_video(query):
        ydl_opts = {
            'quiet': True,
            'extract_flat': True, 
            'force_generic_extractor': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in result:
                return result['entries'][0]
            return None
       
    async def get_audio_url(self, video_url):
        if video_url:
            ydl_opts = {
                'format': 'bestaudio/best',
                'extractaudio': True, 
                'audioquality': 1,  
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'noplaylist': True,
                'quiet': True,  
                'no_warnings': True,  
                'extract_flat': True,  
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url['url'], download=False)
                self.thumbnail = info_dict.get('thumbnail')
                self.title = info_dict.get('title', 'Unknown Title')
                formats = info_dict.get('formats', [])
                audio_url = None

                for fmt in formats:
                    if fmt.get('acodec') != 'none': 
                        audio_url = fmt['url']
                        break
            return audio_url
        
    async def play_audio_url(self, ctx, audio_url, ffmpeg_options = None):
        voice_client = ctx.voice_client
        
        # here for if the bots is disconnected.
        # make sure that there is a reset function
        if not voice_client:
            await self.reset(ctx)

        if not ffmpeg_options:
            ffmpeg_options = {
                'before_options': '-ss 50',
                'options': f'-t {self.song_length} -vn',
            }
              
        
        source = discord.FFmpegPCMAudio(source=audio_url, **ffmpeg_options)

        voice_client.play(source,after=partial(self.next_song, ctx=ctx))

    def next_song(self, error=None, ctx=None):
            if error:
                print(error)
            self.bot.loop.create_task(self.start_song(ctx)) 

    async def join_channel(self, ctx):
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
            if not ctx.voice_client:
                try:
                    await voice_channel.connect()
                except Exception as e:
                    print(e)
                    await ctx.send("Something went wrong  the bilster can not join!")
            else:
                await ctx.send("The bilster is already in the voice channel!")
        else:
            await ctx.send("Your not in a voice channel THE BILSTER CAN NOT JOIN!")