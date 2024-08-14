import asyncio
import json
import random
from cogs import edit_stats

from discord.ext import commands


deck = ["2♠", "3♠", "4♠", "5♠", "6♠", "7♠", "8♠", "9♠", "10♠", "J♠", "Q♠", "K♠", "A♠",
        "2♥", "3♥", "4♥", "5♥", "6♥", "7♥", "8♥", "9♥", "10♥", "J♥", "Q♥", "K♥", "A♥",
        "2♣", "3♣", "4♣", "5♣", "6♣", "7♣", "8♣", "9♣", "10♣", "J♣", "Q♣", "K♣", "A♣",
        "2♦", "3♦", "4♦", "5♦", "6♦", "7♦", "8♦", "9♦", "10♦", "J♦", "Q♦", "K♦", "A♦"]

values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
          "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11}

naturals = [["A", "10"], ["A", "J"], ["A", "Q"], ["A", "K"],
            ["10", "A"], ["J", "A"], ["Q", "A"], ["K", "A"]]


class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='blackjack', description='Starts a Blackjack game with bet')
    async def blackjack(self, ctx: commands.Context, bet_amount: str = None):
        user_id = str(ctx.author.id)
        if bet_amount is None:
            await ctx.send("you need to bet an amount!\n`!blackjack <BetAmount>`", delete_after=5)
            return

        if not bet_amount.isdigit() and bet_amount != "all":
            await ctx.send("bet an AMOUNT. dumbass", delete_after=5)
            return

        with open("json/stats.json", "r") as file:
            stats = json.load(file)
            user_points = stats[user_id]['points']

        if bet_amount == "all":
            bet_amount = user_points

        bet_amount = int(bet_amount)
        if bet_amount < 1:
            await ctx.send("retarded much?", delete_after=5)
            return

        if bet_amount > user_points:
            await ctx.send("you dont have enough points. brokie", delete_after=5)
            return

        with open("json/blackjack.json", "r") as file:
            game_data = json.load(file)
            if user_id not in game_data:
                game_data[user_id] = {"deck": deck}

            for game in game_data[user_id]:
                if game == "deck":
                    continue

                if not game_data[user_id][game]["concluded"]:
                    await ctx.send("you already have a game ongoing", delete_after=5)
                    return

        with open("json/blackjack.json", "w") as file:
            json.dump(game_data, file, indent=8)

        edit_stats.add_points(ctx, -bet_amount)
        game_id = await create_game(ctx, bet_amount)
        with open("json/blackjack.json", "r") as file:
            users_game_data = json.load(file)

        p_hand = users_game_data[user_id][game_id]['player hand']['hand']
        d_hand = users_game_data[user_id][game_id]['dealer hand']['hand']
        if (users_game_data[user_id][game_id]['player hand']['value'] == 21 and
                users_game_data[user_id][game_id]['dealer hand']['value'] < 21):
            await ctx.send(f"<@{user_id}> bet {bet_amount} points\n\n"
                           f"your hand: {', '.join(p_hand)}\n"
                           f"your hand value: 21\n\n"
                           f"dealer hand: {', '.join(d_hand)}\n"
                           f"dealer hand value: {calculate_hand_value(d_hand)}\n\n"
                           f"natural blackjack!\n"
                           f"you gained {bet_amount} points")
            edit_stats.add_points(ctx, 2 * bet_amount)
            users_game_data[user_id][game_id]["concluded"] = True
            with open("json/blackjack.json", "w") as file:
                json.dump(users_game_data, file, indent=8)

            return

        if (users_game_data[user_id][game_id]['player hand']['value'] == 21 and
                users_game_data[user_id][game_id]['dealer hand']['value'] == 21):
            await ctx.send(f"<@{user_id}> bet {bet_amount} points\n\n"
                           f"your hand: {', '.join(p_hand)}\n"
                           f"your hand value: 21\n\n"
                           f"dealer hand: {', '.join(d_hand)}\n"
                           f"dealer hand value: 21\n\n"
                           f"tie!\n"
                           f"you got your {bet_amount} points back")
            add_points(ctx, bet_amount)
            users_game_data[user_id][game_id]["concluded"] = True
            with open("json/blackjack.json", "w") as file:
                json.dump(users_game_data, file, indent=8)

            return

        await ctx.send(f"<@{user_id}> bet {bet_amount} points\n\n"
                       f"your hand: {', '.join(p_hand)}\n"
                       f"your hand value: {users_game_data[user_id][game_id]['player hand']['value']}\n\n"
                       f"dealer hand: {d_hand[0]}, ??\n"
                       f"dealer hand value: {calculate_hand_value([d_hand[0]])}\n\n"
                       f"!hit, !stand, or !double?")

    @commands.command(name='stand', description='Blackjack command: Stands')
    async def stand(self, ctx: commands.Context):
        user_id = str(ctx.message.author.id)
        if not game_active(ctx):
            await ctx.send("you havent started a blackjack game yet\n"
                           "start one with `!blackjack <BetAmount>`", delete_after=5)
            return

        with open("json/blackjack.json", "r") as file:
            users_game_data = json.load(file)
            game_id = find_game_id(ctx)

        users_game_data[user_id][game_id]['stood'] = True
        users_game_data[user_id][game_id]['can double'] = False

        with open("json/blackjack.json", "w") as file:
            json.dump(users_game_data, file, indent=8)

        await check_outcome(ctx)

    @commands.command(name='hit', description='Blackjack command: Hits')
    async def hit(self, ctx: commands.Context):
        user_id = str(ctx.message.author.id)
        if not game_active(ctx):
            await ctx.send("you havent started a blackjack game yet!\n"
                           "start one with `!blackjack <BetAmount>`", delete_after=5)
            return

        with open("json/blackjack.json", "r") as file:
            users_game_data = json.load(file)
            game_id = find_game_id(ctx)

        users_game_data[user_id][game_id]['player hand'] = \
            deal(users_game_data[user_id]["deck"], users_game_data[user_id][game_id]['player hand']['hand'], 1)
        users_game_data[user_id][game_id]['can double'] = False

        with open("json/blackjack.json", "w") as file:
            json.dump(users_game_data, file, indent=8)

        if not users_game_data[user_id][game_id]['doubled']:
            await check_outcome(ctx)

    @commands.command(name='double', description='Blackjack command: Doubles')
    async def double(self, ctx: commands.Context):
        user_id = str(ctx.message.author.id)
        if not game_active(ctx):
            await ctx.send("you havent started a blackjack game yet!\n"
                           "start one with `!blackjack <BetAmount>`", delete_after=5)
            return

        with open("json/blackjack.json", "r") as file:
            game_data = json.load(file)
            game_id = find_game_id(ctx)

        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        if not game_data[user_id][game_id]["can double"]:
            await ctx.send("too late to double the round now", delete_after=5)
            return

        if user_data[user_id]['points'] < game_data[user_id][game_id]["total bet"]:
            await ctx.send("you do not have enough points to double the bet.\n"
                           "brokie", delete_after=5)
            return

        edit_stats.add_points(ctx, -game_data[user_id][game_id]["total bet"])
        game_data[user_id][game_id]["doubled"] = True
        game_data[user_id][game_id]["total bet"] *= 2
        with open("json/blackjack.json", "w") as file:
            json.dump(game_data, file, indent=8)

        await self.hit(ctx)
        await check_outcome(ctx)
        with open("json/blackjack.json", "r") as file:
            game_data = json.load(file)

        if not game_data[user_id][game_id]["concluded"]:
            await self.stand(ctx)


