import subprocess, os, json, shutil
from discord.ext import commands
from discord.commands import slash_command, Option
import discord

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

    @slash_command(name="undo", description="Recovers the last version of the stats before the last saved game.")
    @commands.is_owner()
    async def undo(self, ctx):
        await ctx.defer()
        shutil.copy(os.path.join("backups", "players.json"), os.path.join("data", "players.json"))
        shutil.copy(os.path.join("backups", "characters.json"), os.path.join("data", "characters.json"))
        shutil.copy(os.path.join("backups", "games.json"), os.path.join("data", "games.json"))
        await ctx.respond('Los datos de la última partida guardada se han borrado. Recuerda que solo se pueden borrar los datos de la última partida; si haces `/undo` más de una vez seguida, no va a cambiar nada.')

    @slash_command(name="backup", description="Sends the stats files.")
    @commands.is_owner()
    async def backup(self, ctx):
        await ctx.respond("Enviando los archivos de partidas guardadas...")
        files = [os.path.join("data", "players.json"), os.path.join("data", "characters.json"), os.path.join("data", "games.json")]
        for f in files:
            await ctx.send(file=discord.File(f))

def setup(bot):
    bot.add_cog(AdminCog(bot))