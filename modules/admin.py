import subprocess, os, json
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
            print(f"\n===== MODULE {cog} RELOADED =====\n")
            await ctx.respond('Módulo recargado :tada:')
    
    @slash_command(name="sync", description="Syncs commands with Discord (owner-only).")
    @commands.is_owner()
    async def sync(self, ctx):
        await self.bot.sync_commands()
        await ctx.respond('Comandos sincronizados :tada:')

    @slash_command(name="config", description="Set up configuration options.")
    @commands.is_owner()
    async def config(self, ctx, 
                     player_role: Option(str, "Player role ID number", required=False), 
                     st_role: Option(str, "Storyteller role ID", required=False), 
                     game_chat: Option(str, "Game chat text channel ID", required=False)):
        bot_config_f = "config.json"
        if not os.path.isfile(bot_config_f):
            with open(bot_config_f, "w") as f:
                json.dump({}, f)

        with open(bot_config_f, "r") as f:
            bot_config = json.load(f)

        if player_role:
            bot_config["player_role"] = player_role
        if st_role:
            bot_config["st_role"] = st_role
        if game_chat:
            bot_config["game_chat"] = game_chat
        
        with open(bot_config_f, "w") as f:
            json.dump(bot_config, f)
        
        await ctx.respond(f'Configuración guardada :tada:')
    
    @slash_command(name="getpid", description="Gets process ID of the bot (owner-only).")
    @commands.is_owner()
    async def getpid(self, ctx):
        pid = os.getpid()
        await ctx.respond(f'PID: `{pid}`')

    @slash_command(name="error", description="Forcibly causes the bot to error, for debugging purposes (owner-only).", guild_ids=[551837071703146506])
    @commands.is_owner()
    async def error(self, ctx):
        print("/error used!")
        raise Exception("Forced error")

def setup(bot):
    bot.add_cog(AdminCog(bot))