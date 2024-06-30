import asyncio
import json
import random
import discord

from cogs import edit_stats
from discord import app_commands
from discord.ext import commands


class Token:
    def __init__(self, name: str):
        self.token_name: str = name
        self.token_id: str = generate_id()
        self.total_supply: float = 10000  # total tokens
        self.market_cap: float = 200  # starts with initial 200 points (costs 200 points to start a token)
        self.buyable_supply = self.total_supply  # supply remaining
        self.price: float = self.market_cap / self.total_supply

    def buy(self, makerid: int, num_points: float) -> None:
        add_holder(makerid)
        total_tokens: float = num_points / self.price
        self.buyable_supply -= total_tokens
        update_market_cap(num_points)

        with open("json/stonks.json", "w") as file:
            data = json.load(file)
            data[makerid]["holdings"][self.token_id] = {
                    "symbol": self.token_name,
                    "holding": total_tokens
                }
            json.dump(data, file, indent=4)

    def sell(self, makerid: int, percent_of_holdings: float) -> None:
        with open("json/stonks.json", "r") as file:
            data = json.load(file)

        num_tokens = (percent_of_holdings/100)*data[makerid]['holdings'][self.token_id]['holding']
        price_sold = num_tokens * self.price
        self.buyable_supply += num_tokens
        update_market_cap(-price_sold)

        data[makerid]["holdings"][self.token_id]["holding"] -= num_tokens
        data[makerid]["points"] += price_sold
        if data[makerid]["holdings"][self.token_id]["holding"] <= 0:
            del data[makerid]["holdings"][self.token_id]

        with open("json/stonks.json", "w") as file:
            json.dump(data, file, indent=4)

    def update_market_cap(self, amount) -> None:
        self.market_cap += amount
        self.price = self.market_cap / self.total_supply


class Stonks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # TODO commands to make: create_token, buy_token, sell_token, track_holdings, show_graph
    @commands.command(name="transfer")
    async def transfer(self, ctx: commands.Context, amount):
        amount = int(amount)
        user_id = str(ctx.message.author.id)
        with open("json/stats.json", "r") as file:
            data = json.load(file)

        if amount <= 0 or amount > data[user_id]['points']:
            p = data[user_id]['points']
            await ctx.send(f"mate, you can only transfer up to "
                           f"{p} point{'s' if p > 1 else ''}. Brokie")
            return
        
        add_holder(user_id)
        with open("json/stonks.json", "r") as file:
            stonks = json.load(file)
            
        edit_stats.add_points(ctx, -amount)
        stonks[user_id]['points'] += amount

        with open("json/stonks.json", "w") as file:
            json.dump(stonks, file, indent=4)

        p = stonks[user_id]['points']
        await ctx.send(f"successfully transfered {amount} point{'s' if amount > 1 else ''} "
                       f"to crypto account. you're now holding "
                       f"{p} point{'s' if p > 1 else ''}.")


    @commands.command(name="cashout")
    async def cashout(self, ctx: commands.Context, amount):
        amount = int(amount)
        user_id = str(ctx.message.author.id)
        add_holder(user_id)
        with open("json/stonks.json", "r") as file:
            stonks = json.load(file)

        if amount <= 0 or amount > stonks[user_id]['points']:
            p = stonks[user_id]['points']
            await ctx.send(f"mate, you can only cash out up to "
                           f"{p} point{'s' if p > 1 else ''}. Brokie")
            return
        
        edit_stats.add_points(ctx, amount)
        stonks[user_id]['points'] -= amount

        with open("json/stonks.json", "w") as file:
            json.dump(stonks, file, indent=4)

        with open("json/stats.json", "r") as file:
            data = json.load(file)

        p = data[user_id]['points']
        await ctx.send(f"successfully cashed out {amount} point{'s' if amount > 1 else ''} "
                       f"to main account. you now have "
                       f"{p} point{'s' if p > 1 else ''}.")

    @commands.command(name="myholdings")
    async def holdings(self, ctx: commands.Context):
        user_id = str(ctx.message.author.id)
        username = ctx.message.author.name
        with open("json/stonks.json", "r") as file:
            data: dict = json.load(file)

        points = data[user_id]['points']
        embed = discord.Embed(title=f"{username}'s holdings", description="", color=0x00ffff)
        embed.add_field(name="Crypto account points", value=points, inline=False)

        with open("json/tokens.json", "r") as file:
            token_data = json.load(file)

        for tok_id, info in data[user_id]['holdings'].items():
            tok_price = token_data[tok_id]['price']
            embed.add_field(
                name = info['symbol'],
                value = f"price: {tok_price}\n"
                        f"{info['holding']} total tokens owned\n"
                        f"worth {tok_price * info['holding']} points",
                inline = False
            )

        await ctx.send(embed=embed)
            


def add_holder(id: str) -> None:
    with open("json/stonks.json", "r") as file:
        data = json.load(file)

    if id not in data:
        data[id] = {
                "points": 0,
                "holdings": {}
            }

        with open("json/stonks.json", "w") as file:
            json.dump(data, file, indent=4)
    
    return


def generate_id() -> str:
    chars = "abcdefghijklmnopqrstuvwxyz1234567890"
    token_id = ""
    while len(token_id) < 10:
        token_id += random.choice(chars)

    with open("json/stonks.json", "r") as file:
        data = json.load(file)

    for user in data:
        if token_id in user:
            return generate_id()

    return token_id


async def setup(bot: commands.Bot):
    await bot.add_cog(Stonks(bot))