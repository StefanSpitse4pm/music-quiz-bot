import discord
from discord.ext import commands
import asyncio
from cogs.musicQuiz import MusicQuiz
from cogs.VideoPlay import Videoplaying
import logging
import os
from dotenv import load_dotenv 

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(root=True, handler=handler)

intents = discord.Intents.default()
intents.message_content = True

load_dotenv()

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description='THE BILSTER THINKS YOU ARE A NERD',
    intents=intents
)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


async def main():
    async with bot:
        await bot.add_cog(MusicQuiz(bot))
        await bot.add_cog(Videoplaying(bot))
        await bot.start(os.getenv("testing"))


asyncio.run(main())