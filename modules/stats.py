import time, os, json
import discord
from discord.ext import commands
from discord.commands import slash_command, Option

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name='stats', description='Da estadísticas generales sobre el juego')
    async def stats(self, ctx):
        utilities = self.bot.get_cog("UtilitiesCog")

        game_stats = utilities.generate_game_stats()
        
        if not game_stats:
            await ctx.respond("No tengo partidas registradas.")
            return
        
        await ctx.respond(game_stats)
        return

    @slash_command(name='personaje', description='Da estadísticas sobre el personaje')
    async def personaje(self, ctx, character: Option(str, "Personaje")):
        utilities = self.bot.get_cog("UtilitiesCog")

        character = character.lower().replace(" ", "")
        if not utilities.is_character_valid(character):
            await ctx.respond("El personaje no es válido. Usa el nombre del personaje en inglés, en minúscula y sin espacios (por ejemplo: `scarletwoman`).")
            return
        
        character_stats = utilities.generate_character_stats(character)
        
        if not character_stats:
            await ctx.respond(f"No tengo partidas registradas con el {character}.")
            return
        
        await ctx.respond(character_stats)
        return

    @slash_command(name='jugador', description='Da estadísticas sobre el jugador')
    async def jugador(self, ctx, player: Option(str, "Jugador: mención o ID")):
        utilities = self.bot.get_cog("UtilitiesCog")

        player = utilities.clean_id(player)
        if not player:
            await ctx.respond("El jugador no es válido. Solo acepto menciones o IDs de usuarios.")
            return
        
        player_stats = utilities.generate_player_stats(player)
        
        if not player_stats:
            await ctx.respond(f"No tengo partidas registradas con <@{player}>.")
            return
        
        await ctx.respond(player_stats)
        return

    @slash_command(name='resultado', description='Registra el resultado de una partida.')
    @commands.is_owner()
    async def resultado(self, ctx, 
                        players: Option(str, "Lista de jugadores con sus personajes al acabar la partida."), 
                        winner: Option(str, "Resultado del juego. Valores admitidos: good, evil")):
        utilities = self.bot.get_cog("UtilitiesCog")

        if winner not in ["good", "evil"]:
            await ctx.respond("El resultado solo puede ser 'good' o 'evil'.")
            return

        raw_player_list = players.split(" ")
        processed_players = {}
        for player_data in raw_player_list:
            player = utilities.clean_id(player_data.split("-")[0]) # Renive the <@> part of the user ID
            if not player:
                await ctx.respond(f"El usuario {player_data.split('-')[0]} no es válido. Solo acepto menciones o IDs de usuarios.")
                return

            character = player_data.split("-")[1]
            if utilities.is_character_valid(character) == False: # Check if character is in character_data.json
                await ctx.respond(f"El personaje {character} no es válido.")
                return
            if player in processed_players:
                await ctx.respond(f"No puedo procesar este resultado. <@{player}> está duplicado.")
                return
            processed_players[player] = character
        print(processed_players)

        utilities.backup_data()

        confirmation = utilities.generate_confirmation_msg(processed_players, winner)
        if confirmation == None:
            await ctx.respond("Error al procesar la validez de los parámetros. Revisa que los jugadores, personajes, alineamiento y resultado sean correctos.")
            return
        await ctx.respond(confirmation, view=self.ConfirmationButtons(ctx, self.bot, processed_players, winner))

        return
    
    @resultado.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.NotOwner):
            await ctx.respond("No tienes permiso para guardar una partida.")
        else:
            raise error

    class ConfirmationButtons(discord.ui.View):
        def __init__(self, ctx, bot, processed_players, winner):
            super().__init__()
            self.ctx = ctx
            self.author = ctx.author
            self.processed_players = processed_players
            self.winner = winner
            self.utilities = bot.get_cog("UtilitiesCog")

        @discord.ui.button(label="✅ Confirmar", row=0, style=discord.ButtonStyle.primary)
        async def confirm_btn_callback (self, button, interaction):
            button.label = "✅ Partida guardada"
            self.disable_all_items()
            save_game = self.utilities.update_game_stats(self.processed_players, self.winner)
            for player in self.processed_players:
                self.utilities.update_player_stats(str(player), self.processed_players[player], self.winner)
            
            for player in self.processed_players:
                self.utilities.update_character_stats(self.processed_players[player], self.winner)

            await self.ctx.send(f"**Partida guardada.** ID: `{save_game}` / Fecha: <t:{int(time.time())}:f>")
            await interaction.response.edit_message(view=self)
            return

        @discord.ui.button(label="❌ Cancelar", row=0, style=discord.ButtonStyle.danger)
        async def cancel_btn_callback (self, button, interaction):
            button.label = "Cancelado"
            self.disable_all_items()
            await self.ctx.send("Partida no guardada.")
            await interaction.response.edit_message(view=self)
            return

        async def interaction_check(self, interaction: discord.Interaction):
            return interaction.user.id == self.author.id # Only the user who sent the command can interact with the buttons
        
def setup(bot):
    bot.add_cog(StatsCog(bot))