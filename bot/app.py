import discord
from discord.ext import commands
import asyncio
from cogs.musicQuiz import MusicQuiz
import logging

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(root=True, handler=handler)

intents = discord.Intents.default()
intents.message_content = True


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
        await bot.start("MTIxNTA1ODcxODU0NzI1NTI5Ng.G_sx7U.XQXlPpVdZywRQNnBxjmpohNgNAD486rVvkkKkk")  # Use environment variable for token


asyncio.run(main())