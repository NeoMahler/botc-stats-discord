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
        player_members = []
        for player in players.split(" "):
            player = self.utilities.clean_id(player) # Remove the <@> part of the user ID
            if not player:
                await ctx.respond(f"El usuario {player} no es válido. Solo acepto menciones o IDs de usuarios.")
                return
            clean_players.append(str(player))
            player_member = await self.bot.fetch_user(int(player))
            player_members.append(player_member)
        
        pings = [f'<@{player}>' for player in clean_players]
        msg = "¡El Boomdandy ha explotado! Los jugadores que sobrevivieron son:\n"
        msg += f"{' '.join(pings)}\n\n"
        msg += "Tenéis **1 minuto** para decidir quien va a morir. Usad los botones para escogerlo."

        await ctx.respond(msg, view=self.BoomdandyUI(ctx, player_members))
        return

    class BoomButton(discord.ui.Button):
        def __init__(self, ctx, player):
            super().__init__(label=player.display_name, style=discord.ButtonStyle.primary)
            self.ctx = ctx
            self.disabled = False
            self.player = player
        
        async def callback(self, interaction):
            await interaction.response.defer()
            await self.ctx.send(f"<@{interaction.user.id}> está apuntando a <@{self.player.id}>")
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