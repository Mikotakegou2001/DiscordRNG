import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import time
import json
import os
from keep_alive import keep_alive

# ==================== Khởi động Flask server ====================
keep_alive()

# ==================== DỮ LIỆU ====================
def save_game_data():
    with open('game_data.json', 'w') as f:
        json.dump({
            'player_data': player_data,
            'last_roll_times': last_roll_times
        }, f, indent=2)

def load_game_data():
    if os.path.exists('game_data.json'):
        try:
            with open('game_data.json', 'r') as f:
                data = json.load(f)
                player_data = data.get('player_data', {})
                last_roll_times = data.get('last_roll_times', {})

                for user_id, pdata in player_data.items():
                    if not isinstance(pdata, dict):
                        player_data[user_id] = {}
                    default_data = {
                        "money": 0,
                        "roles": [],
                        "active_role": None,
                        "luck": 1.0,
                        "roll_count": 0
                    }
                    for key, value in default_data.items():
                        if key not in player_data[user_id]:
                            player_data[user_id][key] = value

                return player_data, last_roll_times
        except (json.JSONDecodeError, IOError):
            print("Lỗi khi đọc file game_data.json, tạo dữ liệu mới")
            return {}, {}
    return {}, {}

# ==================== CẤU HÌNH ====================
ADMIN_ID = 464603232606617611  # Thay bằng ID admin của bạn
TARGET_CHANNEL_ID = 1358109476590321796

game_roles = [
    ("Common", 1/2, 1, 1358105936346091722, "R001", 1, 0xA9A9A9),
    ("Uncommon", 1/6, 2, 1358106208506085479, "R002", 2, 0x32CD32),
    ("Rare", 1/16, 3, 1358106861932642497, "R003", 5, 0x87CEFA),
    ("Ultra Rare", 1/28, 4, 1358106922259185684, "R004", 10, 0x1E90FF),
    ("Epic", 1/50, 5, 1358107017197129780, "R005", 25, 0x800080),
    ("Ultra Epic", 1/100, 6, 1358107140530901301, "R006", 50, 0xDA70D6),
    ("Legendary", 1/1000, 7, 1358107205819437317, "R007", 100, 0xFFD700),
    ("Mythical", 1/10000, 8, 1358107256364994640, "R008", 250, 0xFF0000),
    ("Secret", 1/100000, 9, 1358107299125788993, "R009", 500, 0x000000)
]

player_data, last_roll_times = load_game_data()

# ==================== HÀM TIỆN ÍCH ====================
def init_player(user_id):
    if str(user_id) not in player_data:
        player_data[str(user_id)] = {
            "money": 0,
            "roles": [],
            "active_role": None,
            "luck": 1.0,
            "roll_count": 0
        }
    else:
        default_data = {
            "money": 0,
            "roles": [],
            "active_role": None,
            "luck": 1.0,
            "roll_count": 0
        }
        for key, value in default_data.items():
            if key not in player_data[str(user_id)]:
                player_data[str(user_id)][key] = value
    save_game_data()

def weighted_random_roll(luck):
    adjusted_roles = [(r[0], r[1] * (luck if r[2] >= 4 else 1), *r[2:]) for r in game_roles]
    total = sum(r[1] for r in adjusted_roles)
    rand = random.uniform(0, total)
    cumulative = 0
    for role in adjusted_roles:
        cumulative += role[1]
        if rand <= cumulative:
            return role

def get_role_info(role_id):
    return next((r for r in game_roles if r[3] == role_id), None)

async def clear_roles(member, guild):
    for role in game_roles:
        if role_obj := guild.get_role(role[3]):
            if role_obj in member.roles:
                await member.remove_roles(role_obj)

