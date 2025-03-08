import datetime
import json
import discord

from random import randint
from discord import app_commands
from discord.ext import commands


def edit_stats(ctx: commands.Context,
               user_id: str,
               _name: str = None,
               _level: int = None,
               _xp: int = None,
               _pts: int = None,
               _msg_total: int = None,
               _bonus: str = None,
               _athan: bool = None,
               _weather: bool = None,
               _reminders: dict = None):
    with open("json/stats.json", "r") as file:
        user_data = json.load(file)

    if user_id not in user_data:
        user_data[user_id] = {
            "name": _name if _name is not None else ctx.author.name,
            "level": 1,
            "xp": _xp if _xp is not None else 0,
            "points": _pts if _pts is not None else 0,
            "total messages": _msg_total if _msg_total is not None else 0,
            "bonus claimed at": _bonus if _bonus is not None else f"{datetime.datetime(2000, 1, 1, 0, 0, 0, 1)}",
            "athan reminder": _athan if _athan is not None else False,
            "weather updates": _weather if _weather is not None else False,
            "reminders": _reminders if _reminders is not None else {}
        }

        with open("json/stats.json", "w") as file:
            json.dump(user_data, file, indent=4)

        return

    user_data[user_id] = {
        "name": _name if _name is not None else user_data[user_id]["name"],
        "level": _level if _level is not None else user_data[user_id]["level"],
        "xp": _xp if _xp is not None else user_data[user_id]["xp"],
        "points": _pts if _pts is not None else user_data[user_id]["points"],
        "total messages": _msg_total if _msg_total is not None else user_data[user_id]["total messages"],
        "bonus claimed at": _bonus if _bonus is not None else user_data[user_id]["bonus claimed at"],
        "athan reminder": _athan if _athan is not None else user_data[user_id]["athan reminder"],
        "weather updates": _weather if _weather is not None else user_data[user_id]["weather updates"],
        "reminders": _reminders if _reminders is not None else user_data[user_id]["reminders"]
    }

    with open("json/stats.json", "w") as file:
        json.dump(user_data, file, indent=4)


def add_points(ctx: commands.Context, amount: int, override_id=None, name=None):
    user_id = override_id if override_id is not None else str(ctx.author.id)
    edit_stats(ctx, user_id)
    with open("json/stats.json", "r") as file:
        user_data = json.load(file)

    if user_data[user_id]['points'] == "inf":
        return;

    edit_stats(ctx, user_id, _name=name, _pts=(user_data[user_id]['points'] + amount))


