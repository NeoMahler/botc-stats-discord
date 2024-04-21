import os, json, shutil
from discord.ext import commands
import discord
import time

class MessagesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utilities = bot.get_cog("UtilitiesCog")
    
    def generate_confirmation_msg(self, players, result):
        msg = "¿Guardar partida con los siguientes datos?\n\n"
        for player in players:
            char_id = players[player].split("(")[0]
            character = self.utilities.get_character_name(char_id)
            if "(" in players[player]:
                alignment = players[player][-2]
                if alignment == "g":
                    alignment = "bueno"
                elif alignment == "e":
                    alignment = "malvado"
                else:
                    return None
                msg += f"**<@{player}>** era el **{character}** ({alignment})\n"
            else:
                is_good = self.utilities.is_character_good(char_id)
                if is_good:
                    alignment = "bueno"
                else:
                    alignment = "malvado"
                article = self.utilities.get_character_article(char_id)
                msg += f"**<@{player}>** era {article}**{character}** ({alignment})\n"

        if result == "good":
            result = "Bueno"
        else:
            result = "Malvado"

        msg += f"\nEquipo ganador: **{result}**"

        return msg
    
    def generate_player_stats(self, player, user, character=None):
        player_stats_f = os.path.join("data", "players.json")
        with open(player_stats_f, 'r') as f:
            player_stats = json.load(f)
        if str(player) not in player_stats:
            return False
        
        player_stats = player_stats[str(player)]
        good_games = player_stats['games_good'] if player_stats['games_good'] > 0 else 0
        evil_games = player_stats['games_evil'] if player_stats['games_evil'] > 0 else 0
        winrate_good = player_stats['winrate_good'] if player_stats['winrate_good'] > 0 else 0
        winrate_evil = player_stats['winrate_evil'] if player_stats['winrate_evil'] > 0 else 0

        if good_games == 0:
            g_winrate_percentage = 0
        else:
            g_winrate_percentage = round(winrate_good / good_games * 100)
        if evil_games == 0:
            e_winrate_percentage = 0
        else:
            e_winrate_percentage = round(winrate_evil / evil_games * 100)
        
        print(f"Good games: {good_games} ({winrate_good}), Evil games: {evil_games} ({winrate_evil})" )

        if evil_games == 0 or good_games == 0:
            general_winrate_percentage = 0
        else:
            general_winrate_percentage = round((winrate_good + winrate_evil) / (good_games + evil_games) * 100)
        
        print(f"General winrate: {general_winrate_percentage}%")

        all_played_chars = player_stats['characters']
        top_chars = sorted(all_played_chars.items(), key=lambda x: x[1]['games'], reverse=True)[:5] # Ordenar los personajes según el valor de "games" de cada personaje

        top_chars_final = []
        for char in top_chars:
            char_name = self.utilities.get_character_name(char[0])
            top_chars_final.append(f"{char_name} ({char[1]['games']})")

        embed = discord.Embed(title=f"Estadísticas de {user.display_name}", description=f"Ha participado en {good_games + evil_games} partidas")
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Victorias", value=f"{general_winrate_percentage}%")
        embed.add_field(name="Equipo bueno", value=f"{good_games} (:trophy: {g_winrate_percentage}%)")
        embed.add_field(name="Equipo malvado", value=f"{evil_games} (:trophy: {e_winrate_percentage}%)")
        if not character:
            embed.add_field(name="Personajes más jugados", value=", ".join(top_chars_final))
            embed.set_footer(text="Usa /jugador <jugador> <personaje> para ver estadísticas con un personaje concreto.")
        else:
            if character not in player_stats['characters']:
                embed.set_footer(text=f"ERROR: {user.display_name} no ha jugado nunca como {character}.")
                return embed
            char_stats = player_stats['characters'][character]
            char_article = self.utilities.get_character_article(character)
            char_name = self.utilities.get_character_name(character)
            char_games = char_stats['games']
            char_winrate = round(char_stats['winrate'] / char_games * 100)
            embed.add_field(name=f"Partidas como {char_article}{char_name}", value=f"{char_games} (:trophy: {char_winrate}%)")

        return embed
    
    def generate_character_stats(self, character):
        character_stats_f = os.path.join("data", "characters.json")
        with open(character_stats_f, 'r') as f:
            character_stats = json.load(f)

        with_stats = False
        if character in character_stats:
            with_stats = True
        
        if with_stats:
            character_stats = character_stats[character]
            winrate = round(character_stats['winrate'] / character_stats['games'] * 100)

        char_details = self.utilities.get_character_details(character)
        character = char_details["name"]["es"]
        character_en = char_details["name"]["en"]
        type = char_details["type"]
        if type == "demon":
            type = "Demonio"
            color = discord.Color.red()
        elif type == "minion":
            type = "Secuaz"
            color = discord.Color.red()
        elif type == "outsider":
            type = "Forastero"
            color = discord.Color.blue()
        elif type == "townsfolk":
            type = "Aldeano"
            color = discord.Color.blue()
        elif type == "fabled":
            type = "Mítico"
            color = discord.Color.gold()
        else:
            type = "Viajero"
            color = discord.Color.dark_magenta()
        wiki = "https://wiki.bloodontheclocktower.com/" + character_en.replace(" ", "_")

        embed = discord.Embed(title=f"{character}", description=char_details["description"]["es"], url=wiki, color=color)
        embed.add_field(name="Tipo", value=type)
        if with_stats:
            embed.add_field(name="Partidas", value=f"{character_stats['games']} (:trophy: {winrate}%)")
        embed.add_field(name="En inglés", value=character_en)
        if with_stats:
            embed.set_footer(text="Nota: no incluye partidas con el alineamiento alterado.")
        else:
            embed.set_footer(text="No tengo partidas guardadas con este personaje.")

        return embed
    
    def generate_game_stats(self):
        game_stats_f = os.path.join("data", "games.json")
        with open(game_stats_f, 'r') as f:
            game_stats = json.load(f)
        if game_stats == {}:
            return False
        
        character_stats_f = os.path.join("data", "characters.json")
        with open(character_stats_f, 'r') as f:
            character_stats = json.load(f)
        
        #player_stats_f = os.path.join("data", "players.json")
        #with open(player_stats_f, 'r') as f:
        #    player_stats = json.load(f)

        # Get percentage of results
        good_games = []
        evil_games = []
        for game in game_stats:
            if game_stats[game]["result"] == "good":
                good_games.append(game)
            elif game_stats[game]["result"] == "evil":
                evil_games.append(game)
        good_percentage = round(len(good_games) / len(game_stats) * 100)
        evil_percentage = round(len(evil_games) / len(game_stats) * 100)

        # Get top characters
        all_characters = [] 
        for game in game_stats:
            characters = game_stats[game]["players"]
            print(characters.values())
            all_characters.append(list(characters.values())) # This creates a list of lists...        
        all_chars_processed = [item for sublist in all_characters for item in sublist] # So we create a new list with only strings
        top_characters = sorted(set(all_chars_processed), key=lambda i: all_chars_processed.count(i), reverse=True)[:5] # We get the top 5 by frequency in the list
        final_char_list = []
        for character in top_characters:
            char_name = self.utilities.get_character_name(character)
            winrate_absolute = character_stats[character]["winrate"]
            winrate = round(winrate_absolute / character_stats[character]["games"] * 100)
            final_char_list.append(f"{char_name} (:trophy: {winrate}%)")
    
        embed = discord.Embed(title=f"Estadísticas generales", description=f"De un total de {len(game_stats)} partidas.")
        embed.add_field(name="Victorias buenas", value=f"{good_percentage}%")
        embed.add_field(name="Victorias malvadas", value=f"{evil_percentage}%")
        embed.add_field(name="Personajes más jugados", value="\n".join(final_char_list))
        embed.set_footer(text="Usa /jugador o /personaje para obtener estadísticas concretas.")

        return embed

def setup(bot):
    bot.add_cog(MessagesCog(bot))