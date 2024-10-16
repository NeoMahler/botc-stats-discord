import os, json, shutil
from discord.ext import commands
import time
from fuzzywuzzy import process

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
        if character_data[character]["type"] in ["townsfolk", "outsider"]: # All Travellers in stats should have the alignment modifier (e) or (g)
            return True
        else:
            return False
    
    def get_character_name(self, character, lang="en"):
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
    
    def did_player_win(self, characters, result):
        last_character = characters[-1]
        character_alignment = self.is_character_good(last_character)
        if character_alignment is True:
            if result == "good":
                return True
        if character_alignment is False:
            if result == "evil":
                return True
        return False
    
    def did_player_end_good(self, characters):
        last_character = characters[-1]
        return self.is_character_good(last_character)

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
    
    def update_player_stats(self, player, characters, result):
        player_file = os.path.join("data", "players.json")
        with open(player_file, 'r') as f:
            players = json.load(f)

        if player not in players: # Register new player
            players[player] = {
                "games_good": 0,
                "games_evil": 0,
                "winrate_good": 0,
                "winrate_evil": 0,
                "characters": {}
            }

        player_characters = players[player]["characters"]
        player_won = self.did_player_win(characters, result) # True if won, False if lost (based on the character they had at game end)
        for character in characters:
            if character not in player_characters:
                player_characters[character] = { #Register new played character if first time
                    "games": 0,
                    "winrate": 0
                }
            # TODO: Winrate should be based on whether the last character won or not
            player_characters[character]["games"] += 1
            if player_won:
                player_characters[character]["winrate"] += 1

            player_ended_good = self.did_player_end_good(characters)
            if player_ended_good:
                players[player]["games_good"] += 1
                if result == "good":
                    players[player]["winrate_good"] += 1
            else:
                players[player]["games_evil"] += 1
                if result == "evil":
                    players[player]["winrate_evil"] += 1
            
            self.update_character_stats(character, result)

        with open(player_file, 'w') as f:
            json.dump(players, f)
        return

    def update_character_stats(self, character, result):
        character_file = os.path.join("data", "characters.json")
        with open(character_file, 'r') as f:
            characters = json.load(f)
        
        print(f"Characters: {characters.keys()} // Character: {character}")
        if character not in set(characters):
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
    
    def backup_data(self):
        if not os.path.exists("backups"):
            os.makedirs("backups")
        
        shutil.copy(os.path.join("data", "players.json"), os.path.join("backups", "players.json"))
        shutil.copy(os.path.join("data", "characters.json"), os.path.join("backups", "characters.json"))
        shutil.copy(os.path.join("data", "games.json"), os.path.join("backups", "games.json"))
        return
    
    def get_config(self):
        config_file = "config.json"
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config

    def get_player_type(self, player):
        config = self.get_config()
        player_role = int(config["player_role"])
        st_role = int(config["st_role"])

        player_role_ids = []
        for role in player.roles:
            player_role_ids.append(role.id)

        if st_role in player_role_ids:
            return "st"
        elif player_role in player_role_ids:
            return "player"
        else:
            return False

    def get_player_name(self, player):
        if player.global_name:
            return player.global_name
        else:
            return player.display_name
        
    async def update_player_details(self, player):
        player_file = os.path.join("data", "player_details.json")
        user = self.bot.get_user(player)
        if user is None:
            user = await self.bot.fetch_user(player)

        print(user)

        with open(player_file, 'r') as f:
            player_details = json.load(f)

        player_details[str(player)] = {
            "username": user.name,
            "display_name": user.display_name,
            "global_name": user.global_name
        }

        with open(player_file, 'w') as f:
            json.dump(player_details, f)
        return
    
    def get_player_from_data(self, data):
        player_file = os.path.join("data", "player_details.json")
        with open(player_file, 'r') as f:
            player_details = json.load(f)
        
        all_options = []
        for player in player_details:
            for value in player_details[player].values():
                all_options.append(value)
                if value == data:
                    return player

        try:
            fuzzy_match = process.extract(data, all_options, limit=1)[0][0] #fuzzywuzzy
        except:
            return False            

        for player in player_details:
            for value in player_details[player].values():
                if value == fuzzy_match:
                    return player

        return False

def setup(bot):
    bot.add_cog(UtilitiesCog(bot))