import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

import json
import utils
from cogs import chatbot, edit_stats as eus
from cogs import scrapers as SC


load_dotenv()
auth = os.getenv('AUTH')
TOKEN = os.getenv('TOKEN')
LANG_DET = os.getenv('LANG_DET')
SERV_ID = int(os.getenv('PRIV_SERV'))
ID1 = int(os.getenv('ID1'))
ID2 = int(os.getenv('ID2'))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

song_data = {}


@bot.event
async def on_ready():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

    utils.delete_music(song_data)
    print('Ready')

    # This should always be executed last (because of infinite while loop)
    await bot.get_cog('Reminders').start_reminders()
            


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # TODO: fix
    # if ((str(message.author.id) == auth or message.author.id == ID2)
    #         and not message.content.startswith("!") and message.guild.id == SERV_ID):
    #     language = "es" if str(message.author.id) == auth else "de"
    #     a = message.content.replace('’', "\'")
    #     ctx = await bot.get_context(message)
    #     translated = GoogleTranslator(source=language, target='en').translate(a)
    #     if translated is not None and translated.lower() != a.lower():
    #         await ctx.send(translated)

    await bot.process_commands(message)

    # disabled for now
    await eus.count_message(message)
    await chatbot.record_words(message)
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
        await ctx.send("unauthorized")
        return

    synced = await bot.tree.sync()
    await ctx.send(f"synced {len(synced)} commands globally")


@bot.tree.command(name='commands', description='DMs you the currently available commands')
async def send_commands(action: discord.Interaction):
    embed = discord.Embed(title="Commands", description="", color=0x00ffff)
    embed.add_field(name="/join", value="Join sender's voice channel", inline=True)
    embed.add_field(name="/leave", value="Leave voice channel", inline=True)
    embed.add_field(name="/play", value="`/play <Song>`\nPlays first youtube video that pops up"
                                        " from the `<Song>` parameter", inline=True)
    embed.add_field(name="/stop", value="Stops playing music and clears queue", inline=True)
    embed.add_field(name="/clearq", value="Clears queue", inline=True)
    embed.add_field(name="/pause", value="Pauses the current song", inline=True)
    embed.add_field(name="/unpause", value="Resumes the current song", inline=True)
    embed.add_field(name="/queue", value="Shows current song queue", inline=True)
    embed.add_field(name="/skip", value="Skips to next song in queue", inline=True)
    embed.add_field(name="/playq", value="`/playq <NumFromQueue>`\nPlays a song from"
                                         " the queue", inline=True)
    embed.add_field(name="/remove", value="`/remove <NumFromQueue>`\nRemoves a song from queue", inline=True)
    embed.add_field(name="/points", value="Shows your current points", inline=True)
    embed.add_field(name="/level", value="Shows your current level", inline=True)
    embed.add_field(name="/claim", value="Claim your daily points", inline=True)
    embed.add_field(name="/donate", value="`/donate <UserMention> <Amount>`\n"
                                          "Gives the mentioned user `<Amount>` points from your account", inline=True)
    embed.add_field(name="/roll", value="`/roll <BetAmount>`\nGambles `<BetAmount>` points"
                                        " with a 50% chance of winning", inline=True)
    embed.add_field(name="/blackjack", value="`/blackjack <BetAmount>`\nStarts a game of blackjack against the bot with"
                                             " a bet of `<BetAmount>`", inline=True)
    embed.add_field(name="/athan", value="Toggle prayer athan reminders, sends you DMs at athan times", inline=True)
    embed.add_field(name="/catch", value="`/catch <UserMention> <BetAmount>`\n"
                                         "starts a catch game against `<UserMention>`"
                                         " with bet amount `<BetAmount>`", inline=True)
    embed.add_field(name="/createreminder", value="`/createreminder <Name> <Days> <times>`, "
                                                  "Sets a reminder with name `<Name>`, on the days `<Days>`"
                                                  "and at the times `<Times>`\n"
                                                  "Example usage: "
                                                  "`/createreminder jigglin 1,2 04:20 AM, 12:00 PM`\n"
                                                  "in this case, a reminder with name 'jigglin' was set on the days "
                                                  "tuesday and wednesday and will be triggered at"
                                                  " 04:20 AM and 12:00 PM.", inline=True)
    embed.add_field(name="/talk", value="or `!talk`\n`/talk <Message>`\n"
                                        "Sends a random message using the "
                                        "current server's word dictionary", inline=True)
    user = await bot.fetch_user(action.user.id)
    await user.send(embed=embed)
    await action.response.send_message("DM'd you the current bot commands", delete_after=5)


async def chatter(msg: discord.Message):
    try:
        guild_id = str(msg.guild.id)
    except AttributeError:
        return

    with open("json/words.json", "r") as file:
        data = json.load(file)

    if not data[guild_id]["chatter"]:
        return

    ctx = await bot.get_context(msg)
    if random.randint(0, 12) == 0:
        chat_bot: Chatbot = bot.get_cog('Chatbot')
        await chat_bot.talk(ctx, msg.content)


async def send_msg_to_athan_boys(msg: str):
    with open("json/stats.json") as file:
        user_data = json.load(file)
    
    for _id in user_data:
        if user_data[_id]["athan reminder"]:
            gigachad = await bot.fetch_user(_id)
            await gigachad.send(msg)


async def send_me_a_msg(msg: str):
    me = await bot.fetch_user(auth)
    await me.send(msg)


if __name__ == "__main__":
    bot.run(TOKEN)
