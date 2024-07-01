import asyncio
import json
import random
import discord

from cogs import edit_stats
from discord import app_commands
from discord.ext import commands


BASE_MARKET_CAP = 50  # points
INITIAL_SUPPLY = 1000000000


class Token:
    def __init__(self,
                 name: str,
                 dev_id: str,
                 dev_name: str,
                 contract_id: str,
                 holders: dict = {},
                 total_supply: int = INITIAL_SUPPLY,
                 market_capital: float = BASE_MARKET_CAP,
                 buyable_supply: float = INITIAL_SUPPLY,
                 ) -> None:
        self.name: str = name
        self.developer_id = dev_id
        self.developer_name = dev_name
        self.token_id: str = contract_id
        self.holders = holders
        self.total_supply: int = total_supply  # total tokens
        self.market_cap: float = market_capital  # costs this many points to create a token
        self.buyable_supply = buyable_supply  # supply remaining
        self.price = 0
        self.update_market_cap(0)


    def buy(self, makerid: int, num_points: float) -> float:
        with open("json/stonks.json", "r") as file:
            data = json.load(file)

        tokens_bought: float = num_points / self.price
        self.buyable_supply -= tokens_bought 
        self.update_market_cap(num_points)
        holder = makerid in self.holders


        alr_holding = 0 if not holder else data[makerid]['holdings'][self.token_id]['holding']
        data[makerid]['holdings'][self.token_id] = {
                "symbol": self.name,
                "holding": alr_holding + tokens_bought
            }
        data[makerid]['points'] -= num_points

        with open("json/stonks.json", "w") as file:
            json.dump(data, file, indent=4)

        if not holder:
            self.holders[makerid] = 0

        self.holders[makerid] += num_points

        add_token(self)
        return tokens_bought

    def sell(self, makerid: int, percent_of_holdings: float) -> float:
        with open("json/stonks.json", "r") as file:
            data = json.load(file)

        with open("json/tokens.json", "r") as file:
            tok_data = json.load(file)

        num_tokens = (percent_of_holdings/100)*data[makerid]['holdings'][self.token_id]['holding']
        self.buyable_supply += num_tokens

        points_sold = (percent_of_holdings/100)*self.holders[makerid]

        self.update_market_cap(-self.holders[makerid])  # remove invested capital by user
        price_sold = num_tokens * self.price  # calculate price after removing user capital invested
        self.update_market_cap(self.holders[makerid] - points_sold)  # re-add the capital invested and remove the points sold

        self.holders[makerid] -= points_sold
        if self.holders[makerid] == 0:
            del self.holders[makerid]

        data[makerid]["holdings"][self.token_id]["holding"] -= num_tokens
        data[makerid]["points"] += price_sold
        if data[makerid]["holdings"][self.token_id]["holding"] <= 0:
            del data[makerid]["holdings"][self.token_id]

        with open("json/stonks.json", "w") as file:
            json.dump(data, file, indent=4)

        add_token(self)
        return price_sold

    def update_market_cap(self, amount) -> None:
        self.market_cap += amount
        self.price = self.market_cap / self.total_supply * 1000


