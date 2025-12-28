import discord
from discord.ext import commands
import random

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="yeet")
    @commands.has_permissions(kick_members=True)
    async def yeet(self, ctx, member: discord.Member, *, reason=None):
        if reason is None:
            reasons = [
                "The atmosphere was too heavy.",
                "Failed the vibe check.",
                "Gravity reversed!",
                "To infinity and beyond!",
                "Begone, thot!",
                "Sent to the shadow realm."
            ]
            reason = random.choice(reasons)
        
        try:
            await member.kick(reason=reason)
            await ctx.send(f"```text\n{member.name} was yeeted. Reason: {reason} 🚀\n```")
        except discord.Forbidden:
            await ctx.send("```text\nI tried to yeet them, but they are too heavy (Missing Permissions).\n```")

    @yeet.error
    async def yeet_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("```text\nYou don't have the power to yeet people!\n```")

    @commands.command(name="silence")
    @commands.has_permissions(move_members=True)
    async def silence(self, ctx, member: discord.Member):
        """Disconnects a user from voice channel."""
        if member.voice and member.voice.channel:
            try:
                await member.move_to(None)
                await ctx.send(f"```text\n{member.name} has been silenced. 🤫\n```")
            except discord.Forbidden:
                await ctx.send("```text\nI can't disconnect them (Missing Permissions).\n```")
        else:
            await ctx.send(f"```text\n{member.name} is not in a voice channel.\n```")

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
