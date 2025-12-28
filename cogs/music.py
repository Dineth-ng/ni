import discord
from discord.ext import commands
from discord import ui
import yt_dlp
import asyncio
import shutil
import sys
import os
import datetime
import random

# --- Data Classes ---

class Song:
    def __init__(self, source, data, requester):
        self.source = source
        self.data = data
        self.requester = requester
        self.title = data.get('title')
        self.url = data.get('url')
        self.web_url = data.get('webpage_url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader')

    def create_embed(self, status="Playing"):
        duration_str = str(datetime.timedelta(seconds=self.duration)) if self.duration else "Unknown"
        embed = discord.Embed(
            title=self.title,
            url=self.web_url,
            color=discord.Color.blue()
        )
        embed.set_author(name=f"Now {status}", icon_url="https://cdn.discordapp.com/emojis/866030999557242880.webp?size=96&quality=lossless")
        embed.set_thumbnail(url=self.thumbnail)
        embed.add_field(name="Author", value=self.uploader, inline=True)
        embed.add_field(name="Duration", value=duration_str, inline=True)
        embed.add_field(name="Requested by", value=self.requester.mention, inline=True)
        embed.set_footer(text=f"Antigravity Music System • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return embed

class MusicQueue:
    def __init__(self):
        self._queue = []
        self._history = []
        self.loop = False # False, 'track', 'queue'
        self.current_song = None
        self.interaction_message = None
        self.volume = 1.0

    def add(self, song):
        self._queue.append(song)

    def next(self):
        # Handle Loop Track
        if self.loop == 'track' and self.current_song:
            return self.current_song

        # Handle Loop Queue
        if self.loop == 'queue' and self.current_song:
            self._queue.append(self.current_song)

        # Add current to history before moving on
        if self.current_song:
            self._history.append(self.current_song)
            if len(self._history) > 10: # keep history small
                self._history.pop(0)

        if not self._queue:
            self.current_song = None
            return None
        
        self.current_song = self._queue.pop(0)
        return self.current_song

    def prev(self):
        if not self._history:
            return None
        # Push current back to queue (if exists) to not lose it
        if self.current_song:
            self._queue.insert(0, self.current_song)
        
        self.current_song = self._history.pop()
        return self.current_song

    def shuffle(self):
        random.shuffle(self._queue)

    def clear(self):
        self._queue = []
        self._history = []
        self.current_song = None

# --- UI Components ---

class FilterSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="None", description="No effects", value="none", emoji="❌"),
            discord.SelectOption(label="Nightcore", description="Speed up and higher pitch", value="nightcore", emoji="🌙"),
            discord.SelectOption(label="Bass Boost", description="Boost that bass!", value="bass", emoji="🔊"),
            discord.SelectOption(label="Vaporwave", description="Slow and chill", value="vaporwave", emoji="🌊"),
            discord.SelectOption(label="8D", description="Rotating audio", value="8d", emoji="🎧")
        ]
        super().__init__(placeholder="Select Audio Filter...", min_values=1, max_values=1, options=options, row=3)

    async def callback(self, interaction: discord.Interaction):
        # Placeholder for filter logic
        await interaction.response.send_message(f"Selected filter: **{self.values[0]}** (Note: Filters require ffmpeg restart - Placeholder)", ephemeral=True)

