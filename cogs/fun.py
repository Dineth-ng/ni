import discord
from discord.ext import commands
import random

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="iq")
    async def iq(self, ctx):
        iq_val = random.randint(1, 200)
        msg = f"{ctx.author.name}, your IQ is {iq_val}."
        if iq_val > 150:
            msg += " (Einstein?)"
        elif iq_val < 50:
            msg += " (Oof...)"
        await ctx.send(f"```text\n{msg}\n```")

    @commands.command(name="roast")
    async def roast(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        roasts = [
            "You're the reason they put instructions on shampoo bottles.",
            "I'd agree with you but then we'd both be wrong.",
            "You bring everyone so much joy when you leave the room.",
            "I see you're setting aside some time to humiliate yourself in public.",
            "You have a face for radio."
        ]
        await ctx.send(f"```text\n@{member.name}, {random.choice(roasts)} 🔥\n```")

    @commands.command(name="fortune")
    async def fortune(self, ctx):
        fortunes = [
            "A cosmic ray will hit your CPU today.",
            "You will find a missing semicolon in your life.",
            "Avoid red cables.",
            "The stars predict a segmentation fault.",
            "You will meet a tall, dark, and handsome syntax error."
        ]
        await ctx.send(f"```text\n🔮 Fortune: {random.choice(fortunes)}\n```")

async def setup(bot):
    await bot.add_cog(FunCog(bot))
