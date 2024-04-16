import os, json, shutil
from discord.ext import commands
import discord
import time

class UtilitiesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    def clean_id(self, id):
        clean_id = id.replace('<', '').replace('>', '').replace('!', '').replace('@', '').replace('&', '').replace(' ', '')
        try:
            clean_id = int(clean_id)
            return clean_id
        except:
            return False
    
    def is_character_valid(self, character):
        character_data = os.path.join("data", "character_data.json")
        with open(character_data, 'r') as f:
            character_data = json.load(f)
        if character not in character_data:
            if character.endswith(")"): #This means there's a custom alignment!
                character = character[:-3]
                if character not in character_data:
                    return False
                else:
                    return True
            else:
                return False
        else:
            return True #If character is in character data as-is, there's no custom alignment
    
    def is_character_good(self, character):
        if character.endswith(")"): #This means there's a custom alignment!
            alignment = character[-2]
            if alignment == "g":
                return True
            elif alignment == "e":
                return False 
            else:
                return None

        character_data = os.path.join("data", "character_data.json")
        with open(character_data, 'r') as f:
            character_data = json.load(f)
        if character_data[character]["type"] in ["townsfolk", "outsider"]:
            return True
        else:
            return False
    
    def get_character_name(self, character, lang="es"):
        modifier = ""
        if "(" in character:
            modifier = " bueno" if character[-2] == "g" else " malvado"
            character = character.split("(")[0]
        character_data = os.path.join("data", "character_data.json")
        with open(character_data, 'r') as f:
            character_data = json.load(f)

        name = character_data[character]["name"][lang]
            
        return f"{name}{modifier}"

    def get_character_article(self, character):
        character_data = os.path.join("data", "character_data.json")
        with open(character_data, 'r') as f:
            character_data = json.load(f)

        return character_data[character]["article"]["es"]
    
    def get_character_details(self, character):
        character_data = os.path.join("data", "character_data.json")
        with open(character_data, 'r') as f:
            character_data = json.load(f)

        if "(" in character:
            character = character.split("(")[0]

        return character_data[character]

    def generate_game_id(self):
        games_file = os.path.join("data", "games.json")
        with open(games_file, 'r') as f:
            games = json.load(f)
        if len(games) == 0:
            return 0
        else:
            return int(max([int(n) for n in games])) + 1

    def update_game_stats(self, player_data, result):
        game_id = self.generate_game_id()
        game_time = int(time.time()) # Unix timestamp (without decimals), which can be easily displayed on discord as <t:TIMESTAMP:F>
        games_file = os.path.join("data", "games.json")
        with open(games_file, 'r') as f:
            games = json.load(f)
        games[game_id] = {
            "timestamp": game_time,
            "players": player_data,
            "result": result
        }
        with open(games_file, 'w') as f:
            json.dump(games, f)
        return game_id
    
    def update_player_stats(self, player, character, result):
        player_file = os.path.join("data", "players.json")
        with open(player_file, 'r') as f:
            players = json.load(f)

        print(player)
        print(players)
        if player not in players: # Register new player
            players[player] = {
                "games_good": 0,
                "games_evil": 0,
                "winrate_good": 0,
                "winrate_evil": 0,
                "characters": {}
            }

        player_characters = players[player]["characters"]
        if character not in player_characters:
            player_characters[character] = { #Register new played character if first time
                "games": 0,
                "winrate": 0
            }
        player_characters[character]["games"] += 1
        if result == "good" and self.is_character_good(character):
            player_characters[character]["winrate"] += 1

        if self.is_character_good(character):
            players[player]["games_good"] += 1
            if result == "good":
                players[player]["winrate_good"] += 1
        else:
            players[player]["games_evil"] += 1
            if result == "evil":
                players[player]["winrate_evil"] += 1

        with open(player_file, 'w') as f:
            json.dump(players, f)
        return

    def update_character_stats(self, character, result):
        character_file = os.path.join("data", "characters.json")
        with open(character_file, 'r') as f:
            characters = json.load(f)
        
        if character not in characters:
            characters[character] = {
                "games": 0,
                "winrate": 0
            }
        
        characters[character]["games"] += 1
        if self.is_character_good(character):
            if result == "good":
                characters[character]["winrate"] += 1
        else:
            if result == "evil":
                characters[character]["winrate"] += 1

        with open(character_file, 'w') as f:
            json.dump(characters, f)

        return
    
    def generate_confirmation_msg(self, players, result):
        msg = "¿Guardar partida con los siguientes datos?\n\n"
        for player in players:
            print(player)
            char_id = players[player].split("(")[0]
            character = self.get_character_name(char_id)
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
                is_good = self.is_character_good(char_id)
                if is_good:
                    alignment = "bueno"
                else:
                    alignment = "malvado"
                article = self.get_character_article(char_id)
                msg += f"**<@{player}>** era {article}**{character}** ({alignment})\n"

        if result == "good":
            result = "Bueno"
        else:
            result = "Malvado"

        msg += f"\nEquipo ganador: **{result}**"

        return msg
    
    def generate_player_stats(self, player):
        player_stats_f = os.path.join("data", "players.json")
        with open(player_stats_f, 'r') as f:
            player_stats = json.load(f)
        if str(player) not in player_stats:
            return False
        
        player_stats = player_stats[str(player)]
        g_winrate_percentage = round(player_stats['winrate_good'] / (player_stats['games_good']) * 100)
        e_winrate_percentage = round(player_stats['winrate_evil'] / (player_stats['games_evil']) * 100)
        general_winrate_percentage = round((player_stats['winrate_good'] + player_stats['winrate_evil']) / (player_stats['games_good'] + player_stats['games_evil']) * 100)

        msg = f"Estadísticas para <@{player}>:\n\n"
        msg += f"Ha jugado **{player_stats['games_good'] + player_stats['games_evil']} partidas**, de las que ha ganado un {general_winrate_percentage}%:\n"
        msg += f":innocent: {player_stats['games_good']} en el equipo bueno ({g_winrate_percentage}% ganadas)\n"
        msg += f":smiling_imp: {player_stats['games_evil']} en el equipo malvado ({e_winrate_percentage}% ganadas)\n\n"

        all_played_chars = player_stats['characters']
        print(all_played_chars)
        top_chars = sorted(all_played_chars.items(), key=lambda x: x[1]['games'], reverse=True)[:5] # Ordenar los personajes según el valor de "games" de cada personaje
        msg += f"Sus personajes más jugados son:\n"
        for char in top_chars:
            char_name = self.get_character_name(char[0])
            msg += f"1. **{char_name}** ({char[1]['games']} partidas)\n"

        return msg
    
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

        char_details = self.get_character_details(character)
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

        msg = f"Tengo {len(game_stats)} partidas registradas:\n"
        msg += f"El equipo bueno ha ganado un {good_percentage}% y el malvado {evil_percentage}%.\n\n"
        msg += "Personajes más usados:\n"
        for character in top_characters:
            char_name = self.get_character_name(character)
            winrate_absolute = character_stats[character]["winrate"]
            winrate = round(winrate_absolute / character_stats[character]["games"] * 100)
            msg += f"1. {char_name} (:trophy: {winrate}%)\n"

        return msg
    
    def backup_data(self):
        if not os.path.exists("backups"):
            os.makedirs("backups")
        
        shutil.copy(os.path.join("data", "players.json"), os.path.join("backups", "players.json"))
        shutil.copy(os.path.join("data", "characters.json"), os.path.join("backups", "characters.json"))
        shutil.copy(os.path.join("data", "games.json"), os.path.join("backups", "games.json"))
        return


def setup(bot):
    bot.add_cog(UtilitiesCog(bot))