class MusicPlayerView(ui.View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=None)
        self.cog = cog
        self.ctx = ctx
        self.add_item(FilterSelect())

    def _get_queue(self):
        return self.cog.get_queue(self.ctx.guild.id)

    # --- Row 1 ---
    @ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def previous(self, interaction: discord.Interaction, button: ui.Button):
        queue = self._get_queue()
        if not queue._history:
             return await interaction.response.send_message("No history available.", ephemeral=True)
        
        # Stop current, logic in 'prev' handled by queue, but we need to trigger play_prev specifically or manipulate queue
        # For simplicity, we'll manually manipulate and stop.
        # But 'after' callback in play_next handles 'next'. We need a way to tell it to go 'prev'.
        # Complex. For now, let's just say "Previous not fully supported in this version" or implement a hack.
        await interaction.response.send_message("Previous track not supported yet (Requires playback state reset).", ephemeral=True)

    @ui.button(emoji="⏪", style=discord.ButtonStyle.secondary, row=0, disabled=True)
    async def rewind(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Rewind not supported.", ephemeral=True)

    @ui.button(emoji="⏯️", style=discord.ButtonStyle.primary, row=0)
    async def pause_resume(self, interaction: discord.Interaction, button: ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            if vc.is_paused():
                vc.resume()
                await interaction.response.send_message("Resumed! ▶️", ephemeral=True)
            else:
                vc.pause()
                await interaction.response.send_message("Paused! ⏸️", ephemeral=True)

    @ui.button(emoji="⏩", style=discord.ButtonStyle.secondary, row=0)
    async def skip(self, interaction: discord.Interaction, button: ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("Skipped! ⏭️", ephemeral=True)

    @ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def next_track(self, interaction: discord.Interaction, button: ui.Button):
        # Alias for skip
        await self.skip(interaction, button)


    # --- Row 2 ---
    @ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle(self, interaction: discord.Interaction, button: ui.Button):
        queue = self._get_queue()
        queue.shuffle()
        await interaction.response.send_message("Queue shuffled! 🎲", ephemeral=True)

    @ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, row=1)
    async def loop_mode(self, interaction: discord.Interaction, button: ui.Button):
        queue = self._get_queue()
        if not queue.loop:
            queue.loop = 'queue'
            button.style = discord.ButtonStyle.green
            msg = "Looping Queue 🔁"
        elif queue.loop == 'queue':
            queue.loop = 'track'
            button.style = discord.ButtonStyle.blurple
            msg = "Looping Track 🔂"
        else:
            queue.loop = False
            button.style = discord.ButtonStyle.secondary
            msg = "Loop Disabled"
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(msg, ephemeral=True)

    @ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, row=1)
    async def stop(self, interaction: discord.Interaction, button: ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            self._get_queue().clear()
            vc.stop()
            await interaction.response.send_message("Stopped. ⏹️", ephemeral=True)

    @ui.button(emoji="📜", style=discord.ButtonStyle.secondary, row=1)
    async def show_queue(self, interaction: discord.Interaction, button: ui.Button):
        queue = self._get_queue()
        if not queue._queue:
            content = "Queue is empty."
        else:
            fmt = "\n".join([f"{i+1}. {s.title}" for i, s in enumerate(queue._queue[:10])])
            content = f"**Queue ({len(queue._queue)}):**\n{fmt}"
        await interaction.response.send_message(content, ephemeral=True)
    
    @ui.button(emoji="📄", style=discord.ButtonStyle.secondary, row=1)
    async def lyrics(self, interaction: discord.Interaction, button: ui.Button):
        time = datetime.datetime.now().strftime("%Y")
        await interaction.response.send_message(f"Lyrics System (c) {time} - Feature coming soon!", ephemeral=True)


    # --- Row 3 ---
    @ui.button(emoji="🔉", style=discord.ButtonStyle.secondary, row=2)
    async def vol_down(self, interaction: discord.Interaction, button: ui.Button):
        vc = interaction.guild.voice_client
        queue = self._get_queue()
        if vc and vc.source:
             new_vol = max(0.0, queue.volume - 0.1)
             queue.volume = new_vol
             vc.source.volume = new_vol
             await interaction.response.send_message(f"Volume: {int(new_vol*100)}%", ephemeral=True)

    @ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, row=2)
    async def vol_up(self, interaction: discord.Interaction, button: ui.Button):
        vc = interaction.guild.voice_client
        queue = self._get_queue()
        if vc and vc.source:
             new_vol = min(2.0, queue.volume + 0.1)
             queue.volume = new_vol
             vc.source.volume = new_vol
             await interaction.response.send_message(f"Volume: {int(new_vol*100)}%", ephemeral=True)

    @ui.button(emoji="🔇", style=discord.ButtonStyle.secondary, row=2)
    async def mute(self, interaction: discord.Interaction, button: ui.Button):
        vc = interaction.guild.voice_client
        queue = self._get_queue()
        if vc and vc.source:
             if vc.source.volume > 0:
                 vc.source.volume = 0
                 await interaction.response.send_message("Muted 🔇", ephemeral=True)
             else:
                 vc.source.volume = queue.volume
                 await interaction.response.send_message("Unmuted 🔊", ephemeral=True)


# --- Cog ---

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {} # Guild ID -> MusicQueue
        
        self.yt_dlp_options = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0', 
            'quiet': True,
            'no_warnings': True,
        }
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        self.ytdl = yt_dlp.YoutubeDL(self.yt_dlp_options)
        
        # FFmpeg check
        if not shutil.which("ffmpeg"):
            self._find_ffmpeg()

    def _find_ffmpeg(self):
         # Try to find it in common locations
        common_paths = [
            r"C:\Users\Dinet\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
        ]
        for path in common_paths:
            if os.path.exists(path):
                os.environ["PATH"] += os.pathsep + os.path.dirname(path)
                print(f"Found FFmpeg at {path}, added to PATH.")
                break

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    async def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        song = queue.next()
        
        if not song:
            await ctx.send("```text\nQueue finished. Silence falls... 🌌\n```")
            return

        try:
            # Create PCMVolumeTransformer
            source = discord.FFmpegPCMAudio(song.url, **self.ffmpeg_options)
            source = discord.PCMVolumeTransformer(source, volume=queue.volume)
            
            def after_playing(error):
                if error:
                    print(f"Error: {error}")
                
                # Check for loop track logic re-add here if strict precision needed, 
                # but we handle it in queue.next()
                
                fut = asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
                try: fut.result() 
                except: pass

            ctx.voice_client.play(source, after=after_playing)
            
            view = MusicPlayerView(self, ctx)
            embed = song.create_embed()
            
            msg = await ctx.send(embed=embed, view=view)
            queue.interaction_message = msg
            
        except Exception as e:
            print(f"Error in play_next: {e}")
            await ctx.send(f"Error playing {song.title}: {e}")
            await self.play_next(ctx)


    @commands.command(name="join")
    async def join(self, ctx):
        if not shutil.which("ffmpeg"):
             await ctx.send("❌ **System Error**: FFmpeg is corrupt or missing from PATH.")
             return

        if ctx.author.voice:
            channel = ctx.author.voice.channel
            try:
                if ctx.voice_client:
                    await ctx.voice_client.move_to(channel)
                else:
                    await channel.connect(timeout=10.0, reconnect=True)
                await ctx.send(f"Connected to **{channel.name}**! 🎵")
            except Exception as e:
                await ctx.send(f"Connection error: {e}")
        else:
            await ctx.send("You need to be in a voice channel!")

    @commands.command(name="play")
    async def play(self, ctx, *, query):
        if not shutil.which("ffmpeg"):
            await ctx.send("❌ **System Error**: FFmpeg is corrupt or missing from PATH. Restart bot env.")
            return

        if not ctx.voice_client:
            if ctx.author.voice:
                try:
                    await ctx.author.voice.channel.connect(timeout=10.0, reconnect=True)
                except Exception as e:
                    await ctx.send(f"Connection Error: {e}")
                    return
            else:
                await ctx.send("Join a voice channel first!")
                return
        
        search_msg = await ctx.send(f"Searching for `{query}`... 🔍")

        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(query, download=False))
            
            if data is None:
                 await search_msg.edit(content="Could not find any results.")
                 return

            if 'entries' in data:
                data = data['entries'][0]
            
            song = Song(None, data, ctx.author)
            queue = self.get_queue(ctx.guild.id)
            queue.add(song)
            
            if not ctx.voice_client.is_playing():
                await search_msg.delete()
                await self.play_next(ctx)
            else:
                await search_msg.edit(content=f"📝 Added **{song.title}** to the queue!")

        except Exception as e:
            await search_msg.edit(content=f"Error processing track: {e}")
            print(f"Play error: {e}")

    @commands.command(name="stop")
    async def stop(self, ctx):
        if ctx.voice_client:
             queue = self.get_queue(ctx.guild.id)
             queue.clear()
             ctx.voice_client.stop()
             await ctx.send("Stopped.")

    @commands.command(name="skip")
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
             ctx.voice_client.stop()
             await ctx.send("Skipped! ⏩")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
