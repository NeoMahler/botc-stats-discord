import json
from discord.ext import commands
import discord

class StorytellerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(StorytellerCog(bot))