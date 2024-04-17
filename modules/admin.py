import subprocess
from discord.ext import commands
from discord.commands import slash_command, Option

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @slash_command(name='ping', description='Pong!')
    async def ping(self, ctx):
        await ctx.respond('Pong!')
        return

    @slash_command(name="update", description="Pulls the latest version from GitHub (owner-only).")
    @commands.is_owner()
    async def update(self, ctx):
        await ctx.defer()
        output = subprocess.check_output("git pull", shell=True)
        await ctx.respond("Obteniendo la última versión de GitHub: ```" + str(output) + "``` Recuerda usar `/reload` para que los cambios surtan efecto.")

    @slash_command(name="load", description="Loads a previously unloaded module (owner-only).")
    @commands.is_owner()
    async def load(self, ctx, cog: Option(str, "Name of the module (without .py extension)")):
        module = "modules." + cog
        try:
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.respond(f':scream: Error: {type(e).__name__} - {e}')
        else:
            await ctx.respond('Módulo cargado :tada:')

    @slash_command(name="unload", description="Unloads a previously loaded module (owner-only).")
    @commands.is_owner()
    async def unload(self, ctx, cog: Option(str, "Name of the module (without .py extension)")):
        module = "modules." + cog
        try:
            self.bot.unload_extension(module)
        except Exception as e:
            await ctx.respond(f':scream: Error: {type(e).__name__} - {e}')
        else:
            await ctx.respond('Módulo descargado :tada:')

    @slash_command(name="reload", description="Reloads a previously loaded module (owner-only).")
    @commands.is_owner()
    async def reload(self, ctx, cog: Option(str, "Name of the module (without .py extension)")):
        module = "modules." + cog
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.respond(f':scream: Error: {type(e).__name__} - {e}')
        else:
            await ctx.respond('Módulo recargado! :tada:')

def setup(bot):
    bot.add_cog(AdminCog(bot))