import functools
import asyncio
import itertools
import random

import discord
import youtube_dl
from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

class YTDLSource(discord.PCMVolumeTransformer):
    ytdl_format_options = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': True,
        'quiet': False,
        'no_warnings': False,
        'default_search': 'auto',
        'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
    }

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise ValueError('Couldn\'t find anything that matches `{}`'.format(search))
        print(data)
        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                info = processed_info['entries'].pop(0)

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.ffmpeg_options), data=info)

class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx
        self.voice = None

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    @commands.command(name='join', invoke_without_subcommand=True)
    async def join(self, ctx: commands.Context):
        destination = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, url: str):
        if not ctx.voice_client:
            await ctx.invoke(self._join)

        async with ctx.typing():
            player = await YTDLSource.from_url(ctx, url, loop=self.bot.loop)
            ctx.voice_state.voice.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command(name='stream')
    async def stream(self, ctx: commands.Context, *, url: str):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command(name='volume')
    async def volume(self, ctx: commands.Context, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command(name='leave')
    async def leave(self, ctx: commands.Context):
        await ctx.voice_client.disconnect()

    @commands.command(name='stop')
    async def stop(self, ctx:commands.Context):
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            return
        
        await ctx.send("Currently not playing any song.")
        raise commands.CommandError("Music bot not playing a song.")

    @commands.command(name='pause')
    async def pause(self, ctx:commands.Context):
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            return
        
        await ctx.send("Currently not playing any song.")
        raise commands.CommandError("Music bot not playing a song.")

    @commands.command(name='resume')
    async def resume(self, ctx:commands.Context):
        if ctx.voice_client is not None and not ctx.voice_client.is_playing():
            ctx.voice_client.resume()
            return
        
        await ctx.send("Currently not playing any song.")
        raise commands.CommandError("Music bot not playing a song.")

    @play.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        if ctx.voice_client is None:
            if ctx.author.voice:
                ctx.voice_state.voice = await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()