import asyncio
import json
import random
import discord
import edit_stats

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

    def buy(self, makerid: int, num_points: float):
        add_holder(makerid)
        total_tokens: float = num_points / self.price
        self.buyable_supply -= total_tokens
        self.market_cap += num_points
        self.price = self.market_cap / self.total_supply

        with open("json/stonks.json", "w") as file:
            data = json.load(file)
            data[makerid]["holdings"][self.token_id] = {
                    "symbol": self.token_name,
                    "holding": total_tokens
                }

    def sell(self, makerid: int, num_tokens: float):
        with open("json/stonks.json", "r") as file:
            data = json.load(file)
        
        if num_tokens > data[makerid]["holdings"][self.token_id]["holding"]:
            return  # can't sell what you don't have 

        price_sold = num_tokens * self.price
        self.buyable_supply += num_tokens
        self.market_cap -= price_sold
        self.price = self.market_cap / self.total_supply

        data[makerid]["holdings"][self.token_id]["holding"] -= num_tokens
        data[makerid]["points"] += price_sold
        if data[makerid]["holdings"][self.token_id]["holding"] <= 0:
            del data[makerid]["holdings"][self.token_id]


class Stonks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # TODO commands to make: transfer, cashout, create_token, buy_token, sell_token, track_holdings, show_graph



def add_holder(id: int) -> none:
    with open("json/stonks.json", "r") as file:
        data = json.load(file)

    if id not in data:
        data[id] = {
                "points": 0,
                "holdings": {}
            }
    
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
    await bot.add_cog(Scrapers(bot))