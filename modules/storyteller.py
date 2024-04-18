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
        if self.utilities.get_player_type(ctx.author) != "st":
            await ctx.respond("Solo el Narrador puede activar esta función.")
            return
        
        clean_players = []
        player_members = []
        for player in players.split(" "):
            player = self.utilities.clean_id(player) # Remove the <@> part of the user ID
            if not player:
                await ctx.respond(f"Error: Solo acepto menciones o IDs de usuarios.")
                return
            clean_players.append(str(player))
            player_member = await self.bot.fetch_user(int(player))
            player_members.append(player_member)
        
        if len(set(clean_players)) < 3: # set() to remove duplicates
            await ctx.respond("Error: Debes darme por lo menos 3 jugadores (separados con espacios) sin repeticiones.")
            return

        pings = [f'<@{player}>' for player in clean_players]
        msg = "# ¡El Boomdandy ha explotado! Los jugadores que sobrevivieron son:\n"
        msg += f"{' '.join(pings)}\n\n"
        msg += "Tenéis **1 minuto** para decidir quien va a morir. Usad los botones para escogerlo."


        self.BoomdandyUI.result = {}
        await ctx.respond(msg, view=self.BoomdandyUI(ctx, self.bot, player_members))
        return

    class BoomButton(discord.ui.Button):
        def __init__(self, ctx, bot, player_name, player):
            super().__init__(label=f"👉 {player_name}", style=discord.ButtonStyle.primary)
            self.utilities = bot.get_cog("UtilitiesCog")
            self.ctx = ctx
            self.disabled = False
            self.player = player
        
        async def callback(self, interaction):
            if self.utilities.get_player_type(interaction.user) != "player":
                await interaction.response.send_message("No estás jugando, así que no puedes participar en la votación.", ephemeral=True)
                return
            await interaction.response.defer()
            await self.ctx.send(f"<@{interaction.user.id}> está apuntando a <@{self.player.id}>")
            result_dict = StorytellerCog.BoomdandyUI.result
            for player in result_dict: # Avoid duplicates
                if interaction.user.id in result_dict[player]:
                    result_dict[player].remove(interaction.user.id)
            result_dict[self.player.id].append(interaction.user.id)
            return
        
    class BoomdandyUI(discord.ui.View):
        result = {}
        def __init__(self, ctx, bot, players):
            super().__init__(timeout=10.0, disable_on_timeout=True)
            self.players = players
            self.ctx = ctx
            self.bot = bot
            self.utilities = bot.get_cog("UtilitiesCog")

            for player in players:
                self.result[player.id] = []
                player_name = self.utilities.get_player_name(player)
                self.add_item(StorytellerCog.BoomButton(ctx, self.bot, player_name, player))
        
        async def on_timeout(self): # TODO: I don't think this is working accurately!"
            msg = "## :bomb: **TIEMPO** :bomb:\n\n"
            msg += "Resultados:\n"
            for player in self.result:
                msg += f"**<@{player}>**: {', '.join([f'<@{user}>' for user in self.result[player]])} (**{len(self.result[player])} votos**)\n"
            await self.ctx.send(msg)
            return 


def setup(bot):
    bot.add_cog(StorytellerCog(bot))