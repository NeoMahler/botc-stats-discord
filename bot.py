import discord
from discord.ext import commands

from dotenv import load_dotenv

import logging, sys, traceback

import datetime

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

def get_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""

    # Notice how you can use spaces in prefixes. Try to keep them simple though.
    prefixes = ['!', 'cs!']

    # Check to see if we are outside of a guild. e.g DM's etc.
    if not message.guild:
        # Only allow ? to be used in DMs
        return ['!', 'cs!', '']

    # If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
    return commands.when_mentioned_or(*prefixes)(bot, message)


# Below cogs represents our folder our cogs are in. Following is the file name. So 'meme.py' in cogs, would be cogs.meme
# Think of it like a dot path import
initial_extensions = ['modules.utilities', 'modules.messages', 'modules.stats', 'modules.storyteller', 'modules.admin']

bot = commands.Bot(command_prefix=get_prefix)
# CONFIG: CHANGE OWNER_ID IN ABOVE LINE TO YOUR DISCORD ACCOUNT'S USER ID.

bot.remove_command('help')

# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    # Changes our bots Playing Status. type=1(streaming) for a standard game you could remove type and url.
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='you!'))
    print(f'Successfully logged in and booted...!')

@bot.event
async def on_application_command(ctx):
    logfile = "commands.log"
    with open(logfile, 'a') as f:
        f.write(f"[{datetime.datetime.now()}] {ctx.command}{' ' + str(ctx.selected_options) if ctx.selected_options != None else ''} in server {ctx.guild} ({ctx.guild_id}).\n")

@bot.event
async def on_application_command_error(ctx, exception):
    await ctx.respond(f":bug: Error desconocido: ```python\n{exception}```")
    raise exception

# @bot.event # TODO: on_error doesn't get ctx
# async def on_error(ctx):
#     await ctx.respond(f":bug: Error desconocido. Traceback completo: ```python\n{traceback.format_exc()}```")
#     raise traceback.format_exc()

load_dotenv()
try:
    with open('token.cfg', 'r') as f:
        token = f.read()
    bot.run(token, reconnect=True)
except KeyError:
    token = input("I can't find the token. You can enter it manually here: ")
    bot.run(token, reconnect=True)