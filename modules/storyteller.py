import json
from discord.ext import commands
from discord.commands import Option, slash_command
import discord

class StorytellerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utilities = bot.get_cog("UtilitiesCog")
    
    @slash_command(name="boomdandy", description="Boom!", guild_ids=[551837071703146506])
    async def boomdandy(self, ctx, players: Option(str, "Space-separated list of surviving players (using Discord mentions).")):
        clean_players = []
        for player in players.split(" "):
            player = self.utilities.clean_id(player) # Remove the <@> part of the user ID
            if not player:
                await ctx.respond(f"El usuario {player} no es válido. Solo acepto menciones o IDs de usuarios.")
                return
            clean_players.append(str(player))
        
        msg = "¡El Boomdandy ha explotado! Los jugadores que sobrevivieron son:\n"
        msg += f"{' '.join(clean_players)}\n\n"
        msg += "Tenéis **1 minuto** para decidir quien va a morir. Usad los botones para escogerlo."

        await ctx.respond(msg, view=self.BoomdandyUI(ctx, clean_players))
        return

    class BoomButton(discord.ui.Button):
        def __init__(self, ctx, player):
            super().__init__(label=str(player), style=discord.ButtonStyle.primary)
            self.ctx = ctx
            self.disabled = False
        
        async def callback(self, interaction):
            await self.ctx.send(f"Apuntando a {self.label}")
            return

    class BoomdandyUI(discord.ui.View):
        def __init__(self, ctx, players):
            super().__init__(timeout=60.0, disable_on_timeout=True)
            self.players = players
            self.ctx = ctx

            for player in players:
                self.add_item(StorytellerCog.BoomButton(ctx, player))
        
        async def on_timeout(self):
            await self.ctx.send("¡Tiempo!")
            return 


def setup(bot):
    bot.add_cog(StorytellerCog(bot))