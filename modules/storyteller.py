import random, asyncio
from discord.ext import commands
from discord.commands import Option, slash_command
import discord

class StorytellerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utilities = bot.get_cog("UtilitiesCog")
    
    @slash_command(name="boomdandy", description="Boom!")
    async def boomdandy(self, ctx, players: Option(str, "Space-separated list of surviving players (using Discord mentions).")):
        if self.utilities.get_player_type(ctx.author) != "st": # Avoid activation by regular players
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
        msg = "# ¡El Boomdandy ha explotado!\n"
        msg += f"Los supervivientes son: {' '.join(pings)}\n\n"
        msg += "Tenéis **1 minuto** para decidir quién va a morir. Usad los botones para escogerlo."


        self.BoomdandyUI.result = {} # Empty the dictionary, otherwise it would carry over the survivors form the previous game
        view = self.BoomdandyUI(ctx, self.bot, player_members)
        await ctx.respond(msg, view=view)

        await asyncio.sleep(60) # Wait for the "vote" to end
        view.disable_all_items() # Disable the buttons
        await ctx.edit(view=view)
        result = self.BoomdandyUI.result
        msg = "## :bomb: **TIEMPO** :bomb:\n\n"
        msg += "Resultados:\n"
        for player in result:
            msg += f"**<@{player}>**: {', '.join([f'<@{user}>' for user in result[player]])} (**{len(result[player])} votos**)\n"
        await ctx.send(msg)
        return 

    class BoomButton(discord.ui.Button):
        def __init__(self, ctx, bot, player_name, player):
            super().__init__(label=f"👉 {player_name}", style=discord.ButtonStyle.primary)
            self.utilities = bot.get_cog("UtilitiesCog")
            self.ctx = ctx
            self.disabled = False
            self.player = player
        
        async def callback(self, interaction):
            emojis = [":bomb:", ":scream:", ":smirk:", ":zany_face:", ":nerd:", ":disguised_face:", ":flushed:", ":face_in_clouds:", ":face_with_peeking_eye:", ":shaking_face:", ":smiling_imp:", ":clown:", ":skull:", ":spy:"]
            emoji = random.choice(emojis)
            if self.utilities.get_player_type(interaction.user) != "player": # Prevent non-players (and ST) from voting
                await interaction.response.send_message("No estás jugando, así que no puedes participar en la votación.", ephemeral=True)
                return
            await interaction.response.defer() # Prevent button from being unresponsive for 3 seconds and erroring out
            await self.ctx.send(f"<@{interaction.user.id}> está apuntando a <@{self.player.id}> {emoji}")
            result_dict = StorytellerCog.BoomdandyUI.result
            for player in result_dict: # Avoid duplicates
                if interaction.user.id in result_dict[player]:
                    result_dict[player].remove(interaction.user.id) # Remove the voter from the previous votee (if any)
            result_dict[self.player.id].append(interaction.user.id)
            return
        
    class BoomdandyUI(discord.ui.View):
        result = {} # Accessible from other methods
        def __init__(self, ctx, bot, players):
            super().__init__()
            self.players = players
            self.ctx = ctx
            self.bot = bot
            self.utilities = bot.get_cog("UtilitiesCog")

            for player in players:
                self.result[player.id] = []
                player_name = self.utilities.get_player_name(player)
                self.add_item(StorytellerCog.BoomButton(ctx, self.bot, player_name, player))


def setup(bot):
    bot.add_cog(StorytellerCog(bot))