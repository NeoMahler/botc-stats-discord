import os, json, shutil
from discord.ext import commands
import discord
import time

class MessagesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utilities = bot.get_cog("UtilitiesCog")
    
    def generate_confirmation_msg(self, players, result, bluffs, fabled):
        msg = "¿Guardar partida con los siguientes datos?\n\n"
        for player in players:
            player_characters = players[player]
            formatted_characters = []
            for raw_character in player_characters:
                char_id = raw_character.split("(")[0]
                character = self.utilities.get_character_name(char_id)
                print(f"Character: {character} ({char_id})")
                if "(" in raw_character:
                    alignment = raw_character[-2]
                    if alignment == "g":
                        alignment = "bueno"
                    elif alignment == "e":
                        alignment = "malvado"
                    else:
                        return None
                else:
                    is_good = self.utilities.is_character_good(char_id)
                    if is_good:
                        alignment = "bueno"
                    else:
                        alignment = "malvado"
                formatted_characters.append(f"{character} ({alignment})")
            msg += f"<@{player}>: {', '.join(formatted_characters)}\n"

        if result == "good":
            result = "Bueno"
        else:
            result = "Malvado"

        msg += f"\nEquipo ganador: **{result}**"

        if bluffs:
            clean_bluffs = []
            for bluff in bluffs:
                clean_bluffs.append(self.utilities.get_character_name(bluff))
            bluffs = ", ".join(clean_bluffs)
            msg += f"\n\n**Demon bluffs:** {bluffs}"
        else:
            msg += "\n\n**Demon bluffs:** El demonio no sabía qué personajes estaban fuera de juego."

        if fabled:
            clean_fabled = []
            for fabled in fabled:
                clean_fabled.append(self.utilities.get_character_name(fabled))
            fabled = ", ".join(clean_fabled)
            msg += f"\n\n**Fabled:** {fabled}"
        else:
            msg += "\n\n**Fabled:** Ninguno"

        return msg
    
    def generate_character_list(self, player=None, team=None):
        player_stats_f = os.path.join("data", "players.json")
        with open(player_stats_f, 'r') as f:
            player_stats = json.load(f)
        if str(player) not in player_stats:
            return False

        all_played_chars = player_stats[player]['characters']
        all_chars = sorted(all_played_chars.items(), key=lambda x: x[1]['games'], reverse=True)

        msg = f"<@{player}> ha jugado con {len(all_chars)} personajes diferentes:\n"

        good_games = player_stats[player]['games_good'] if player_stats[player]['games_good'] > 0 else 0
        evil_games = player_stats[player]['games_evil'] if player_stats[player]['games_evil'] > 0 else 0
        for char in all_chars:
            char_name = self.utilities.get_character_name(char[0])
            char_games = char[1]['games']
            char_stats = all_played_chars[char[0]]
            char_winrate = round(char_stats['winrate'] / char_games * 100)
            total_player_games = good_games + evil_games
            char_percent = round(char_games / total_player_games * 100)

            if char_games == 1:
                s = ""
            else: 
                s = "s"
            msg += f"- **{char_name}**: {char_games}  partida{s}, {char_stats['winrate']} ganada{s} ({char_percent}%, :trophy: {char_winrate}%)\n"

        msg += "\n_Nota: Los personajes con alineamiento alterado cuentan como personajes diferentes._"

        return msg
    
    def generate_generic_character_list(self):
        character_stats_f = os.path.join("data", "characters.json")
        with open(character_stats_f, 'r') as f:
            character_stats = json.load(f)

        games_file = os.path.join("data", "games.json")
        with open(games_file, 'r') as f:
            games = json.load(f)
        total_games = len(games)

        all_chars = sorted(character_stats.items(), key=lambda x: x[1]['games'], reverse=True)

        # Remove fabled from list (irrelevant, and also have different data structure)
        for char in all_chars:
            if self.utilities.is_fabled(char[0]):
                all_chars.remove(char)
        
        all_chars = all_chars[:15]
        msg = "15 personajes con más partidas jugadas:\n"
        for char in all_chars:
            char_name = self.utilities.get_character_name(char[0])
            char_games = char[1]['games']
            char_stats = character_stats[char[0]]
            char_winrate = round(char_stats['winrate'] / char_games * 100)
            char_percent = round(char_games / total_games * 100)

            if char_games == 1:
                s = ""
            else: 
                s = "s"
            msg += f"- **{char_name}**: {char_games}  partida{s}, {char_stats['winrate']} ganada{s} ({char_percent}%, :trophy: {char_winrate}%)\n"

        msg += "\n_Nota: Los personajes con alineamiento alterado cuentan como personajes diferentes._"

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

        if evil_games == 0 and good_games == 0:
            general_winrate_percentage = 0
        else:
            general_winrate_percentage = round((winrate_good + winrate_evil) / (good_games + evil_games) * 100)
        
        print(f"General winrate: {general_winrate_percentage}%")

        all_played_chars = player_stats['characters']
        top_chars = sorted(all_played_chars.items(), key=lambda x: x[1]['games'], reverse=True)[:5] # Ordenar los personajes según el valor de "games" de cada personaje. 0=char id, 1=games player

        top_chars_final = []
        for char in top_chars:
            char_name = self.utilities.get_character_name(char[0])
            char_games = char[1]['games']
            char_stats = player_stats['characters'][char[0]]
            char_winrate = round(char_stats['winrate'] / char_games * 100)
            top_chars_final.append(f"{char_name} ({char_games}, :trophy: {char_winrate}%)")

        embed = discord.Embed(title=f"Estadísticas de {user.display_name}", description=f"Ha participado en {good_games + evil_games} partidas")
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Victorias", value=f"{general_winrate_percentage}%")
        embed.add_field(name="Equipo bueno", value=f"{good_games} (:trophy: {g_winrate_percentage}%)")
        embed.add_field(name="Equipo malvado", value=f"{evil_games} (:trophy: {e_winrate_percentage}%)")
        if not character:
            embed.add_field(name="Personajes más jugados", value=", ".join(top_chars_final))
            embed.set_footer(text="Usa /jugador <jugador> <personaje> para ver estadísticas con un personaje concreto. Las estadísticas de victorias se calculan siempre según al alineamiento final del jugador.")
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
    
    def generate_fabled_stats(self, character):
        character_stats_f = os.path.join("data", "characters.json")
        with open(character_stats_f, 'r') as f:
            full_character_stats = json.load(f)

        with_stats = False
        if character in full_character_stats:
            with_stats = True
        
        if with_stats:
            character_stats = full_character_stats[character]
            total_games = character_stats['games']
            winrate_good = round(character_stats['winrate_good'] / total_games * 100)   
            winrate_evil = round(character_stats['winrate_evil'] / total_games * 100)

        # Set up embed
        char_details = self.utilities.get_character_details(character)
        character = char_details["name"]["es"]
        character_en = char_details["name"]["en"]
        wiki = "https://wiki.bloodontheclocktower.com/" + character_en.replace(" ", "_")

        # Set up the embed
        embed = discord.Embed(title=f"{character_en}", description=char_details["description"]["es"], url=wiki, color=discord.Color.gold())
        embed.set_thumbnail(url=char_details["icon"])
        embed.add_field(name="Tipo", value="Mítico")
        if with_stats:
            embed.add_field(name=f"Partidas", value=f"{character_stats['games']}")
            embed.add_field(name=f"Victoria de los buenos", value=f"{character_stats['winrate_good']} (:trophy: {winrate_good}%)")
            embed.add_field(name=f"Victoria de los malvados", value=f"{character_stats['winrate_evil']} (:trophy: {winrate_evil}%)")
        #embed.add_field(name="En inglés", value=character_en)
        if not with_stats:
            embed.set_footer(text="No tengo partidas guardadas con este personaje.")

        return embed

    def generate_character_stats(self, character):
        character_stats_f = os.path.join("data", "characters.json")
        with open(character_stats_f, 'r') as f:
            full_character_stats = json.load(f)

        with_stats = False
        if character in full_character_stats:
            with_stats = True

        if with_stats:
            character_stats = full_character_stats[character]
            winrate = round(character_stats['winrate'] / character_stats['games'] * 100)

        # Find stats in opposite alignment
        if self.utilities.is_character_good(character):
            opposite = f"{character}(e)"
            team_message = "(equipo bueno)"
            opposite_message = "(equipo malvado)"
        else:
            opposite = f"{character}(g)"
            team_message = "(equipo malvado)"
            opposite_message = "(equipo bueno)"
        print(f"Opposite: {opposite}")
        with_opposite_stats = False
        if opposite in full_character_stats:
            with_opposite_stats = True
        if with_opposite_stats:
            opposite_stats = full_character_stats[opposite]
            opposite_winrate = round(opposite_stats['winrate'] / opposite_stats['games'] * 100)    

        # Set up what appears in the embed
        char_details = self.utilities.get_character_details(character)
        character = char_details["name"]["es"]
        character_en = char_details["name"]["en"]
        type = char_details["type"]
        type_details = { # Fabled missing because it's handled by generate_fabled_stats
            "demon": {"label": "Demonio", "color": discord.Color.red()},
            "minion": {"label": "Secuaz", "color": discord.Color.red()},
            "outsider": {"label": "Forastero", "color": discord.Color.blue()},
            "townsfolk": {"label": "Aldeano", "color": discord.Color.blue()},
            "traveller": {"label": "Viajero", "color": discord.Color.dark_magenta()}
        }
        color = type_details[type]["color"]
        type = type_details[type]["label"]
        wiki = "https://wiki.bloodontheclocktower.com/" + character_en.replace(" ", "_")

        # Set up the embed
        embed = discord.Embed(title=f"{character_en}", description=char_details["description"]["es"], url=wiki, color=color)
        embed.set_thumbnail(url=char_details["icon"])
        embed.add_field(name="Tipo", value=type)
        if with_stats:
            embed.add_field(name=f"Partidas {team_message}", value=f"{character_stats['games']} (:trophy: {winrate}%)")
        if with_opposite_stats:
            embed.add_field(name=f"Partidas {opposite_message}", value=f"{opposite_stats['games']} (:trophy: {opposite_winrate}%)")
        #embed.add_field(name="En inglés", value=character_en)
        if not with_stats and not with_opposite_stats:
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