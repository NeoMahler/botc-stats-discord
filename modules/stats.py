import time, os, json
import discord
from discord.ext import commands
from discord.commands import slash_command, Option

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utilities = bot.get_cog("UtilitiesCog")
        self.messages = bot.get_cog("MessagesCog")

    @slash_command(name='stats', description='Da estadísticas generales sobre el juego')
    async def stats(self, ctx):

        game_stats = self.messages.generate_game_stats()
        
        if not game_stats:
            await ctx.respond("No tengo partidas registradas.")
            return
        
        await ctx.respond(embed=game_stats)
        return

    @slash_command(name='personaje', description='Da estadísticas sobre el personaje')
    async def personaje(self, ctx, character: Option(str, "Personaje")):

        character = character.lower().replace(" ", "")
        if not self.utilities.is_character_valid(character):
            await ctx.respond("El personaje no es válido. Usa el nombre del personaje en inglés, en minúscula y sin espacios (por ejemplo: `scarletwoman`).")
            return
        
        character_stats = self.messages.generate_character_stats(character)
        
        await ctx.respond(embed=character_stats)
        return

    @slash_command(name='jugador', description='Da estadísticas sobre el jugador')
    async def jugador(self, ctx, jugador: Option(str, "Jugador: mención o ID"), character: Option(str, "Personaje", required=False)):
        player = self.utilities.clean_id(jugador)
        if not player:
            player = self.utilities.get_player_from_data(jugador)
            if not player:
                await ctx.respond(f"No conozco a {jugador}.")
                return
        
        if character:
            if not self.utilities.is_character_valid(character):
                await ctx.respond(f"El personaje {character} no es válido. Usa el nombre del personaje en inglés, en minúscula y sin espacios (por ejemplo: `scarletwoman`).")
                return
        
        player_member = await self.bot.fetch_user(int(player))
        
        player_stats = self.messages.generate_player_stats(player, player_member, character=character if character else None)
        
        if not player_stats:
            await ctx.respond(f"No tengo partidas registradas con <@{player}>.")
            return
        
        await ctx.respond(embed=player_stats)
        return

    @slash_command(name='resultado', description='Registra el resultado de una partida.')
    @commands.is_owner()
    async def resultado(self, ctx, 
                        players: Option(str, "Lista de jugadores con sus personajes al acabar la partida."), 
                        winner: Option(str, "Resultado del juego. Valores admitidos: good, evil", choices=["good", "evil"])):
        await ctx.defer()
        if winner not in ["good", "evil"]:
            await ctx.respond("El resultado solo puede ser 'good' o 'evil'.")
            return

        raw_player_list = players.split(" ")
        processed_players = {}
        for player_data in raw_player_list:
            player = self.utilities.clean_id(player_data.split("-")[0]) # Remove the <@> part of the user ID
            if not player:
                await ctx.respond(f"El usuario {player_data.split('-')[0]} no es válido. Solo acepto menciones o IDs de usuarios.")
                return

            characters = player_data.split("-")[1:]
            player_characters = []

            for character in characters:
                if self.utilities.is_character_valid(character) == False: # Check if character is in character_data.json
                    await ctx.respond(f"El personaje **{character}** no es válido. Recuerda no especificar el alineamiento de los personajes que no hayan cambiado de alineamiento.")
                    return
                if player in processed_players:
                    await ctx.respond(f"No puedo procesar este resultado. <@{player}> está duplicado.")
                    return
                player_characters.append(character)
            processed_players[player] = player_characters

            await self.utilities.update_player_details(player)

        self.utilities.backup_data()

        confirmation = self.messages.generate_confirmation_msg(processed_players, winner)
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
            
            characters_list = self.utilities.get_all_characters_from_game(self.processed_players)
            for character in characters_list:
                self.utilities.update_character_stats(character, self.winner)

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