async def create_game(ctx, amount: int):
    user_id = str(ctx.message.author.id)

    with open("json/blackjack.json", "r") as file:
        game_data = json.load(file)

    game_id = generate_game_id()
    game_data[user_id][game_id] = {
        "total bet": amount,
        "can double": True,
        "doubled": False,
        "stood": False,
        "dealer hand": deal(game_data[user_id]["deck"], [], 2),
        "player hand": deal(game_data[user_id]["deck"], [], 2),
        "concluded": False
    }

    with open("json/blackjack.json", "w") as file:
        json.dump(game_data, file, indent=8)

    return game_id


def deal(remaining_deck: list, current_hand: list, num_cards: int):
    for i in range(num_cards):
        random_card = random.choice(remaining_deck)
        current_hand.append(random_card)
        remaining_deck.remove(random_card)
    player_hand = {"hand": current_hand, "value": calculate_hand_value(current_hand)}
    return player_hand


def calculate_hand_value(hand: list):
    value = 0
    hand_copy = []

    for card in hand:
        hand_copy.append(card[:-1])

    for card in hand_copy:
        value += values[card]

    while value > 21 and hand_copy.count("A") > 0:
        hand_copy.remove("A")
        value -= 10

    return value


def game_active(ctx):
    user_id = str(ctx.message.author.id)
    with open("json/blackjack.json", "r") as file:
        game_data = json.load(file)

    try:
        for game in game_data[user_id]:
            if game == "deck":
                continue

            if not game_data[user_id][game]["concluded"]:
                return True

    except KeyError:
        return False

    return False


