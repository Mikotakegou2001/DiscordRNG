import discord
import datetime
from main import bot  # lấy bot từ main.py

start_time = datetime.datetime.utcnow()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() == "status":
        uptime = datetime.datetime.utcnow() - start_time
        h, r = divmod(int(uptime.total_seconds()), 3600)
        m, s = divmod(r, 60)
        embed = discord.Embed(
            title="Trạng thái Bot",
            description=f"✅ Bot đang chạy\n⏱ Thời gian chạy: **{h}h {m}m {s}s**",
            color=discord.Color.blue()
        )
        await message.channel.send(embed=embed)

    await bot.process_commands(message)