async def get_user_from_input(ctx, user_input):
    """Hàm chuyển đổi user input (mention, ID hoặc tên) thành user object"""
    try:
        # Thử chuyển đổi thành user ID nếu là mention hoặc ID
        user_id = user_input.strip("<@!>")
        user = await ctx.guild.fetch_member(int(user_id))
        return user
    except:
        # Nếu không phải mention hoặc ID, tìm theo tên
        members = ctx.guild.members
        for member in members:
            if user_input.lower() in member.name.lower() or (member.nick and user_input.lower() in member.nick.lower()):
                return member
        return None

# ==================== GIAO DIỆN ====================
class PremiumRollView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(NormalRollButton())
        self.add_item(ShopButton())

class SuccessRollView(View):
    """View chứa nút Roll Again và Shop cho tin nhắn roll thành công"""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(NormalRollButton())
        self.add_item(ShopButton())

class RollAgainView(View):
    """View chứa nút Roll Again và Shop cho tin nhắn roll trùng"""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(NormalRollButton())
        self.add_item(ShopButton())

class NormalRollButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, 
                        label="Normal Roll (Free)", 
                        custom_id="normal_roll")

    async def callback(self, interaction):
        user_id = str(interaction.user.id)
        init_player(user_id)

        if time.time() - last_roll_times.get(user_id, 0) < 1.5:
            return await interaction.response.send_message(
                "⏳ Vui lòng đợi 1.5 giây!", 
                ephemeral=True
            )

        pdata = player_data[user_id]
        pdata["roll_count"] = pdata.get("roll_count", 0) + 1
        last_roll_times[user_id] = time.time()

        if pdata["roll_count"] >= 150:
            multiplier, roll_type = 5, "Exotic"
            pdata["roll_count"] = 0
        elif pdata["roll_count"] >= 12:
            multiplier, roll_type = 2, "Enchant"
        else:
            multiplier, roll_type = 1, "Normal"

        role = weighted_random_roll(pdata["luck"] * multiplier)

        if role[3] in pdata["roles"]:
            pdata["money"] += role[5]
            embed = discord.Embed(
                title="🎉 Chúc mừng!",
                description=f"{interaction.user.mention} đã roll được {role[0]} nhưng đã sở hữu, đã bán lại và nhận {role[5]}$! ♻️",
                color=0x32CD32
            )
            await interaction.response.send_message(embed=embed, view=RollAgainView())
        else:
            pdata["roles"].append(role[3])
            embed = discord.Embed(
                title=f"🎉 {roll_type} Roll thành công!",
                description=f"{interaction.user.mention} đã nhận được {role[0]}!",
                color=role[6]
            )
            embed.set_footer(text=f"Sử dụng !role {role[4]} để trang bị.")
            await interaction.response.send_message(embed=embed, view=SuccessRollView())

        save_game_data()

class ShopView(View):
    def __init__(self, cost, can_afford):
        super().__init__(timeout=None)
        if can_afford:
            self.add_item(BuyLuckButton(cost))
        else:
            disabled_button = BuyLuckButton(cost)
            disabled_button.disabled = True
            self.add_item(disabled_button)

class BuyLuckButton(Button):
    def __init__(self, cost):
        super().__init__(style=discord.ButtonStyle.success, 
                        label=f"Mua Luck - {cost}$", 
                        custom_id="buy_luck")

    async def callback(self, interaction):
        user_id = str(interaction.user.id)
        init_player(user_id)
        pdata = player_data[user_id]
        current_luck = pdata.get("luck", 1.0)

        if current_luck >= 1.5:
            return await interaction.response.send_message(
                "✅ Luck đã đạt tối đa!", 
                ephemeral=True
            )

        steps = int((current_luck - 1) * 10)
        cost = 100 * (10 ** steps)

        if pdata["money"] < cost:
            return await interaction.response.send_message(
                f"❌ Không đủ tiền! Cần {cost}$", 
                ephemeral=True
            )

        pdata["money"] -= cost
        pdata["luck"] = round(current_luck + 0.1, 1)
        save_game_data()

        # Cập nhật lại embed shop
        new_embed, can_afford = create_shop_embed(interaction.user)
        await interaction.response.edit_message(
            embed=new_embed, 
            view=ShopView(100 * (10 ** int((pdata["luck"] - 1) * 10)), can_afford)
        )

