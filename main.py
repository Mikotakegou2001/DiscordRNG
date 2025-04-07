from keep_alive import keep_alive
keep_alive()

import os
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

bot.run(os.getenv("TOKEN"))
