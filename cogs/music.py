import asyncio
import discord
import yt_dlp
import scrapers
import edit_stats as stats
import utils

from discord import app_commands
from discord.ext import commands
from yt_dlp_py import YTDLSource

song_queue = []
song_data = {}


class MusicBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.in_queue = False

    @commands.Cog.listener()
    async def on_song_end(self, ctx: commands.Context):
        while True:
            self.in_queue = True
            if len(song_queue) == 0:
                self.in_queue = False
                return

            try:
                voice = ctx.guild.voice_client
                if not voice.is_playing() and not voice.is_paused():
                    await self.play(ctx, song_queue[0][0], explicit_call=False)
                    song_queue.pop(0)
                    self.in_queue = False
                    return

            except (discord.errors.ClientException, yt_dlp.utils.DownloadError, AttributeError, KeyError):
                self.in_queue = False
                return

            await asyncio.sleep(5)

    @commands.hybrid_command(name='join', description='Join the user\'s voice channel')
    async def join(self, ctx: commands.Context):
        voice_client = ctx.guild.voice_client
        if voice_client:
            await ctx.send("already connected", delete_after=5)
            return

        if not ctx.message.author.voice:
            await ctx.send(f"retard <@{ctx.message.author.id}>."
                           f" you arent connected to a voice channel", delete_after=5)

        else:
            channel = ctx.message.author.voice.channel
            await channel.connect()
            await ctx.send(f"<@{ctx.message.author.id}> joined your channel", delete_after=5)

    @app_commands.command(name='leave', description='leave the current voice channel')
    async def leave(self, action: discord.Interaction):
        voice_client = action.guild.voice_client
        if voice_client and voice_client.is_connected():
            voice_client.stop()
            await voice_client.disconnect()
            await action.response.send_message(f"left the voice channel", delete_after=5)
            await asyncio.sleep(1)
            utils.delete_music(song_data)

        if not voice_client:
            await action.response.send_message(f"are you fucking stupid <@{action.user.id}>?", delete_after=5)

    @commands.hybrid_command(name='play', description='Searches for a song on youtube and plays it')
    async def play(self, ctx: commands.Context, search: str, explicit_call: bool = True):
        voice_client = ctx.guild.voice_client
        if not ctx.author.voice:
            await ctx.send(f"<@{ctx.author.id}> retard you arent connected to a voice channel", delete_after=5)
            return

        if not voice_client:
            await self.join(ctx)

        if not search:
            await ctx.send(f"<@{ctx.author.id}> play what nigga", delete_after=5)
            return

        voice_client = ctx.guild.voice_client
        url = scrapers.yt(search)
        if url not in song_data:
            await ctx.send("downloaded")
            filename, length = await YTDLSource.from_url(url, loop=self.bot.loop)
            length = 10 if length > 10 else length
            song_data[url] = (filename, length)

        if voice_client and voice_client.is_playing():
            song_queue.append(scrapers.yt(search, True))
            title = song_queue[-1][1]
            if not self.in_queue:
                await self.bot.loop.create_task(self.on_song_end(ctx))

            await ctx.send(f"<@{ctx.author.id}> added \"{title}\" to current song queue")
            if explicit_call:
                stats.add_points(ctx, song_data[url][1])

            return

        await ctx.send("now playing \"%s\"" % ' '.join(song_data[url][0][:-19].split('_')))
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=song_data[url][0]))
        if explicit_call:
            stats.add_points(ctx, song_data[url][1])

        song_data.pop(url)

    @commands.hybrid_command(name='stop', description='Stops music and clears queue')
    async def stop(self, ctx: commands.Context):
        voice_client = ctx.message.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            song_queue.clear()
            await ctx.send("stopped music and cleared queue", delete_after=5)
            await asyncio.sleep(1)
            utils.delete_music(song_data)

        elif voice_client and voice_client.is_paused():
            voice_client.resume()
            await self.stop(ctx)

        else:
            await ctx.message.channel.send("im not playing anything stupid", delete_after=5)

    @app_commands.command(name='pause', description='Pauses the bot\'s voice output')
    async def pause(self, action: discord.Interaction):
        voice_client = action.guild.voice_client
        if voice_client and voice_client.is_playing():
            await action.response.send_message("paused", delete_after=5)
            voice_client.pause()

        elif voice_client and voice_client.is_paused():
            return

        elif voice_client and not voice_client.is_playing():
            await action.response.send_message("im not playing anything retard", delete_after=5)

        else:
            await action.response.send_message("im not in a voice channel dumbass", delete_after=5)

    @app_commands.command(name='unpause', description='Resume the bot\'s voice output')
    async def unpause(self, action: discord.Interaction):
        voice_client = action.guild.voice_client
        if voice_client and voice_client.is_paused():
            await action.response.send_message("unpaused", delete_after=5)
            voice_client.resume()

        elif voice_client and not voice_client.is_playing():
            await action.response.send_message("im not playing anything dumbass", delete_after=5)

        elif voice_client and not voice_client.is_paused():
            await action.response.send_message("im not paused idiot", delete_after=5)

        else:
            await action.response.send_message("im not in a voice channel dumbass", delete_after=5)

    @app_commands.command(name='skip', description='Stops the current song and plays next song in queue')
    async def skip(self, action: discord.Interaction):
        if len(song_queue) == 0:
            await action.response.send_message("queue is empty", delete_after=5)
            return

        voice_client = action.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()

        else:
            await action.response.send_message("im not playing anything stupid", delete_after=5)
            return

        try:
            await self.play(await self.bot.get_context(action), song_queue[0][0], explicit_call=False)
            song_queue.pop(0)
            return

        except (discord.ClientException, yt_dlp.utils.DownloadError):
            return

    @app_commands.command(name='queue', description='Shows the current song queue')
    async def queue(self, action: discord.Interaction):
        if len(song_queue) < 1:
            embed = discord.Embed(title="queue is empty", description="", color=0x00ffff)
            await action.response.send_message(embed=embed, delete_after=5)
            return

        embed = discord.Embed(title="current song queue:", description="", color=0x00ffff)
        titles = [f"<@{action.user.id}> current song queue:"]
        for num, song in enumerate(song_queue):
            titles.append(f"{num + 1}- {song[1]}")
            embed.add_field(name=f"{num + 1}- {song[1]}", value="", inline=False)

        await action.response.send_message(embed=embed)

    @app_commands.command(name='clearq', description='Clears the current queue')
    async def clearq(self, ctx: discord.Interaction):
        await ctx.response.send_message("queue cleared", delete_after=5)
        song_queue.clear()

    @app_commands.command(name='remove', description='Removes a song from the current queue')
    async def remove(self, action: discord.Interaction, num: int):
        try:
            title = song_queue[int(num) - 1][1]
            song_queue.pop(int(num) - 1)
            await action.response.send_message(
                f"removed \"{title}\" from song queue\n`/queue` to view current queue", delete_after=5
            )

        except (ValueError, IndexError):
            await action.response.send_message(
                "type a fucking *number from the list*. actual brain damage", delete_after=5
            )
            return

    @commands.hybrid_command(name='playq', description='Skips current song and plays the specified song from the queue')
    async def playq(self, ctx: commands.Context, num: int):
        if not num:
            await ctx.send("`!pq <SongNumFromQueue>`", delete_after=5)
            return

        if len(song_queue) == 0:
            await ctx.send("queue is empty", delete_after=5)
            return

        voice_client = ctx.message.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()

        try:
            song = song_queue[int(num) - 1]
            await ctx.send(f"skipping to {song[1]}...")

            await self.play(ctx, song[0], explicit_call=False)
            if len(song_queue) > 0 and not self.in_queue:
                await self.bot.loop.create_task(self.on_song_end(ctx))

        except discord.ClientException:
            return

        except yt_dlp.utils.DownloadError:
            await self.playq(ctx, num)
            return

        except (TypeError, IndexError, ValueError):
            await ctx.send("type a fucking *number from queue list*. actual brain damage", delete_after=5)
            return

        song_queue.pop(int(num) - 1)


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicBot(bot))
