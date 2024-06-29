import json
import random
import discord

from discord import app_commands
from discord.ext import commands

allowed_characters = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
                      "<@1234567890>"
                      "")

blacklist = ["allah", "islam", "muslim", "god", "athan", "allahu", "amna", "aya",
             ">m", ">rs", ">osu", ">c", "s", "k", "q", "r", "e", "t", "y", "u",
             "o", "p", "d", "f", "g", "h", "j", "l", "m", "n", "z", "x", "c",
             "v", "b", "Q", "E", "R", "T", "Y", "U", "O", "P", "S", "D", "F",
             "G", "H", "J", "K", "L", "Z", "X", "C", "V", "B", "N", "M"]


async def record_words(msg: discord.Message):
    message: str = msg.content
    try:
        guild_id = str(msg.guild.id)
    except AttributeError:
        print(f"\n================================\n\n"
              f"{msg.author.name} sent a DM to the bot: \"{message}\""
              f"\n\n================================\n")
        return

    if not message.startswith("!talk") and message.startswith("!"):
        return

    elif message.startswith("!talk"):
        message = message[6:]

    for letter in message:
        if letter not in allowed_characters:
            message = message.replace(letter, "")

    message_list = message.split()
    index = 0
    for word in message_list:
        if word.lower() in blacklist:
            message_list.remove(word)

        elif not word.isupper():
            message_list.remove(word)
            message_list.insert(index, word.lower())

        index += 1

    with open("json/words.json", "r") as file:
        all_data = json.load(file)

    if guild_id not in all_data:
        all_data[guild_id] = {"chatter": False, "phrases": {}, "words": []}

    new_words = set(message_list) - set(all_data[guild_id]["words"])
    all_data[guild_id]["words"] = sorted(list(set(all_data[guild_id]["words"]) | set(message_list)))

    with open("json/words.json", "w") as file:
        json.dump(all_data, file, indent=4, sort_keys=True)

    add_phrase_records(msg, new_words)
    set_good_words(msg, message_list)


def set_good_words(message: discord.Message, sentence: list):
    guild_id = str(message.guild.id)
    with open("json/words.json", "r") as file:
        all_data = json.load(file)

    for index in range(len(sentence)):
        try:
            if sentence[index + 1] not in all_data[guild_id]["phrases"][sentence[index]]["good"]:
                all_data[guild_id]["phrases"][sentence[index]]["good"].append(sentence[index + 1])
                all_data[guild_id]["phrases"][sentence[index]]["good"].sort()

        except IndexError:
            continue

    with open("json/words.json", "w") as file:
        json.dump(all_data, file, indent=4, sort_keys=True)


def add_phrase_records(message: discord.Message, new_words: set):
    guild_id = str(message.guild.id)
    with open("json/words.json", "r") as file:
        all_data = json.load(file)

    for word in new_words:
        all_data[guild_id]["phrases"][word] = {"good": [], "bad": [word]}

    with open("json/words.json", "w") as file:
        json.dump(all_data, file, indent=4, sort_keys=True)


class Chatbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='talk',
                             description='Generate random messages from the current server based on sentence length')
    async def talk(self, ctx: commands.Context, sentence: str):
        guild_id = str(ctx.message.guild.id)
        user_id = str(ctx.message.author.id)
        with open("json/words.json", "r") as file:
            all_data = json.load(file)

        sentence_length = len(sentence.split())
        message = []
        message_length = random.randint(sentence_length, sentence_length + 10)
        for x in range(message_length):
            try:
                while True:
                    random_word = random.choice(all_data[guild_id]["phrases"][message[x - 1]]["good"])
                    if random_word not in all_data[guild_id]["phrases"][message[x - 1]]["bad"]:
                        message.append(random_word)
                        break

            except IndexError:
                if x == 0:
                    message.append(random.choice(all_data[guild_id]["words"]))

                else:
                    while True:
                        random_word = random.choice(all_data[guild_id]["words"])
                        if random_word not in all_data[guild_id]["phrases"][message[x - 1]]["bad"]:
                            message.append(random_word)
                            break

        message = ' '.join(message)
        await ctx.send(f"<@{user_id}> {message}")

    @commands.hybrid_command(name='bad', description='Sets a bad phrase **owner only**')
    async def set_bad_phrase(self, ctx: commands.Context, phrase: str):
        if not await self.bot.is_owner(ctx.message.author):
            await ctx.send("unauthorized")
            return

        phrase = phrase.split(" ")
        guild_id = str(ctx.guild.id)
        with open("json/words.json", "r") as file:
            all_words = json.load(file)

        try:
            all_words[guild_id]["phrases"][phrase[0]]["bad"].append(phrase[1])
            all_words[guild_id]["phrases"][phrase[0]]["bad"].sort()
            all_words[guild_id]["phrases"][phrase[0]]["good"].remove(phrase[1])
            all_words[guild_id]["phrases"][phrase[0]]["good"].sort()
            await ctx.send(f"removed phrase \"{phrase[0]} {phrase[1]}\"")
        except KeyError:
            await ctx.send(f"the phrase \"{phrase[0]} {phrase[1]}\" does not exist in the database")

        with open("json/words.json", "w") as file:
            json.dump(all_words, file, indent=4, sort_keys=True)

    @app_commands.command(name='delete', description='Deletes a word from server dictionary **owner only**')
    async def delete_word(self, action: discord.Interaction, word: str):
        if not await self.bot.is_owner(action.user):
            await action.response.send_message("unauthorized")
            return

        guild_id = str(action.guild.id)
        with open("json/words.json", "r") as file:
            all_words = json.load(file)

        try:
            all_words[guild_id]["words"].remove(word)
            del all_words[guild_id]["phrases"][word]

        except ValueError:
            await action.response.send_message(f"\"{word}\" not found in dictionary", delete_after=5)
            return

        for phrase in all_words[guild_id]["phrases"]:
            if word in all_words[guild_id]["phrases"][phrase]["good"]:
                all_words[guild_id]["phrases"][phrase]["good"].remove(word)

            if word in all_words[guild_id]["phrases"][phrase]["bad"]:
                all_words[guild_id]["phrases"][phrase]["bad"].remove(word)

        await action.response.send_message(f"\"{word}\" deleted from dictionary", delete_after=5)
        with open("json/words.json", "w") as file:
            json.dump(all_words, file, indent=4, sort_keys=True)

    @app_commands.command(
        name='chatter',
        description='Enables auto chatter mode, occasionally sends messages to the server **owner only**'
    )
    async def enable(self, action: discord.Interaction):
        if not await self.bot.is_owner(action.user):
            await ctx.send("unauthorized")
            return

        guild_id = str(action.guild.id)
        with open("json/words.json", "r") as file:
            all_words = json.load(file)

        all_words[guild_id]["chatter"] = not all_words[guild_id]["chatter"]
        msg = "auto chatter toggled on" if all_words[guild_id]["chatter"] else "auto chatter toggled off"
        await action.response.send_message(msg)
        with open("json/words.json", "w") as file:
            json.dump(all_words, file, indent=4, sort_keys=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Chatbot(bot))
