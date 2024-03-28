import datetime
import json
from random import choice

import requests
from bs4 import BeautifulSoup as bs
from discord.ext import commands

from cogs import edit_stats as eus


class Scrapers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='rdt', description='Sends a random post from the subreddit **owner only for now**')
    async def reddit(self, ctx: commands.Context, subreddit: str, limit: int = None):
        # if not await self.bot.is_owner(ctx.message.author):
        #     await ctx.send("unauthorized")
        #     return

        cost = 10
        user_id = str(ctx.message.author.id)

        with open("json/stats.json", "r") as file:
            raw_json = json.loads(' '.join(file.readlines()))

        if raw_json[user_id]["points"] < cost:
            await ctx.send(f"fucking poor, need {cost} points", delete_after=5)
            return

        url = f"https://www.reddit.com/r/{subreddit}/.json?limit={limit}"
        response = requests.get(url, headers={"User-Agent": subreddit})
        raw_json = json.loads(str(response.text))
        all_posts = []
        for post in raw_json["data"]["children"]:
            all_posts.append(f"{post['data']['title']} {post['data']['url']}")

        all_posts.pop(0)
        eus.add_points(ctx, -cost, override_id=user_id)
        await ctx.send(choice(all_posts))


def get_soup(search_url: str, syntax: str, tags: str, search: str = None, original_url: str = None):
    if search:
        search = search.split()
        search = syntax.join(search)
        url = search_url + search
    else:
        url = original_url
    response = requests.get(url)
    soup = bs(response.text, "html.parser")
    return soup.find_all(tags)


def yt(search: str, get_title: bool = False):
    raw_json = None
    for script in (get_soup("https://www.youtube.com/results?search_query=",
                            '+',
                            'script',
                            search)):
        if 'videoId' in str(script):
            raw_json = json.loads(str(script)[59:-10])
            break

    for x in (raw_json['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']
    ['contents'][0]['itemSectionRenderer']['contents']):

        # noinspection PyBroadException
        try:
            if get_title:
                title = x["videoRenderer"]["title"]["runs"][0]["text"]
                return 'https://www.youtube.com/watch?v=' + str(x["videoRenderer"]["videoId"]), title
            return 'https://www.youtube.com/watch?v=' + str(x["videoRenderer"]["videoId"])

        except BaseException:
            pass


def get_athan_time():
    url = "https://timesprayer.com/en/prayer-times-in-amman.html"
    response = requests.get(url)
    soup = bs(response.text, "html.parser")
    td = soup.find_all("td")[0:12]
    prayers = []
    times = []
    for i in range(0, 12):
        if i % 2 == 0 and i != 2:
            prayers.append(td[i].text.strip())

        elif i % 2 != 0 and i != 3:
            t = datetime.datetime.strptime(td[i].text.strip(), "%I:%M %p").time()
            t_obj = datetime.time(t.hour + 1 if t.hour + 1 < 24 else 0, t.minute)
            time = datetime.time.strftime(t_obj, "%I:%M %p")
            times.append(time)

    prayer_times = {key: val for key, val in zip(prayers, times)}
    for prayer, time in prayer_times.items():
        next_prayer_time = datetime.datetime.strptime(time, "%I:%M %p").time()
        if datetime.datetime.now().time() < next_prayer_time:
            return prayer, time

    return list(prayer_times.items())[0]


def weather_stats_today():
    url = "https://www.arabiaweather.com/en"
    response = requests.get(url)
    soup = bs(response.text, "html.parser")
    divs = [soup.find("div", class_=f"hourly-item hourly-item-{i} step-coming") for i in range(6)]
    temps = [soup.find("text", class_=f"ltr svg-temp temp-{i} svg-temp-coming").text for i in range(6)]
    data = {
        x.find("div", class_="hour-time").text: [x.find("div", class_="weather-box").find(
            "div", class_="status-icon-container").find("img").get("alt"), temps[i]] for i, x in enumerate(divs)
    }

    return '\n'.join(f"{key}: {', '.join(val)}" for key, val in data.items())


async def setup(bot: commands.Bot):
    await bot.add_cog(Scrapers(bot))
