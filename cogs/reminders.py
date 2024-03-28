import json

import discord
from discord import app_commands
from discord.ext import commands

from cogs import edit_stats as es

weekdays = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}


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
            user_data = json.load(file)[action.user.id]

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

        user_data["reminders"][name] = {
            "day": weekdays[day],
            "time": f"{'0' if time_hour < 10 else ''}{time_hour}:{'0' if time_min < 10 else ''}{time_min} {am_pm}"
        }
        es.edit_stats(await self.bot.get_context(action), _reminders=user_data["reminders"])


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
