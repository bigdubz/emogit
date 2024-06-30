import main
import json
import random
import discord
from cogs import edit_stats as es

from discord import app_commands
from discord.ext import commands


GRID_SIZE = 11
MAX_MOVES = GRID_SIZE * 2 - 1


class Cmiyc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name='catch',
        description='Starts a Catch game against mentioned user with a bet'
    )
    async def create_challenge(self, action: discord.Interaction, mention: str, bet_amount: str):
        player_id = str(action.user.id)
        if not mention or not mention.startswith("<@") or not mention.endswith(">"):
            await action.response.send_message("please mention an opponent", delete_after=5)
            return

        opponent_id = mention[2:-1]
        if player_id == opponent_id:
            await action.response.send_message("are you fucking stupid?", delete_after=5)
            return

        if await check_if_game_exists(action, player_id, opponent_id):
            return

        if not bet_amount or not bet_amount.isdigit():
            await action.response.send_message("please enter a valid bet amount"
                                               " greater than 0 thanks dumbass", delete_after=5)
            return

        bet_amount = int(bet_amount)
        if bet_amount <= 0:
            await action.response.send_message("please enter a valid bet amount"
                                               " greater than 0 thanks dumbass", delete_after=5)
            return

        with open("json/stats.json", "r") as file:
            stats = json.load(file)

        if opponent_id not in stats or stats[player_id]["points"] < bet_amount or stats[opponent_id]["points"] \
                < bet_amount:
            await action.response.send_message("either you or your opponent dont have enough points", delete_after=5)
            return

        game_id = generate_game_id()
        with open("json/cmiyc.json", "r") as file:
            games = json.load(file)

        player_pos = [random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)]  # (Row, Column)
        while True:
            opponent_pos = [random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)]
            if opponent_pos != player_pos:
                break

        games[game_id] = {
            "challenger": {
                "id": player_id,
                "position": player_pos
            },
            "opponent": {
                "id": opponent_id,
                "position": opponent_pos
            },
            "bet amount": bet_amount,
            "accepted": False,
            "map": None,
            "total moves": 0,
            "turn": opponent_id,
        }
        games[game_id]["map"] = get_grid(games[game_id])

        with open("json/cmiyc.json", "w") as file:
            json.dump(games, file, sort_keys=True, indent=4)

        await action.response.send_message(
            f"{mention}, do you accept this Catch game against <@{player_id}> with bet {bet_amount}?\n"
            f"`/accept` or `/reject`"
        )

    @app_commands.command(name='accept', description='Accepts the Catch game challenge')
    async def accept(self, action: discord.Interaction):
        user_id = str(action.user.id)
        game_id = await find_game(action, user_id)
        if game_id is None:
            return

        with open("json/cmiyc.json", "r") as file:
            games = json.load(file)

        if not games[game_id]["accepted"]:
            games[game_id]["accepted"] = True
            challenger_id = games[game_id]["challenger"]["id"]
            bet_amount = games[game_id]["bet amount"]
            with open("json/cmiyc.json", "w") as file:
                json.dump(games, file, sort_keys=True, indent=4)

            es.add_points(await self.bot.get_context(action), -bet_amount)
            es.add_points(await self.bot.get_context(action), -bet_amount, override_id=challenger_id)
            await get_outcome(action, game_id)

        else:
            await action.response.send_message("nothing to accept", delete_after=5)

    @app_commands.command(name='reject', description='Rejects the Catch game challenge')
    async def reject(self, action: discord.Interaction):
        user_id = str(action.user.id)
        game_id = await find_game(action, user_id)
        if game_id is None:
            return

        with open("json/cmiyc.json", "r") as file:
            games = json.load(file)

        if not games[game_id]["accepted"]:
            await action.response.send_message("game rejected")
            del games[game_id]

        else:
            await action.response.send_message("nothing to reject", delete_after=5)

        with open("json/cmiyc.json", "w") as file:
            json.dump(games, file, sort_keys=True, indent=4)

    @app_commands.command(name='refresh', description='Resends the current Catch game in case of an error')
    async def refresh(self, action: discord.Interaction):
        game_id = await find_game(action, str(action.user.id))
        await get_outcome(action, game_id)

    async def get_outcome(self, action: discord.Interaction, game_id):
        with open("json/cmiyc.json", "r") as file:
            games = json.load(file)

        if game_id not in games:
            return

        games[game_id]["map"] = get_grid(games[game_id])
        message = ""

        for y in games[game_id]["map"]:
            for x in y:
                message += x
            message += "\n"

        embed = discord.Embed(description=message, color=0x00ffff)
        challenger_id = games[game_id]["challenger"]["id"]
        opponent_id = games[game_id]["opponent"]["id"]
        bet_amount = games[game_id]["bet amount"]
        if games[game_id]["opponent"]["position"] == games[game_id]["challenger"]["position"]:
            await action.channel.send(
                f"<@{challenger_id}> wins by catching opponent! "
                f"they gained {bet_amount} points", embed=embed
            )
            name = main.bot.get_user(int(challenger_id))
            es.add_points(await self.bot.get_context(action), 2 * bet_amount, override_id=challenger_id, name=name)
            del games[game_id]
            with open("json/cmiyc.json", "w") as file:
                json.dump(games, file)

            return

        elif games[game_id]["total moves"] > MAX_MOVES:
            await action.channel.send(
                f"<@{opponent_id}> wins by surviving! they gained {bet_amount} points", embed=embed
            )
            name = main.bot.get_user(int(opponent_id))
            es.add_points(await self.bot.get_context(action), 2 * bet_amount, override_id=opponent_id, name=name)
            del games[game_id]
            with open("json/cmiyc.json", "w") as file:
                json.dump(games, file)

            return

        turn_id = games[game_id]["turn"]
        buttons = Buttons(game_id)
        await action.channel.send(f"<@{turn_id}> its your turn", embed=embed, view=buttons)


