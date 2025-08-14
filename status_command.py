# status_command.py
import datetime
from main import bot  # import bot từ main.py

start_time = datetime.datetime.utcnow()

@bot.command()
async def status(ctx):
    uptime = datetime.datetime.utcnow() - start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    embed = discord.Embed(
        title="Trạng thái Bot",
        description=f"✅ Bot đang chạy\n⏱ Thời gian chạy: **{uptime_str}**",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
    