async def check_outcome(ctx: commands.Context):
    user_id = str(ctx.message.author.id)
    with open("json/blackjack.json", "r") as file:
        game_data = json.load(file)
        game_id = find_game_id(ctx)

    stood = game_data[user_id][game_id]['stood']
    bet_amount = game_data[user_id][game_id]['total bet']
    p_hand = game_data[user_id][game_id]['player hand']['hand']
    p_hand_val = game_data[user_id][game_id]['player hand']['value']
    d_hand = game_data[user_id][game_id]['dealer hand']['hand']
    d_hand_val = game_data[user_id][game_id]['dealer hand']['value']

    if stood:
        await ctx.send(f"dealer reveals his second card: {', '.join(d_hand)}\n"
                       f"dealer hand value: {d_hand_val}")
        await asyncio.sleep(1)
        while d_hand_val <= 16:
            game_data[user_id][game_id]['dealer hand'] = \
                deal(game_data[user_id]["deck"], game_data[user_id][game_id]['dealer hand']['hand'], 1)
            d_hand = game_data[user_id][game_id]['dealer hand']['hand']
            d_hand_val = game_data[user_id][game_id]['dealer hand']['value']
            await ctx.send(f"dealer hits: {', '.join(d_hand)}\n"
                           f"dealer hand value: {d_hand_val}")
            await asyncio.sleep(1)

    if p_hand_val > 21:
        await ctx.send(f"<@{user_id}>\n"
                       f"your hand: {', '.join(p_hand)}\n"
                       f"your hand value: {p_hand_val}\n\n"
                       "bust!\n"
                       f"you lost {bet_amount} points")
        game_data[user_id][game_id]["concluded"] = True
        with open("json/blackjack.json", "w") as file:
            json.dump(game_data, file, indent=8)

        await reshuffle(ctx)
        return

    if d_hand_val > 21:
        await ctx.send(f"<@{user_id}>\n"
                       f"your hand: {', '.join(p_hand)}\n"
                       f"your hand value: {p_hand_val}\n\n"
                       "dealer bust!\n"
                       f"you gained {bet_amount} points")
        edit_stats.add_points(ctx, 2 * bet_amount)
        game_data[user_id][game_id]["concluded"] = True
        with open("json/blackjack.json", "w") as file:
            json.dump(game_data, file, indent=8)

        await reshuffle(ctx)
        return

    if stood and d_hand_val == p_hand_val:
        await ctx.send(f"<@{user_id}>\n"
                       f"your hand: {', '.join(p_hand)}\n"
                       f"your hand value: {p_hand_val}\n\n"
                       "its a tie!\n"
                       f"you got your {bet_amount} points back")
        edit_stats.add_points(ctx, bet_amount)
        game_data[user_id][game_id]["concluded"] = True
        with open("json/blackjack.json", "w") as file:
            json.dump(game_data, file, indent=8)

        await reshuffle(ctx)
        return

    if p_hand_val == 21:
        await ctx.send(f"<@{user_id}>\n"
                       f"your hand: {', '.join(p_hand)}\n"
                       f"your hand value: {p_hand_val}\n\n"
                       f"{'natural blackjack' if check_natural(p_hand) else 'you win'}!\n"
                       f"you gained {bet_amount} points")
        edit_stats.add_points(ctx, 2 * bet_amount)
        game_data[user_id][game_id]["concluded"] = True
        with open("json/blackjack.json", "w") as file:
            json.dump(game_data, file, indent=8)

        await reshuffle(ctx)
        return

    if stood and 21 >= d_hand_val > 16 and d_hand_val > p_hand_val:
        await ctx.send(f"<@{user_id}>\n"
                       f"your hand: {', '.join(p_hand)}\n"
                       f"your hand value: {p_hand_val}\n\n"
                       f"{'dealer natural blackjack' if check_natural(d_hand) else 'dealer wins'}!\n"
                       f"you lost {bet_amount} points")
        game_data[user_id][game_id]["concluded"] = True
        with open("json/blackjack.json", "w") as file:
            json.dump(game_data, file, indent=8)

        await reshuffle(ctx)
        return

    if stood and d_hand_val < p_hand_val <= 21:
        await ctx.send(f"<@{user_id}>\n"
                       f"your hand: {', '.join(p_hand)}\n"
                       f"your hand value: {p_hand_val}\n\n"
                       f"you win!\n"
                       f"you gained {bet_amount} points")
        edit_stats.add_points(ctx, bet_amount * 2)
        game_data[user_id][game_id]["concluded"] = True
        with open("json/blackjack.json", "w") as file:
            json.dump(game_data, file, indent=8)

        await reshuffle(ctx)
        return

    if game_data[user_id][game_id]["doubled"]:
        return

    await ctx.send(f"<@{user_id}>\n"
                   f"your hand: {', '.join(p_hand)}\n"
                   f"your hand value: {p_hand_val}\n\n"
                   f"dealer hand: {d_hand[0]}, ??\n"
                   f"dealer hand value: {calculate_hand_value([d_hand[0]])}\n\n"
                   f"!hit or !stand?")