def create_shop_embed(user):
    user_id = str(user.id)
    init_player(user_id)
    pdata = player_data[user_id]
    current_luck = pdata.get("luck", 1.0)

    if current_luck >= 1.5:
        next_cost = "MAX"
        can_afford = False
    else:
        steps = int((current_luck - 1) * 10)
        next_cost = 100 * (10 ** steps)
        can_afford = pdata["money"] >= next_cost

    embed = discord.Embed(
        title="🛒 Discord RNG's Shop",
        description=(
            f"Xin chào, {user.display_name}!\n\n"
            "Dùng tiền để nâng cấp chỉ số Luck.\n"
            f"🍀 **Luck hiện tại:** {current_luck:.1f}\n"
            f"💰 **Số dư:** {pdata['money']}$\n"
            f"💵 **Giá nâng cấp tiếp theo:** {next_cost if isinstance(next_cost, int) else next_cost}$"
        ),
        color=0x00ffcc
    )
    return embed, can_afford

class ShopButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, 
                        label="Shop", 
                        custom_id="open_shop")

    async def callback(self, interaction):
        embed, can_afford = create_shop_embed(interaction.user)
        user_id = str(interaction.user.id)
        pdata = player_data[user_id]

        if pdata.get("luck", 1.0) >= 1.5:
            cost = "MAX"
        else:
            steps = int((pdata.get("luck", 1.0) - 1) * 10)
            cost = 100 * (10 ** steps)

        await interaction.response.send_message(
            embed=embed, 
            view=ShopView(cost, can_afford)
        )

# ==================== BOT COMMANDS ====================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Bot đã sẵn sàng với tên {bot.user.name}!")
    await bot.change_presence(activity=discord.Game(name="Discord RNG 2.0"))
    bot.add_view(PremiumRollView())
    bot.add_view(SuccessRollView())  # Đăng ký view cho roll thành công
    bot.add_view(RollAgainView())    # Đăng ký view cho roll trùng
    bot.add_view(ShopView(100, True))

@bot.command()
async def rng(ctx):
    if ctx.channel.id != TARGET_CHANNEL_ID:
        return await ctx.send(f"❌ Chỉ dùng trong <#{TARGET_CHANNEL_ID}>!", delete_after=5)

    user_id = str(ctx.author.id)
    init_player(user_id)
    pdata = player_data[user_id]

    active_role = "Chưa có"
    if pdata.get("active_role"):
        role_info = get_role_info(pdata["active_role"])
        if role_info:
            active_role = role_info[0]

    inventory = []
    for r in game_roles:
        if r[3] in pdata["roles"]:
            inventory.append(f"{r[4]} - {r[0]}")

    embed = discord.Embed(
        title="🎲 Discord RNG",
        description=(
            f"Xin chào, {ctx.author.display_name}!\n"
            f"👑 Role: {active_role}\n"
            f"💰 Số dư: {pdata['money']}$\n"
            f"🍀 Luck: {pdata.get('luck', 1.0):.1f}"
        ),
        color=0x00ff00
    )
    embed.add_field(
        name="📦 Inventory", 
        value="\n".join(inventory) if inventory else "Trống", 
        inline=False
    )
    await ctx.send(embed=embed, view=PremiumRollView())

