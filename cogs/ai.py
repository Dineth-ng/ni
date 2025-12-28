import discord
from discord.ext import commands
import google.generativeai as genai
import os

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key and api_key != 'your_gemini_api_key_here':
            genai.configure(api_key=api_key)
            # gemini-pro is deprecated/unavailable in some contexts. using gemini-1.5-flash.
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.chat_session = self.model.start_chat(history=[])
            print("AI Cog: Gemini configured successfully.")
        else:
            self.model = None
            print("AI Cog: WARNING - GEMINI_API_KEY not found or invalid.")

    @commands.command(name="chat", aliases=["ask"])
    async def chat(self, ctx, *, query: str):
        """Talk to the Antigravity Brain."""
        if not self.model:
            await ctx.send("My brain is missing! (Check GEMINI_API_KEY in .env)")
            return

        async with ctx.typing():
            try:
                # Add personality prompt
                prompt = f"You are Antigravity, a chaotic, funny, and slightly unhinged Discord bot. Your purpose is to entertain. Answer the following user query with humor and chaos: {query}"
                
                response = self.chat_session.send_message(prompt)
                
                # Discord has a 2000 char limit. Reserve space for code block.
                response_text = response.text
                if len(response_text) > 1990:
                    response_text = response_text[:1985] + "..."
                
                await ctx.send(f"```text\n{response_text}\n```")
            except Exception as e:
                await ctx.send(f"```text\nError: I tripped over a cosmic ray. ({e})\n```")

async def setup(bot):
    await bot.add_cog(AICog(bot))
