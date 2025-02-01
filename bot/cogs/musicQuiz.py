import discord
from discord.ext import commands
import yt_dlp
import csv
import random
import Levenshtein
from math import ceil
from collections import deque

from time import sleep
import aiomysql
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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class MusicQuiz(commands.Cog, Musichandler):
    
    def __init__(self, bot):
        self.bot = bot
        self.listening = None
        self.song = None
        self.game = {} 
        self.song_queue = deque()
        self.song_queue_length = 15
        self.song_length = 30    
    
    @commands.command()
    async def musicquiz(self, ctx):
        """THE BILSTER WILL START THE MUSIC QUIZ"""
        if self.listening is None:
            self.listening = True    
        else:    
            await ctx.send('Already playing the musicquiz')
            return
        self.game['channel'] = ctx.channel.name
        start_embed = discord.Embed(title="🎵 *The bilster start zo de Music Quiz!*", color=discord.Color.dark_green())
        start_embed.add_field(name="", value=f"This game will have {self.song_queue_length} song previews, {self.song_length} per seconds per song.", inline=False)
        start_embed.add_field(name="", value="You'll have to guess the artist name and the song name and get 80% correct of the name.", inline=False)
        start_embed.add_field(name="", value="```+ 1 point for the artist name\n+ 1 point for the song name\n+ 3 points for both```", inline=False)
        start_embed.add_field(name="", value="You can type `!pass` to vote for passing a song.", inline=False)
        start_embed.add_field(name="", value=":fire:THE BILSTER IS READY IN 10 seconds:fire:", inline=False)
        await ctx.send(embed=start_embed)
        sleep(7)
        # setup game
        self.game['voice'] = {ctx.author.voice.channel}
        self.game['song_guessed'] = False
        self.game['artist_guessed'] = False
        self.game['passes'] = 0
        self.song_number = 1
        self.thumbnail = None
        for member in ctx.author.voice.channel.members:
            self.game[member.name] = {'score':0}
        
        await self.join_channel(ctx)

        # get songs from csv file   
        with open('bot/audio/top200.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            songs = [row for row in reader]
            songs = random.sample   (songs, k=self.song_queue_length)
            self.song_queue.extend(songs)
        await self.start_song(ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.listening:
            print(self.game['channel'], message.channel)
            if message.author == self.bot.user or not message.guild:
                return
            
            if str(self.game['channel']) != str(message.channel):
                return

            if self.song is not None:
                # this code is here if someone was not in the game when they joined they will be added
                if message.author.name not in self.game and message.author.voice.channel == self.game['voice']:
                    self.game[message.author.name] = {'score':0}
                
                def string_percentage(m, title):
                    distance = Levenshtein.distance(m, title)
                    max_len = max(len(m), len(title))
                    similarity = (1 - distance / max_len) * 100
                    return similarity >= 80
                song_guessed = string_percentage(str(self.song['Title']).lower(),  str(message.content).lower())
                artist_guessed = string_percentage(str(self.song['Artists']).lower(),  str(message.content).lower())
                if not self.game['song_guessed'] and song_guessed:
                    await message.add_reaction('✅')
                    self.game[message.author.name]['score'] += 1
                    self.game['song_guessed'] = True
                    self.game['song_guesser'] = message.author.name
                    await message.reply(f'{message.author.mention} got one point there score is now **{self.game[message.author.name]['score']} points**')   
                
                elif not self.game['artist_guessed'] and artist_guessed:
                    await message.add_reaction('✅')
                    self.game[message.author.name]['score'] += 1
                    self.game['artist_guessed'] = True
                    self.game['artist_guesser'] = message.author.name
                    await message.reply(f'{message.author.mention} got one point there score is now **{self.game[message.author.name]['score']} points**', mention_author=True)
                else:
                    await message.add_reaction('❌')
        
                
                if self.game['artist_guessed'] and self.game['song_guessed']:
                    if self.game['song_guesser'] == self.game['artist_guesser']:
                        self.game[self.game['song_guesser']]['score'] += 1
                    ctx = await self.bot.get_context(message)
                    ctx.voice_client.stop()
                    await MusicQuiz.next_song(ctx)
        return

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user:  # Check if it's the bot
            if before.channel is not None and after.channel is None and self.listening:
                text_channel = member.guild.system_channel or member.guild.text_channels[0]  # Get system channel or first text channel
                if text_channel:
                    async for message in text_channel.history(limit=1):  # Get the latest message
                        ctx = await self.bot.get_context(message)  # Create a ctx object from that message
                        if ctx.valid:
                            self.reset(ctx)
                            await ctx.send("The bilster got disconnected from the voice channel\n terminated the music quiz")  # Use ctx.send()



    @commands.command(name="pass")
    async def pass_song(self, ctx):
        """ BILSTER IS DISSAPOINTED IN YOU THAT YOU DONT KNOW THE SONG"""
        if not self.listening:
            return
        if 'passed' not in self.game[ctx.author.name] or not self.game[ctx.author.name]['passed']:
            self.game[ctx.author.name]['passed'] = True
            self.game['passes'] += 1
            threshhold = ceil(len(ctx.author.voice.channel.members)/ 2)
            if self.game['passes'] >= threshhold: 
                self.game['passes'] = 0
                await ctx.send("the bilster is skipping the song...")
                ctx.voice_client.stop()
                await MusicQuiz.next_song(ctx)
                return
            else:
                await ctx.send(f':track_next:**{self.game['passes']} / {threshhold}** votes to pass the song') 
                return
        await ctx.reply('you already passed womp womp')
        return
 
    async def end_of_song(self, ctx):
        if self.song is not None:

            valid_entries = {player: data for player, data in self.game.items() if isinstance(data, dict) and "score" in data}
            top_3_players = sorted(valid_entries.items(), key=lambda item: item[1]["score"], reverse=True)[:3]
            leaderboard = ""
            rank_emojis = {
                    1: "🥇",
                    2: "🥈",
                    3: "🥉",
            }
            for rank, (player, data) in enumerate(top_3_players, start=1):
                emoji = rank_emojis.get(rank, "")
                username = player  # The player's name
                score = data["score"]  # The player's score
                leaderboard += f"{emoji} - {username} - {score}\n"
                self.top_3 = top_3_players
                self.leaderboard = leaderboard
            song_card = discord.Embed(title=f"It was: {self.song['Title']} - {self.song['Artists']}",
                                     description=f"Music Quiz - track {self.song_number - 1} / {self.song_queue_length}",
                                     color=discord.Color.dark_green())
            song_card.add_field(name="**__LEADERBOARD__**", value=leaderboard, inline=False)
            song_card.set_thumbnail(url=self.thumbnail)
            await ctx.send(embed=song_card)
        return

    async def start_song(self, ctx):
        await self.end_of_song(ctx)
        if self.song_queue:
            self.song_number += 1
            await self.reset_round(ctx)
            self.song = self.song_queue.popleft()
            video_url = await self.search_video(f"{self.song['Title']}, {self.song['Artists']}")
            audio_url = await self.get_audio_url(video_url)
            await self.play_audio_url(ctx, audio_url)
        else:
            await self.reset(ctx)
            end_embed = discord.Embed(title="Music Quiz Ranking", color=discord.Color.purple())
            end_embed.add_field(name="", value=self.leaderboard, inline=False)
            await ctx.send(embed=end_embed)
            await ctx.voice_client.disconnect()
            await self.send_info_db()

    async def reset(self, ctx):
        self.listening = None
        self.song = None
        await self.reset_round(ctx)
        self.game = {}

    async def reset_round(self, ctx):
        self.game['song_guessed'] = False
        self.game['artist_guessed'] = False
        self.game['passes'] = 0

        for member in ctx.author.voice.channel.members:
            if member.name != self.bot.user.name:
                self.game[member.name]['passed'] = False

    async def send_info_db(self):
        try:
            self.db_pool = await aiomysql.create_pool(
                host="localhost",
                port=3306,
                user="root",
                password="qwerty",
                db="bilster",
                autocommit=True
            )
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("INSERT INTO `wins`(`username`, `score`) VALUES (%s,%s)", (self.top_3[0][0], self.top_3[0][1]['score']))
        except Exception as e:
            print(e)