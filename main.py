import asyncio
import discord
from discord.ext import commands
import yt_dlp as youtube_dl
 # or import yt_dlp as youtube_dl if using yt-dlp

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

# FFmpeg options for audio streaming (no video)
FFMPEG_OPTIONS = {
    'options': '-vn'
}

# youtube_dl options: these settings ensure we get the best audio quality and disable playlist extraction.
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,  # Less console noise
    'extract_flat': 'in_playlist'
}

ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    """A class to create an audio source from a YouTube URL using youtube_dl."""
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
    
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        """
        Downloads or streams the audio from the provided URL.
        By default, it streams the content (download=False).
        """
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except Exception as e:
            raise Exception(f"Could not retrieve information from the provided URL. Details: {e}")
        
        # If a playlist is given, extract the first item.
        if 'entries' in data:
            data = data['entries'][0]
        
        # For streaming, get the direct URL; otherwise, prepare the filename.
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

# Set up the bot with a command prefix (here, "!")
intents = discord.Intents.default()
intents.message_content = True  # Enable if you are using discord.py 2.x and need to access message content
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot has logged in as {bot.user}')

@bot.command(name='play', help='Plays audio from a YouTube link. Usage: !play <YouTube URL>')
async def play(ctx, url: str):
    # Check if the user is connected to a voice channel
    if not ctx.author.voice:
        await ctx.send("🚫 You are not connected to a voice channel. Please join one and try again.")
        return

    voice_channel = ctx.author.voice.channel

    try:
        # Connect to the voice channel if not already connected
        if ctx.voice_client is None:
            await voice_channel.connect()
            await ctx.send(f"✅ Joined **{voice_channel}**")
        else:
            # If already connected, move to the user's channel (if different)
            if ctx.voice_client.channel != voice_channel:
                await ctx.voice_client.move_to(voice_channel)
                await ctx.send(f"🔄 Moved to **{voice_channel}**")
        
        # Inform the user that the bot is fetching the song
        processing_message = await ctx.send("🔍 Fetching the song, please wait...")

        # Get the audio source from the URL
        source = await YTDLSource.from_url(url, loop=bot.loop, stream=True)

        # Play the audio. The after callback will log any errors.
        ctx.voice_client.play(source, after=lambda error: print(f"Player error: {error}") if error else None)

        # Let the user know which song is playing
        await ctx.send(f"▶️ Now playing: **{source.title}**")
        await processing_message.delete(delay=1)

    except Exception as e:
        error_message = f"⚠️ An error occurred: {e}"
        await ctx.send(error_message)
        print(error_message)

@bot.command(name='stop', help='Stops the music and disconnects the bot from the voice channel.')
async def stop(ctx):
    try:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Disconnected from the voice channel.")
        else:
            await ctx.send("ℹ️ I am not connected to any voice channel.")
    except Exception as e:
        error_message = f"⚠️ An error occurred while trying to disconnect: {e}"
        await ctx.send(error_message)
        print(error_message)

# Run the bot using your token
bot.run('MTMzNjM1NzEyNDM1NTI2MDU0Nw.GW3mXP.9xpxiyJQS42Za8gDFe6xQs87M4O9-_bCUF8htk')

