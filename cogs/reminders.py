import asyncio
import json

import discord
from discord import app_commands
from discord.ext import commands

from cogs import scrapers, edit_stats as es

weekdays = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}


def get_trigger_reminder(current_day: int, current_time: str) -> bool:
    with open("json/stats.json", "r") as file:
        user_data = json.load(file)
    for user in user_data:
        for reminder in user_data[user]["reminders"]:
            if (current_day == user_data[user]["reminders"][reminder]["day"] and current_time ==
                    user_data[user]["reminders"]["reminder"]["time"]):
                return True

    return False


class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @app_commands.command(name="createreminder")
    async def create_reminder(self,
                              action: discord.Interaction,
                              name: str,
                              day: str,
                              time_hour: str,
                              time_min: str,
                              am_pm: str) -> None:

        with open("json/stats.json", "r") as file:
            user_data = json.load(file)[str(action.user.id)]

        if day not in weekdays:
            await action.response.send_message("`day` argument must be one of:\n"
                                               "`monday`, `tuesday`, `wednesday`, "
                                               "`thursday`, `friday`, `saturday`, or `sunday`")
            return

        if not time_hour.isdigit():
            await action.response.send_message("`time_hour` argument must be between 1 and 12")
            return

        time_hour = int(time_hour)
        if not (1 <= time_hour <= 12):
            await action.response.send_message("`time_hour` argument must be between 1 and 12")
            return

        if not time_min.isdigit():
            await action.response.send_message("`time_min` argument must be between 0 and 59")
            return

        time_min = int(time_min)
        if not (0 <= time_min <= 59):
            await action.response.send_message("`time_min` argument must be between 0 and 59")
            return

        if am_pm not in ["am", "pm"]:
            await action.response.send_message("`am_pm` argument must be one of `am` or `pm`")
            return

        time: str = f"{'0' if time_hour < 10 else ''}{time_hour}:{'0' if time_min < 10 else ''}{time_min} {am_pm}"
        user_data["reminders"][name] = {"day": weekdays[day], "time": time}
        await action.response.send_message(f"Reminder successfully set on {day} at {time}")
        es.edit_stats(await self.bot.get_context(action), str(action.user.id), _reminders=user_data["reminders"])

    @bot.event
    async def start_reminders(self):
        weather_time = "07:00 AM"
        channel_id = 1170131569747439747
        prayer, prayer_time = scrapers.get_athan_time()
        prayer_time_obj = datetime.datetime.strptime(prayer_time, "%I:%M %p").time()
        await self.bot.get_channel(channel_id).send(f"upcoming {prayer} athan at {prayer_time}")
        while (datetime.datetime.now().time().strftime("%H:%M") != prayer_time_obj.strftime("%H:%M")
               and datetime.datetime.now().time().strftime("%H:%M %p") != weather_time):
            await asyncio.sleep(45)

        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        if datetime.datetime.now().time().strftime("%H:%M") == prayer_time_obj.strftime("%H:%M"):
            for user in user_data:
                if user_data[user]["athan reminder"]:
                    gigachad = await self.bot.fetch_user(user)
                    await gigachad.send(
                        f"Ramadan Kareem!!\n"
                        f"{'gigachad' if user != '697855051779014796' else 'gigashort'},"  # if user isnt jana
                        f" {prayer} athan now at {prayer_time}"
                    )

        forecast = scrapers.weather_stats_today()
        if datetime.datetime.now().time().strftime("%H:%M %p") == weather_time:
            for user in user_data:
                if user_data[user]["weather updates"]:
                    gigachad = await self.bot.fetch_user(user)
                    await gigachad.send(
                        f"{'gigachad' if user != '697855051779014796' else 'gigashort'},"
                        f" here's today's weather forecast:\n\n{forecast}")

        await self.bot.get_channel(channel_id).send(f"{prayer} athan now at {prayer_time}")
        await asyncio.sleep(30)
        await self.start_reminders()


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