class Stonks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # TODO commands to make: sell_token, track_holdings, show_graph
    # TODO data validation (make sure everything is entered and is in correct format)
    @commands.command(name="transfer")
    async def transfer(self, ctx: commands.Context, amount):
        amount = int(amount)
        user_id = str(ctx.message.author.id)
        with open("json/stats.json", "r") as file:
            data = json.load(file)

        if amount <= 0 or amount > data[user_id]['points']:
            p = data[user_id]['points']
            await ctx.send(f"mate, you can only transfer up to {p} point{'s' if p > 1 else ''}. Brokie")
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
                       f"to crypto account. you're now holding {p} point{'s' if p > 1 else ''}.")


    @commands.command(name="cashout")
    async def cashout(self, ctx: commands.Context, amount):
        amount = int(amount)
        user_id = str(ctx.message.author.id)
        add_holder(user_id)
        with open("json/stonks.json", "r") as file:
            stonks = json.load(file)

        if amount <= 0 or amount > stonks[user_id]['points']:
            p = stonks[user_id]['points']
            await ctx.send(f"mate, you can only cash out up to {p} point{'s' if p > 1 else ''}. Brokie")
            return
        
        edit_stats.add_points(ctx, amount)
        stonks[user_id]['points'] -= amount

        with open("json/stonks.json", "w") as file:
            json.dump(stonks, file, indent=4)

        with open("json/stats.json", "r") as file:
            data = json.load(file)

        p = data[user_id]['points']
        await ctx.send(f"successfully cashed out {amount} point{'s' if amount > 1 else ''} "
                       f"to main account. you now have {p} point{'s' if p > 1 else ''}.")

    @commands.command(name="myholdings")
    async def holdings(self, ctx: commands.Context):
        user_id = str(ctx.message.author.id)
        add_holder(user_id)
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
                value = f"price: {round(tok_price*1000000000, -3)/1000000000}\n"
                        f"{round(info['holding'], 0)} total tokens owned\n"
                        f"worth {round(tok_price * info['holding'], 2)} points",
                inline = False
            )

        embed.add_field(name="Tokens Deving", value='\n'.join([tok for tok in data[user_id]['tokens deving']]))
        await ctx.send(embed=embed)

    @commands.command(name="createtoken")
    async def create_token(self, ctx: commands.Context, name: str):
        user_id = str(ctx.message.author.id)
        add_holder(user_id)
        token = Token(name, user_id, ctx.message.author.name, generate_id())
        await ctx.send(add_token(token, True))

    @commands.command(name="buy")
    async def buy_token(self, ctx: commands.Context, ca: str, amount_in_pts: str):
        user_id = str(ctx.message.author.id)
        add_holder(user_id)
        amount_in_pts = int(amount_in_pts)
        with open("json/stonks.json", "r") as file:
            data = json.load(file)
            
        p = data[user_id]['points']
        if amount_in_pts > p:
            await ctx.send(f"you're not rich enough pookie <3 (you have {p} point{'s' if p > 1 else ''})")
            return

        if amount_in_pts <= 0:
            await ctx.send("don't be retarded thanks :heart:")
            return

        with open("json/tokens.json", "r") as file:
            tok_data: dict = json.load(file)
            
        if ca not in tok_data:
            await ctx.send(f"no token with contract address \"{ca}\" exists. make sure you spelled the ca correctly")
            return

        token = construct_token(ca, tok_data[ca])
        tokens_bought = token.buy(user_id, amount_in_pts)
        await ctx.send(f"successfully bought {round(tokens_bought, 1)} tokens of {token.name}!")

    @commands.command(name="sell")
    async def sell_token(self, ctx: commands.Context, ca: str, percent_of_holdings: str):
        user_id = str(ctx.message.author.id)
        add_holder(user_id)
        percent_of_holdings = int(percent_of_holdings)
        with open("json/stonks.json", "r") as file:
            data = json.load(file)

        with open("json/tokens.json", "r") as file:
            tok_data: dict = json.load(file)

        if ca not in tok_data:
            await ctx.send(f"no token with contract address \"{ca}\" exists. make sure you spelled the ca correctly")
            return

        token = construct_token(ca, tok_data[ca])
        if ca not in data[user_id]['holdings']:
            await ctx.send(f"you don't own any {token.name}!")
            return 

        price_sold = token.sell(user_id, percent_of_holdings)
        await ctx.send(f"successfully sold {round(price_sold, 1)} points worth of {token.name}!")


def add_token(tok: Token, checks=False) -> str:
    with open("json/stonks.json", "r") as file:
        dev_data = json.load(file)

    if checks and dev_data[tok.developer_id]['points'] < BASE_MARKET_CAP:
        return "oh you poor thing. you need 50 points in your crypto account, "\
               "either transfer points via `!transfer` or find a job <3"


    with open("json/tokens.json", "r") as file:
        data: dict = json.load(file)
        if checks:
            for tk in data.values():
                if tk['name'] == tok.name:
                    return f"a token with name {tok.name} already exists!"
            
    data[tok.token_id] = {
        "name": tok.name,
        "dev": f"{tok.developer_name} ({tok.developer_id})",
        "total supply": tok.total_supply,
        "remaining supply": tok.buyable_supply,
        "market capital": tok.market_cap,
        "price": tok.price,
        "holders": tok.holders
    }

    if checks: 
        with open("json/stonks.json", "w") as file:
            dev_data[tok.developer_id]['points'] -= BASE_MARKET_CAP
            dev_data[tok.developer_id]['tokens deving'].append(f"{tok.name} (ca: \"{tok.token_id}\")")
            json.dump(dev_data, file, indent=4)

    with open("json/tokens.json", "w") as file:
        json.dump(data, file, indent=4)

    return f"successfully created \"{tok.name}\"! you can now buy it with `!buy \"{tok.name}\" <points to invest>`"
    

def add_holder(id: str) -> None:
    with open("json/stonks.json", "r") as file:
        data = json.load(file)

    if id not in data:
        data[id] = {
                "points": 0,
                "holdings": {},
                "tokens deving": []
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


def construct_token(ca: str, tok_data: dict) -> Token:
    ind = tok_data['dev'].find(' ')
    return Token(
        tok_data['name'],
        tok_data['dev'][ind+2: -1],
        tok_data['dev'][:ind],
        ca,
        tok_data['holders'],
        tok_data['total supply'],
        tok_data['market capital'],
        tok_data['remaining supply']
    )


async def setup(bot: commands.Bot):
    await bot.add_cog(Stonks(bot))