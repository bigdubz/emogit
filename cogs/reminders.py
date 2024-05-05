import asyncio
import datetime
import json

import discord
from discord import app_commands
from discord.ext import commands

from cogs import scrapers, edit_stats as es

weekdays = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}


def get_trigger_reminder(prayer_time_obj, weather_time) -> bool:
    current_day = datetime.datetime.now().weekday()
    current_time = datetime.datetime.now().time().strftime("%H:%M %p")

    with open("json/stats.json", "r") as file:
        user_data = json.load(file)

    for user in user_data:
        for reminder in user_data[user]["reminders"]:
            if (current_day in user_data[user]["reminders"][reminder]["days"] and current_time in
                    user_data[user]["reminders"][reminder]["times"]):
                return True

    return (datetime.datetime.now().time().strftime("%H:%M") == prayer_time_obj.strftime("%H:%M") or
            datetime.datetime.now().time().strftime("%H:%M %p") == weather_time)


class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @app_commands.command(name="createreminder", description="Sets a custom reminder")
    async def create_reminder(self,
                              action: discord.Interaction,
                              name: str,
                              days: str,
                              times: str) -> None:

        with open("json/stats.json", "r") as file:
            user_data = json.load(file)[str(action.user.id)]

        days_list = days.split(",")
        for day in days_list:
            if day not in weekdays:
                await action.response.send_message("`day` argument must be one of:\n"
                                                   "`monday`, `tuesday`, `wednesday`, "
                                                   "`thursday`, `friday`, `saturday`, or `sunday`")
                return

        # Validate all times
        times_list = times.split(",")
        nums = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        for t in times_list:
            if (t[0] not in nums[:2] or t[1] not in nums or t[2] != ":" or t[3] not in nums[:6] or t[4] not in nums or
                    t[5:] not in [" AM", " PM"]):
                await action.response.send_message(
                    "`time` argument must be in the format HH:MM PP\n"
                    "eg. `07:15 AM`"
                )
                return

        user_data["reminders"][name] = {"days": list(map(lambda x: weekdays[x], days_list)), "times": times_list}
        await action.response.send_message(
            f"reminder {name} successfully set on {', '.join(days_list)} at {', '.join(times_list)}"
        )
        es.edit_stats(await self.bot.get_context(action), str(action.user.id), _reminders=user_data["reminders"])

    async def start_reminders(self):
        weather_time = "07:00 AM"
        prayer, prayer_time = scrapers.get_athan_time()
        prayer_time_obj = datetime.datetime.strptime(prayer_time, "%I:%M %p").time()

        # Main reminder check
        while True:
            if get_trigger_reminder(prayer_time_obj, weather_time):
                break
            await asyncio.sleep(30)

        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        if datetime.datetime.now().time().strftime("%H:%M") == prayer_time_obj.strftime("%H:%M"):
            for user in user_data:
                if user_data[user]["athan reminder"]:
                    gigachad = await self.bot.fetch_user(user)
                    await gigachad.send(
                        f"gigachad, {prayer} athan now at {prayer_time}"
                    )

        if datetime.datetime.now().time().strftime("%H:%M %p") == weather_time:
            for user in user_data:
                if user_data[user]["weather updates"]:
                    gigachad = await self.bot.fetch_user(user)
                    await gigachad.send(
                        f"{'gigachad' if user != '697855051779014796' else 'gigashort'},"
                        f" here's today's weather forecast:\n\n{scrapers.weather_stats_today()}")

        await self.send_reminder_messages()
        await asyncio.sleep(180)
        await self.start_reminders()

    async def send_reminder_messages(self) -> None:
        current_day = datetime.datetime.now().weekday()
        current_time = datetime.datetime.now().time().strftime("%H:%M %p")

        with open("json/stats.json", "r") as file:
            user_data = json.load(file)

        for user in user_data:
            for reminder in user_data[user]["reminders"]:
                if (current_day in user_data[user]["reminders"][reminder]["days"] and current_time in
                        user_data[user]["reminders"][reminder]["times"]):
                    gigachad = await self.bot.fetch_user(user)
                    await gigachad.send(f"{gigachad.name}, This is a reminder for {reminder}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