def generate_game_id():
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%&*"
    game_id = ""
    while len(game_id) < 6:
        game_id += random.choice(allowed)

    with open("json/blackjack.json", "r") as file:
        game_data = json.load(file)

    for user in game_data:
        if game_id in user:
            generate_game_id()

    return game_id


def check_natural(hand: list):
    stripped_hand = [x[:-1] for x in hand]
    return stripped_hand in naturals


def find_game_id(ctx):
    user_id = str(ctx.message.author.id)
    with open("json/blackjack.json", "r") as file:
        user_game_data = json.load(file)[user_id]

    for game in user_game_data:
        if game == "deck":
            continue

        if not user_game_data[game]["concluded"]:
            return game

    raise Exception("No game found")


async def reshuffle(ctx):
    user_id = str(ctx.message.author.id)
    with open("json/blackjack.json", "r") as file:
        game_data = json.load(file)

    if len(game_data[user_id]) > 3:
        game_id = list(game_data[user_id].items())[1][0]
        del game_data[user_id][game_id]

    if len(game_data[user_id]["deck"]) < len(deck) / 2:
        game_data[user_id]["deck"] = deck
        await ctx.send("reshuffled the cards")

    with open("json/blackjack.json", "w") as file:
        json.dump(game_data, file, indent=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(Blackjack(bot))