async def count_message(ctx: commands.Context):
    user_id = str(ctx.author.id)
    edit_stats(ctx, user_id)
    with open("json/stats.json", "r") as file:
        user_data = json.load(file)

    xp_required = 20 + (int(user_data[user_id]["level"]) + 1) * 10
    lvled_up = user_data[user_id]["xp"] + 5 >= xp_required
    lvl = user_data[user_id]["level"] + 1 if lvled_up else user_data[user_id]["level"]
    xp = 0 if lvled_up else user_data[user_id]["xp"] + 5
    total_msgs = user_data[user_id]["total messages"] + 1

    edit_stats(ctx, user_id, _xp=xp, _level=lvl, _msg_total=total_msgs)
    with open("json/stats.json", "r") as file:
        user_data = json.load(file)

    if lvled_up:
        add_points(ctx, lvl // 10)

    if user_data[user_id]["total messages"] % 10 == 0:
        add_points(ctx, 3)


class UserStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='donate', description='Donates points to another user')
    async def give_points(self, ctx: commands.Context, mention: str, amount: int):
        receiver_id = mention[2:-1]
        giver_id = str(ctx.author.id)
        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        if user_data[giver_id]['points'] != 'inf' and user_data[giver_id]['points'] < amount:
            await ctx.send(
                f"<@{ctx.message.author.id}> you do not have enough points, poor", delete_after=5
            )
            return

        if amount < 1:
            await ctx.send("tryna cheat ya piece of shit?", delete_after=5)
            return

        if giver_id == receiver_id:
            await ctx.send("so fking dumb", delete_after=5)
            return

        if len(receiver_id) >= 18:
            name = (await ctx.guild.query_members(user_ids=[int(receiver_id)]))[0].name
            add_points(ctx, -amount)
            add_points(ctx, amount, receiver_id, name)
            await ctx.send(
                f"<@{giver_id}> gave {amount} point{'s' if amount > 1 else ''} to {mention}"
            )

        else:
            await ctx.send("user not found", delete_after=5)

    @commands.hybrid_command(name='roll', description='Gambles points with a 50% chance of winning')
    async def roll(self, ctx: commands.Context, amount: str = None):
        user_id = str(ctx.author.id)
        if amount is None or (not amount.isdigit() and amount != "all"):
            await ctx.send("roll a fucking amount, is your syndrome down?", delete_after=5)
            return

        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        if amount == "all":
            amount = user_data[user_id]['points']

        if user_data[user_id]['points'] != 'inf':
            amount = int(amount)

            if amount < 1:
                await ctx.send("stupid ass", delete_after=5)
                return

            if amount > user_data[user_id]["points"]:
                await ctx.send("you dont have enough points you broke bitch", delete_after=5)
                return

        p = user_data[user_id]['points']
        w = f"{p + amount}" if p != 'inf' else 'infinite'
        l = f"{p - amount}" if p != 'inf' else 'infinite'

        if randint(0, 1) == 1:
            add_points(ctx, amount)
            await ctx.send(
                f"<@{user_id}> you got lucky for once and you gained {amount} points."
                f" you now have {w} points"
            )

        else:
            if amount != 'inf':
                add_points(ctx, -amount)
            await ctx.send(
                f"<@{user_id}> you really thought gamblers win LMAO. you lost {amount} points. you now have "
                f"{l} points"
            )

    @app_commands.command(name='claim', description='Claims your daily points bonus')
    async def claim_bonus(self, action: discord.Interaction):
        bonus_amount = 25
        user_id = str(action.user.id)
        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        tn = datetime.datetime.now()
        tc = datetime.datetime.strptime(user_data[user_id]["bonus claimed at"], "%Y-%m-%d %H:%M:%S.%f")
        days_since_last_claim = (tn - tc).days
        if days_since_last_claim > 0:
            edit_stats(await self.bot.get_context(action), user_id, _bonus=str(datetime.datetime.now()))
            add_points(await self.bot.get_context(action), bonus_amount)
            await action.response.send_message(f"<@{user_id}> you claimed your daily {bonus_amount} points")

        else:
            next_claim = datetime.datetime(tc.year, tc.month, tc.day + 1,
                                           tc.hour, tc.minute, tc.second)
            tl = (next_claim - datetime.datetime.now()).seconds
            h, r = divmod(tl, 3600)
            m, s = divmod(r, 60)
            await action.response.send_message(
                f"<@{user_id}> it hasnt been 24 hours yet you broke cunt\n next claim in {h}:{m}:{s} hr"
            )

    @app_commands.command(name='points', description='Shows your current points')
    async def points(self, action: discord.Interaction):
        user_id = str(action.user.id)
        with open("json/stats.json", "r") as file:
            user_data = json.load(file)


        m = user_data[user_id]['points']
        am = m if m != 'inf' else 'infinite'
        await action.response.send_message(f"<@{user_id}> you have {am} points")

    @commands.command(name='reset', description='Reset all stats **owner only**')
    async def reset(self, ctx: commands.Context):
        if not await self.bot.is_owner(ctx.message.author):
            await ctx.send("unauthorized")
            return

        all_user_ids = {}
        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        for usr_id in user_data:
            all_user_ids[usr_id] = {
                "name": user_data[usr_id]["name"],
                "level": 1,
                "xp": 0,
                "points": 0,
                "total messages": 0,
                "bonus claimed at": f"{datetime.datetime(2000, 1, 1, 0, 0, 0, 1)}",
                "athan reminder": False
            }

        with open("json/stats.json", "w") as outfile:
            json.dump(all_user_ids, outfile, indent=4)

    @commands.command(name='givehead', description='Self explanatory')
    async def givehead(self, ctx: commands.Context):
        head_cost = 10
        user_id = str(ctx.author.id)
        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        if user_data[user_id]['points'] == 'inf' or user_data[user_id]['points'] >= head_cost:
            await ctx.send(f"<@{user_id}> slurp slurp\nDo you like that?")
            add_points(ctx, -head_cost)

        else:
            await ctx.send(f"you're so fucking broke lmao <@{user_id}> (need {head_cost} points)", delete_after=5)

    @app_commands.command(
        name='athan',
        description='Toggles athan reminders. Sends you DMs at athan times when toggled on'
    )
    async def toggle_athan(self, action: discord.Interaction):
        user_id = str(action.user.id)
        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        val = not user_data[user_id]['athan reminder']
        edit_stats(await self.bot.get_context(action), user_id, _athan=val)
        if val:
            await action.response.send_message(
                f"<@{user_id}> athan reminders toggled on. you will now receive DMs at athan times."
            )

        else:
            await action.response.send_message(f"<@{user_id}> athan reminders toggled off", delete_after=5)

    @app_commands.command(
        name='weather',
        description='Toggles daily weather forecast. Sends the weather forecast everyday at 7AM.'
    )
    async def toggle_weather(self, action: discord.Interaction):
        user_id = str(action.user.id)
        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        val = not user_data[user_id]['weather updates']
        edit_stats(await self.bot.get_context(action), user_id, _weather=val)
        if val:
            await action.response.send_message(
                f"<@{user_id}> daily weather forecast toggled on."
                f" you will now receive the weather forecast everyday at 7AM."
            )

        else:
            await action.response.send_message(f"<@{user_id}> daily weather forecast toggled off", delete_after=5)

    @app_commands.command(name='level', description='Shows your current level')
    async def level(self, action: discord.Interaction):
        user_id = str(action.user.id)
        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        await action.response.send_message(f"<@{user_id}> you are currently level {user_data[user_id]['level']}")

    @commands.command(name='add_field')
    async def add_field(self, ctx: commands.Context, field_name: str):
        if not await self.bot.is_owner(ctx.message.author):
            await ctx.send("unauthorized")
            return

        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        for user in user_data:
            user_data[user][field_name] = {}  # edit type for every new field

        with open("json/stats.json", "w") as file:
            json.dump(user_data, file, indent=4)

    @commands.command(name='delete_field')
    async def delete_field(self, ctx: commands.Context, field_name):
        if not await self.bot.is_owner(ctx.message.author):
            await ctx.send("unauthorized")
            return

        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        for user in user_data:
            del user_data[user][field_name]

        with open("json/stats.json", "w") as file:
            json.dump(user_data, file, indent=4)


async def setup(bot: commands.Bot):
    await bot.add_cog(UserStats(bot))
