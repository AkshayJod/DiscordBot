# Discord Music Bot with UI

A Discord music bot built with Python, discord.py, and yt-dlp. This bot can:

- Play high-quality audio from YouTube links.
- Join voice channels and play a custom `Start.mp3` sound when connecting.
- Play a custom `End.mp3` sound when leaving a voice channel.
- Respond to commands for pausing, resuming, and stopping audio.
- Optionally, offer a simple web dashboard UI using Flask.

## Features

- **Music Playback:** Stream high-quality YouTube audio using [yt-dlp](https://github.com/yt-dlp/yt-dlp).
- **Voice Channel Integration:**  
  - `!play <YouTube URL>`: The bot joins your voice channel, plays `Start.mp3` (if joining), then streams the audio.
  - `!hii`: The bot simply joins your voice channel and plays `Start.mp3`.
- **Playback Controls:**
  - `!pause`: Pauses current playback.
  - `!resume`: Resumes paused playback.
  - `!stop`: Stops the audio playback.
- **Exit Command:**
  - `!leave`: Stops any current audio, plays `End.mp3`, and disconnects from the voice channel.
- **Optional Web UI:** A basic Flask dashboard (see the `ui.py` file) that can be run alongside the bot.

## Prerequisites

- **Python 3.8+**
- **FFmpeg:** Must be installed and added to your system's PATH.
- **Discord Bot Token:** Create a bot via the [Discord Developer Portal](https://discord.com/developers/applications) and obtain your token.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/discord-music-bot.git
   cd discord-music-bot