@bot.command()
async def role(ctx, code: str):
    user_id = str(ctx.author.id)
    init_player(user_id)
    pdata = player_data.get(user_id, {})

    role_info = next((r for r in game_roles if r[4].lower() == code.lower()), None)
    if not role_info:
        return await ctx.send("⚠️ Role không tồn tại!", delete_after=5)
    if role_info[3] not in pdata.get("roles", []):
        return await ctx.send("❌ Bạn chưa sở hữu role này!", delete_after=5)

    await clear_roles(ctx.author, ctx.guild)
    role_obj = ctx.guild.get_role(role_info[3])
    if role_obj:
        await ctx.author.add_roles(role_obj)
        pdata["active_role"] = role_info[3]
        save_game_data()
        await ctx.send(f"✅ Đã trang bị {role_info[0]}!", delete_after=5)

@bot.command()
async def unrole(ctx):
    await clear_roles(ctx.author, ctx.guild)
    player_data[str(ctx.author.id)]["active_role"] = None
    save_game_data()
    await ctx.send("✅ Đã gỡ tất cả role!", delete_after=5)

@bot.command()
async def buyluck(ctx):
    user_id = str(ctx.author.id)
    init_player(user_id)
    pdata = player_data[user_id]
    current_luck = pdata.get("luck", 1.0)

    if current_luck >= 1.5:
        return await ctx.send("✅ Luck đã đạt tối đa!", delete_after=5)

    steps = int((current_luck - 1) * 10)
    cost = 100 * (10 ** steps)

    if pdata["money"] < cost:
        return await ctx.send(f"❌ Không đủ tiền! Cần {cost}$", delete_after=5)

    pdata["money"] -= cost
    pdata["luck"] = round(current_luck + 0.1, 1)
    save_game_data()
    await ctx.send(f"✅ Đã nâng cấp Luck lên {pdata['luck']:.1f}!", delete_after=5)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx, user_input: str):
    """Reset dữ liệu người chơi (chỉ admin)
    Cách dùng: !reset @user hoặc !reset username hoặc !reset userID"""
    if ctx.author.id != ADMIN_ID:
        return await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!", delete_after=5)

    user = await get_user_from_input(ctx, user_input)
    if not user:
        return await ctx.send("❌ Không tìm thấy người chơi!", delete_after=5)

    user_id = str(user.id)
    if user_id in player_data:
        # Xóa role hiện tại nếu có
        if player_data[user_id].get("active_role"):
            role_id = player_data[user_id]["active_role"]
            role_obj = ctx.guild.get_role(role_id)
            if role_obj and role_obj in user.roles:
                await user.remove_roles(role_obj)

        # Xóa dữ liệu
        del player_data[user_id]
        if user_id in last_roll_times:
            del last_roll_times[user_id]

        save_game_data()
        await ctx.send(f"✅ Đã reset hoàn toàn dữ liệu của {user.display_name}!")
    else:
        await ctx.send("ℹ️ Người chơi này chưa có dữ liệu để reset!", delete_after=5)

@bot.command()
@commands.has_permissions(administrator=True)
async def money(ctx, amount: int, user_input: str):
    """Thêm/trừ tiền cho người chơi (chỉ admin)
    Cách dùng: !money 100 @user hoặc !money -50 username"""
    if ctx.author.id != ADMIN_ID:
        return await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!", delete_after=5)

    user = await get_user_from_input(ctx, user_input)
    if not user:
        return await ctx.send("❌ Không tìm thấy người chơi!", delete_after=5)

    user_id = str(user.id)
    init_player(user_id)

    # Cập nhật số tiền
    player_data[user_id]["money"] += amount
    save_game_data()

    action = "thêm" if amount >= 0 else "trừ"
    await ctx.send(
        f"✅ Đã {action} {abs(amount)}$ cho {user.display_name}!\n"
        f"💰 Số dư mới: {player_data[user_id]['money']}$"
    )

# ==================== CHẠY BOT ====================
TOKEN = os.getenv('DISCORD_TOKEN') or "MTM1ODA5OTkyMTEzOTY2Mjg5OA.G8ozXf.719DtG1HI7gicn8cgA5BLd41Wndwj3mQ3el1Lg"

if __name__ == "__main__":
    bot.run(TOKEN)
