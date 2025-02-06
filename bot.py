import asyncio
import discord
from discord.ext import commands
import os
import yt_dlp as youtube_dl  # Using yt-dlp for better YouTube support
from dotenv import load_dotenv  # For loading environment variables from .env file
load_dotenv()
secret_key = os.getenv('BOT_TOKEN')
# Suppress yt-dlp console messages
youtube_dl.utils.bug_reports_message = lambda: ''

# FFmpeg options for audio streaming (audio only)
FFMPEG_OPTIONS = {
    'options': '-vn'
}

# yt-dlp options: these settings ensure we get the best audio quality and disable playlist extraction.
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'extract_flat': 'in_playlist'
}

ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    """A class to create an audio source from a YouTube URL using yt-dlp."""
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
    
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except Exception as e:
            raise Exception(f"Could not retrieve information from the provided URL. Details: {e}")
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

# Set up the bot with a command prefix (here, "!")
intents = discord.Intents.default()
intents.message_content = True  # Required for discord.py 2.x if you want to access message content
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot has logged in as {bot.user}')

# Command to play YouTube audio (with Start.mp3 played first if joining the channel)
@bot.command(name='play', help='Joins voice channel, plays Start.mp3 (if joining) then plays audio from the provided YouTube URL.\nUsage: !play <YouTube URL>')
async def play(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("🚫 You are not connected to a voice channel. Please join one and try again.")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        try:
            voice_client = await voice_channel.connect()
            await ctx.send(f"✅ Joined **{voice_channel}**")
        except Exception as e:
            await ctx.send(f"⚠️ Could not join the voice channel: {e}")
            return

        def after_start(error):
            if error:
                print(f"Error during Start.mp3 playback: {error}")
            # After Start.mp3 finishes, start playing the YouTube audio.
            bot.loop.create_task(play_youtube(ctx, url))
        
        try:
            voice_client.play(discord.FFmpegPCMAudio("Start.mp3"), after=after_start)
        except Exception as e:
            await ctx.send(f"⚠️ Error playing Start.mp3: {e}")
            print(f"Error playing Start.mp3: {e}")
    else:
        await play_youtube(ctx, url)

async def play_youtube(ctx, url: str):
    """Fetches and plays YouTube audio after any prior audio finishes."""
    try:
        await ctx.send("🔍 Fetching the song, please wait...")
        source = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(source, after=lambda error: print(f"Player error: {error}") if error else None)
        await ctx.send(f"▶️ Now playing: **{source.title}**")
    except Exception as e:
        error_message = f"⚠️ An error occurred: {e}"
        await ctx.send(error_message)
        print(error_message)

# New command: !hii - joins voice channel and plays Start.mp3
@bot.command(name='hii', help='Joins your voice channel and plays Start.mp3.')
async def hii(ctx):
    if not ctx.author.voice:
        await ctx.send("🚫 You are not connected to a voice channel. Please join one and try again.")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        try:
            voice_client = await voice_channel.connect()
            await ctx.send(f"✅ Joined **{voice_channel}**")
        except Exception as e:
            await ctx.send(f"⚠️ Could not join the voice channel: {e}")
            return
    else:
        voice_client = ctx.voice_client

    try:
        # Stop any currently playing audio before playing Start.mp3.
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        voice_client.play(discord.FFmpegPCMAudio("Start.mp3"))
        await ctx.send("🎶 Playing Start.mp3!")
    except Exception as e:
        await ctx.send(f"⚠️ Error playing Start.mp3: {e}")
        print(f"Error playing Start.mp3: {e}")

@bot.command(name='pause', help='Pauses the current audio playback.')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused the audio.")
    else:
        await ctx.send("ℹ️ No audio is playing to pause.")

@bot.command(name='resume', help='Resumes the paused audio playback.')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed the audio.")
    else:
        await ctx.send("ℹ️ No audio is paused.")

@bot.command(name='stop', help='Stops the current audio playback.')
async def stop(ctx):
    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        ctx.voice_client.stop()
        await ctx.send("⏹️ Stopped the audio playback.")
    else:
        await ctx.send("ℹ️ No audio is playing to stop.")

@bot.command(name='leave', help='Stops any current audio, plays End.mp3, and disconnects the bot from the voice channel.')
async def leave(ctx):
    if ctx.voice_client:
        
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()

        def after_end(error):
            if error:
                print(f"Error during End.mp3 playback: {error}")
            fut = asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(f"Error disconnecting: {e}")

        try:
            ctx.voice_client.play(discord.FFmpegPCMAudio("End.mp3"), after=after_end)
            await ctx.send("👋 Playing end sound and disconnecting...")
        except Exception as e:
            await ctx.send(f"⚠️ Error playing End.mp3: {e}")
            print(f"Error playing End.mp3: {e}")
    else:
        await ctx.send("ℹ️ I am not connected to any voice channel.")

# Run the bot using your token (replace 'YOUR_BOT_TOKEN' with your actual token)
bot.run(secret_key)
