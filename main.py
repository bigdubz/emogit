import os
import random

import discord
from discord.ext import commands

import json
import utils
from cogs import chatbot, edit_stats as eus

TOKEN = "MTEzNjQ2NzYzNDM1NTk2NjAxNQ.GT_knh.-RTm2dklcqHMM8vDjwwoGEbphvEeQjClShBBpE"
intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

auth = "451301920364167179"
song_queue = []
song_data = {}


@bot.event
async def on_ready():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

    utils.delete_music(song_data)
    print('Ready')

    # This should always be executed last
    await bot.get_cog('Reminders').start_reminders()


@bot.event
async def on_message(message):
    if str(message.author.id) == "1136467634355966015":
        return

    if message.author.bot:
        return

    await chatbot.record_words(message)
    await eus.count_message(message)
    await bot.process_commands(message)
    await chatter(message)


@bot.tree.command(name='clear', description='Deletes messages **owner only**')
async def clear(action: discord.Interaction, amount: int):
    if not await bot.is_owner(action.user):
        await action.response.send_message("unauthorized")
        return

    await action.response.send_message(f"deleted {amount} message{'s' if amount > 1 else ''}", delete_after=5)
    channel = bot.get_channel(action.channel.id)
    messages = [msg async for msg in channel.history(limit=amount + 1)]
    await channel.delete_messages(messages)


@bot.command(name='sync', description='Syncs all commands globally **owner only**')
async def sync(ctx: discord.ext.commands.Context):
    if not await bot.is_owner(ctx.message.author):
        await action.response.send_message("unauthorized")
        return

    synced = await bot.tree.sync()
    await ctx.send(f"synced {len(synced)} commands globally")


@bot.tree.command(name='commands', description='DMs you the currently available commands')
async def send_commands(action: discord.Interaction):
    embed = discord.Embed(title="Commands", description="", color=0x00ffff)
    embed.add_field(name="!join", value="Join sender's voice channel", inline=True)
    embed.add_field(name="!leave", value="Leave voice channel", inline=True)
    embed.add_field(name="!play", value="or `!p`\n`!play <Song>`\nPlays first youtube video that pops up"
                                        " from the `<Song>` parameter", inline=True)
    embed.add_field(name="!stop", value="Stops playing music and clears queue", inline=True)
    embed.add_field(name="!clearq", value="Clears queue", inline=True)
    embed.add_field(name="!pause", value="Pauses the current song", inline=True)
    embed.add_field(name="!unpause", value="or `!resume`\nResumes the current song", inline=True)
    embed.add_field(name="!queue", value="Shows current song queue", inline=True)
    embed.add_field(name="!skip", value="Skips to next song in queue", inline=True)
    embed.add_field(name="!playq", value="or `!pq`\n`!playq <NumFromQueue>`\nPlays a song from"
                                         " the queue", inline=True)
    embed.add_field(name="!remove", value="`!remove <NumFromQueue>`\nRemoves a song from queue", inline=True)
    embed.add_field(name="!points", value="or `!pts`\nShows your current points", inline=True)
    embed.add_field(name="!level", value="Shows your current level", inline=True)
    embed.add_field(name="!claim", value="Claim your daily points", inline=True)
    embed.add_field(name="!give", value="or `!donate`\n`!give <UserMention> <Amount>`\n"
                                        "Gives the mentioned user `<Amount>` points from your account", inline=True)
    embed.add_field(name="!roll", value="or `!bet`\n`!roll <BetAmount>`\nGambles `<BetAmount>` points"
                                        " with a 50% chance of winning", inline=True)
    embed.add_field(name="!blackjack", value="or `!bj`\n`!blackjack <BetAmount>`\nStarts a game of blackjack with "
                                             "a bet of `<BetAmount>`!", inline=True)
    embed.add_field(name="!athan", value="or `!reminders`\nToggle prayer athan reminders, "
                                         "sends you DMs at athan times", inline=True)
    embed.add_field(name="!cmiyc", value="or `!catch`\n`!cmiyc <UserMention> <BetAmount>`\n"
                                         "starts a catch game against `<UserMention>`"
                                         " with bet amount `<BetAmount>`", inline=True)
    user = await bot.fetch_user(action.user.id)
    await user.send(embed=embed)
    await action.response.send_message("DMed you the current bot commands", delete_after=5)


async def chatter(msg: discord.Message):
    guild_id = str(msg.guild.id)
    with open("json/words.json", "r") as file:
        data = json.load(file)

    if not data[guild_id]["chatter"]:
        return

    ctx = await bot.get_context(msg)
    if random.randint(0, 12) == 0:
        chat_bot: Chatbot = bot.get_cog('Chatbot')
        await chat_bot.talk(ctx, msg.content)


if __name__ == "__main__":
    bot.run(TOKEN)
