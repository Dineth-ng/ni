import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Required for moderation (kick/ban)

class TerminalHelpCommand(commands.DefaultHelpCommand):
    """Custom help command to match the terminal aesthetic."""
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            # Wrap the help output in a code block
            await destination.send(f"```text\n{page}\n```")

class AntigravityBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=TerminalHelpCommand(),
            case_insensitive=True
        )

    async def setup_hook(self):
        """Loads all cogs from the cogs directory."""
        print("--- Loading Cogs ---")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and filename != '__init__.py':
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Loaded: {filename}')
                except Exception as e:
                    print(f'Failed to load {filename}: {e}')
        print("--- Cogs Loaded ---")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('Antigravity is ready to defy physics (and logic).')
        await self.change_presence(activity=discord.Game(name="Defying Physics | !help"))

# Run the Bot
if __name__ == '__main__':
    if not TOKEN or TOKEN == 'your_discord_token_here':
        print("ERROR: DISCORD_TOKEN is missing or invalid in .env file.")
        print("Please set up your .env file with a valid token.")
    else:
        bot = AntigravityBot()
        bot.run(TOKEN)