# noinspection PyUnusedLocal
class Buttons(discord.ui.View):
    def __init__(self, game_id):
        super().__init__()
        self.value = None
        self.game_id = game_id

    @discord.ui.button(label="⬆️", style=discord.ButtonStyle.grey)
    async def up(self, ctx: discord.Interaction, button: discord.ui.Button):
        await delete_message(ctx)
        await make_move(ctx, self.game_id, 0, -1)

    @discord.ui.button(label="⬇️", style=discord.ButtonStyle.grey)
    async def down(self, ctx: discord.Interaction, button: discord.ui.Button):
        await delete_message(ctx)
        await make_move(ctx, self.game_id, 0, 1)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.grey)
    async def left(self, ctx: discord.Interaction, button: discord.ui.Button):
        await delete_message(ctx)
        await make_move(ctx, self.game_id, -1, 0)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.grey)
    async def right(self, ctx: discord.Interaction, button: discord.ui.Button):
        await delete_message(ctx)
        await make_move(ctx, self.game_id, 1, 0)


async def make_move(ctx, game_id, x_diff, y_diff):
    player_id = str(ctx.user.id)
    with open("json/cmiyc.json", "r") as file:
        games = json.load(file)

    if not games[game_id]["accepted"]:
        await ctx.channel.send("game not yet accepted!")
        return

    if not games[game_id]["turn"] == player_id:
        await ctx.channel.send(f"<@{player_id}>its not your turn!")
        await get_outcome(ctx, game_id)
        return

    name = None
    for x in games[game_id]:
        try:
            if games[game_id][x]["id"] == player_id:
                name = x

        except TypeError:
            continue

    games[game_id][name]["position"][0] += x_diff
    games[game_id][name]["position"][1] += y_diff
    x = games[game_id][name]["position"][0]
    y = games[game_id][name]["position"][1]
    if x > GRID_SIZE - 1 or x < 0 or y > GRID_SIZE - 1 or y < 0:
        await ctx.channel.send("cant do that, out of bounds")
        await get_outcome(ctx, game_id)
        return

    games[game_id]["turn"] = games[game_id]["opponent"]["id"] if \
        games[game_id]["turn"] == games[game_id]["challenger"]["id"] else games[game_id]["challenger"]["id"]

    games[game_id]["total moves"] += 1
    with open("json/cmiyc.json", "w") as file:
        json.dump(games, file, sort_keys=True, indent=4)

    await get_outcome(ctx, game_id)


async def find_game(action: discord.Interaction, user_id):
    with open("json/cmiyc.json", "r") as file:
        games = json.load(file)

    for game in games:
        if user_id == games[game]["opponent"]["id"] or user_id == games[game]["challenger"]["id"]:
            return game

    await action.response.send_message("no game found")


async def check_if_game_exists(action: discord.Interaction, id1, id2):
    with open("json/cmiyc.json", "r") as file:
        games = json.load(file)

    for game in games:
        if games[game]["challenger"]["id"] == id1 or games[game]["opponent"]["id"] == id1:
            await action.response.send_message("either player already in game")
            return True

        if games[game]["challenger"]["id"] == id2 or games[game]["opponent"]["id"] == id2:
            await action.response.send_message("either player already in game")
            return True

    return False


def get_grid(game_data: dict):
    player_pos = game_data["challenger"]["position"]
    opponent_pos = game_data["opponent"]["position"]
    grid = [["⬛" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if [x, y] == player_pos:
                grid[y][x] = "🟩"

            elif [x, y] == opponent_pos:
                grid[y][x] = "🟥"

    return grid


def generate_game_id():
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%&*"
    game_id = ""
    while len(game_id) < 6:
        game_id += random.choice(allowed)

    with open("json/cmiyc.json", "r") as file:
        game_data = json.load(file)

    for game in game_data:
        if game_id == game:
            generate_game_id()

    return game_id


async def delete_message(action: discord.Interaction):
    history = action.channel.history(limit=10)
    async for msg in history:
        if msg.author.id == 1136467634355966015:
            await msg.delete()
            return


async def setup(bot: commands.Bot):
    await bot.add_cog(Cmiyc(bot))
