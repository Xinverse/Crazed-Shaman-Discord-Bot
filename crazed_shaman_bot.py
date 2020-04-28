# TODO LIST
# 1 - Fedit command & error
# 2 - Hour of Werewolf
# 3 - Bugs in name recognition
# 4 - Check with no arguments return user
# 5 - fsync bug


import discord
import random
import pymongo
import threading
import datetime
import time
import re
from collections import deque
import os
from dotenv import load_dotenv

# ----- CONFIG VARIABLES ----------------------------------------------------------------------------------------------
# Logins, settings, esthetics
# -----------------------------------------------------------------------------------------------------------------

# Secret

load_dotenv()
TOKEN = os.getenv("TOKEN")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")

# User settings - Example of settings vars are in comments, using fictitious data

PREFIX = "."
# LOGGING_CHANNEL = "269670622647418891"
LOGGING_CHANNEL = os.getenv("LOGGING_CHANNEL")  # This is where the bot logs its actions
# TALKING_CHANNEL = "269670622647418892"
TALKING_CHANNEL = os.getenv("TALKING_CHANNEL")  # This is where the bot is allowed to talk and reply to commands
# IGNORE_CHANNEL = []
IGNORE_CHANNEL = eval(os.getenv("IGNORE_CHANNEL"))  # Channels ignored for activity points
# SUGGESTIONS_CHANNEL = "264332315762693122"
SUGGESTIONS_CHANNEL = os.getenv("SUGGESTIONS_CHANNEL")
# DEBUG_LOGS_CHANNEL = "251899453068510880"
DEBUG_LOGS_CHANNEL = os.getenv("DEBUG_LOGS_CHANNEL")
# LOBBY_CHANNEL = "251752208980683772"
LOBBY_CHANNEL = os.getenv("LOBBY_CHANNEL")
# SERVER_ID = "251752096906208258"
SERVER_ID = os.getenv("SERVER_ID")
PLAYER_ROLE_NAME = "Players"
# WEREWOLF_BOT = "251745173016068096"
WEREWOLF_BOT = os.getenv("WEREWOLF_BOT")
WHALE_WOLF_PREFIX = "!"
# BOT_OWNER = ["201326114285750788"]
BOT_OWNER = eval(os.getenv("BOT_OWNER"))
# BOT_ADMINS = ["300426113145750785", "302921511763022889", "593592507102314496"]
BOT_ADMINS = eval(os.getenv("BOT_ADMINS"))
HOW_ROLE = "Hour of WW"

# Bot configurations
MIN_CHARACTERS = 7  # Minimum number of characters in a message in order to be awarded a point
POINTS_PER_MSG = 1  # Number of points awarded per eligible message (DEFAULT to 1)
DOWN_TIME = 3600  # How frequently should scores decay in seconds (DEFAULT to 3600)
SPAM_TIMER = 11  # Similar to Whale-Wolf ignore (DEFAULT to 11)
BACKUP_TIMER = 3600 * 12  # How frequently should scores be backed up?
SPAM_TOLERATED = 6  # Similar to Whale-Wolf ignore (DEFAULT to 6)
LEADERBOARD_MAX = 10  # Maximum number of users that show up on the leaderboard
RECORD_MAX = 10  # Maximum number of users that show up on the record board

# Esthetics
COLOR_LEADERBOARD = 0x9cf700  # Color of the leaderboard embed
COLOR_RECORD = 0x00d9f9  # Color of the record board embed
COLOR_ACTIVITY = 0xff0081  # Color of the individual activity board
COLOR_NORMAL = 0x1900be  # Color of all other bot messages
EMBED_HEADER = "Discord Werewolf Server"
EMBED_FOOTER = "Brought to you by the Village's favourite Crazed Shaman!"

# ----- UTILITY ----------------------------------------------------------------------------------------------
# Utility functions and other variables
# -----------------------------------------------------------------------------------------------------------------

client = discord.Client()

mongo_connector = pymongo.MongoClient(MONGO_PASSWORD)

db_werewolf = mongo_connector.werewolf

# Collections for activity related data
col_players = db_werewolf.players  # Database for server activity points
col_backup = db_werewolf.backup  # Backup for col_players
col_temp = db_werewolf.temporary  # Temporary collection, for operations

# Collections for ratings related data
col_ratings = db_werewolf.ratings  # Player ratings

rate_limit_dict = {}
bootTime = 0
darkener_houserule = False

village_roles = [

    "seer", "oracle", "shaman", "harlot", "hunter", "augur", "detective", "matchmaker", "guardian angel", "bodyguard",
    "priest", "village drunk", "mystic", "mad scientist", "time lord", "villager"

]

wolf_roles = [

    "wolf", "werecrow", "doomsayer", "wolf cub", "werekitten", "wolf shaman", "wolf mystic", "traitor", "hag",
    "sorcerer", "warlock", "minion", "cultist"

]

neutral_roles = [

    "jester", "crazed shaman", "monster", "piper", "amnesiac", "fool", "vengeful ghost", "succubus", "clone", "lycan",
    "turncoat", "serial killer", "executioner", "hot potato"

]

all_roles = village_roles + wolf_roles + neutral_roles

gamemodes = [

    "aleatoire", "charming", "default", "evilvillage", "foolish", "lycan", "mad", "mudkip", "noreveal", "belunga",
    "bloodbath", "chaos", "crazy", "drunkfire", "orgy", "random", "rapidfire", "valentines"

]

usable_commands = {

    "uptime": {
        "aliases": ["uptime"],
        "description": "Check the time during which the bot is in operation since its last reboot.",
        "permissions": 0,
        "usage": PREFIX + "uptime"
    },

    "leaderboard": {
        "aliases": ["lead", "lb", "leaderboard"],
        "description": "See the leaderboard of current Activity Points.",
        "permissions": 0,
        "usage": PREFIX + "leaderboard"
    },

    "activity": {
        "aliases": ["activity", "act", "me"],
        "description": "See your activity statistics.",
        "permissions": 0,
        "usage": PREFIX + "activity"
    },

    "ping": {
        "aliases": ["ping", "pong"],
        "description": "Check the responsiveness and latency of the bot.",
        "permissions": 0,
        "usage": PREFIX + "ping"
    },

    "record": {
        "aliases": ["record", "rec", "records"],
        "description": "See the leaderboard of historical Activity Points highscores.",
        "permissions": 0,
        "usage": PREFIX + "record"
    },

    "check": {
        "aliases": ["check"],
        "description": "Check the activity statistics of a specified user.",
        "permissions": 0,
        "usage": PREFIX + "check <user_id> / <username#1234>"
    },

    "information": {
        "aliases": ["info", "information"],
        "description": "See a panel showing the general information of the bot.",
        "permissions": 0,
        "usage": PREFIX + "information"
    },

    "freset_activity": {
        "aliases": ["freset_activity"],
        "description": "Reset the activity database, and clear all data.",
        "permissions": 2,
        "usage": PREFIX + "freset_activity"
    },

    "freset_ratings": {
        "aliases": ["freset_ratings"],
        "description": "Reset the ratings database, and clear all data.",
        "permissions": 2,
        "usage": PREFIX + "freset_ratings"
    },

    "credits": {
        "aliases": ["credits", "cred", "credit"],
        "description": "See a panel showing the credits.",
        "permissions": 0,
        "usage": PREFIX + "credits"
    },

    "list": {
        "aliases": ["list"],
        "description": "See a list of usable commands.",
        "permissions": 0,
        "usage": PREFIX + "list"
    },

    "fbackup": {
        "aliases": ["fbackup"],
        "description": "Create a backup of the database from its current state.",
        "permissions": 1,
        "usage": PREFIX + "fbackup"
    },

    "fload_backup": {
        "aliases": ["fload_backup"],
        "description": "Delete the current database, and load data from the last backup.",
        "permissions": 2,
        "usage": PREFIX + "fload_backup"
    },

    "fsync": {
        "aliases": ["fsync"],
        "description": "Synchronize the database, and remove duplicates.",
        "permissions": 1,
        "usage": PREFIX + "fsync"
    },

    "help": {
        "aliases": ["help"],
        "description": "See helpful information about a command.",
        "permissions": 0,
        "usage": PREFIX + "help <command>"
    },

    "fedit": {
        "aliases": ["fedit"],
        "description": "Manually edit a document within the database. `points`: current activity points. "
                       "`messages`: number of messages within the decay interval. `highest`: record highscore.",
        "permissions": 1,
        "usage": PREFIX + "fedit <user_id> <field: points/messages/highest> <operator: +/-/=> <integer>"
    },

    "fremove_how": {
        "aliases": ["fremove_how"],
        "description": "Remove the Hour of Werewolf (HoW) role from members who have it.",
        "permissions": 1,
        "usage": PREFIX + "fremove_how"
    },

    "join": {
        "aliases": ["join", "j"],
        "description": "... No comment... This is only for the happy few who recognize the joke.",
        "permissions": 0,
        "usage": PREFIX + "join"
    },

    "fdarkener": {
        "aliases": ["fdarkener"],
        "description": "Toggle the Darkener Houserule (no vowels allowed except for bot commands).",
        "permissions": 1,
        "usage": PREFIX + "fdarkener"
    },

    "github": {
        "aliases": ["github"],
        "description": "See the link to the public Github repository.",
        "permissions": 0,
        "usage": PREFIX + "github"
    },

    "role": {
        "aliases": ["role"],
        "description": "Get a list of all members with a certain role.",
        "permissions": 0,
        "usage": PREFIX + "role <role_name>"
    }

}


# Class to store the game data
class GameData:

    def __init__(self):

        self.gamemode = None
        self.correspondences = {}
        self.player_list = []
        self.player_list_temp = []
        self.winners = []

    def clear(self):

        self.__init__()

    def set_player_list(self, player_list):

        self.player_list = player_list
        self.player_list_temp = player_list

    def eliminate_player(self, userid):

        answer = str(userid) in [str(i) for i in self.player_list_temp]
        if answer:
            self.player_list_temp.remove(int(userid))
        return answer

    def set_correspondence(self, dic):

        self.correspondences = dic

    def set_gamemode(self, mode):

        self.gamemode = mode

    def set_winners(self, winners):

        self.winners = winners

    def display(self):

        def make_bold(string):
            return "**{}**".format(string)
        display_str = ""
        for key in self.correspondences:
            user = client.get_user(int(key))
            role = self.correspondences[key]
            display_str += make_bold(user.name) if user else make_bold(key)
            display_str += " is " + make_bold(role)
            display_str += " ; "
        display_str += " Played using the **{}** mode.".format(self.gamemode)
        return display_str

    def push_to_database(self):

        for userid, rolename in self.correspondences.items():
            userid = str(userid)  # 600426113285750785
            rolename = str(rolename)   # "crazed shaman"
            gamemode = str(self.gamemode)  # "default"
            total = "total"  # "total"
            col_ratings.update_one(
                {"_id": userid},
                {"$inc": {rolename: 1, gamemode: 1, total: 1}},
                upsert=True
            )
        for userid in self.winners:
            rolename_win = str(self.correspondences[userid]) + " win"  # "crazed shaman win"
            gamemode_win = str(self.gamemode) + " win"  # "default win"
            total_win = "total win"  # "total win"
            col_ratings.update_one(
                {"_id": userid},
                {"$inc": {rolename_win: 1, gamemode_win: 1, total_win: 1}},
                upsert=True
            )

    def preview_db_query(self):

        def make_bold(string):
            return "**{}**".format(string)

        display_str = ""

        for key in self.correspondences:
            user = client.get_guild(int(SERVER_ID)).get_member(int(key))
            role = self.correspondences[key]
            display_str += make_bold(user.display_name) if user else make_bold(key)
            display_str += " is " + make_bold(role)
            display_str += " ; "

        display_str += " Played using the **{}** mode ; ".format(self.gamemode)
        winners_str = "The winners are: "

        if self.winners:
            for winner_id in self.winners:
                user = client.get_guild(int(SERVER_ID)).get_member(int(winner_id))
                winners_str += make_bold(user.nick) if user else make_bold(winners_id)
                winners_str += "; "
        else:
            winners_str += make_bold("None")

        return display_str + winners_str


current_game = GameData()


# Turn user ID into a ping
def make_ping(userID):
    userID = str(userID)
    namePing = "<@%s>" % (userID)
    return namePing


# Lower the score of short burst spammers
def punish_spammers(score):
    newscore = int(max(score - 25, 0) * 0.99)
    return newscore


# Restrict spammers
def restrict_spammers(userid):

    global rate_limit_dict
    userid = str(userid)

    if userid not in rate_limit_dict:
        rate_limit_dict[str(userid)] = 1

    else:
        rate_limit_dict[str(userid)] = rate_limit_dict[str(userid)] + 1
        if rate_limit_dict[str(userid)] >= SPAM_TOLERATED:
            query = {"userid": str(userid)}
            lookup = col_players.find(query)
            temp = list(lookup)
            print(temp)
            lookup_dict = dict(temp[0])
            old_score = lookup_dict["points"]
            new_score = punish_spammers(old_score)
            col_players.update_one({"userid": str(userid)}, {"$set": {"points": new_score}})


# Checks if user is in server
def is_in_server(userid):
    userid = int(userid)
    server = client.get_guild(int(SERVER_ID))
    user = server.get_member(userid)
    return user


# Checks if it's a command
def is_command(message):
    prefix = message[0]
    return prefix == PREFIX and len(message) > 1


# Gets the (unique) parameter, or first word of a list of parameters
def get_parameter(message):
    sliced = message.split()
    keyword = sliced[1]
    keyword = keyword.strip()
    return keyword


# Gets all the parameters
def get_all_parameters(message):
    sliced = message.split()
    keyword = sliced[1:]
    keyword = " ".join(keyword)
    keyword = keyword.strip()
    return keyword


# Checks if a string is a number
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


# Find a person
def get_person(string):
    string = string.strip('<@!>')
    found_by_id = None
    server = client.get_guild(int(SERVER_ID))
    if is_int(string):
        found_by_id = server.get_member(int(string))
    found_by_username = server.get_member_named(string)
    if found_by_id:
        return found_by_id
    else:
        return found_by_username


# Handles commands
def handles_command(message, keywords, needs_argument, clearance_level, userid):
    """
    :param message: string
    :param keywords: list
    :param needs_argument: int
    :param clearance_level: integer
        # 0 - Everyone may use the command
        # 1 - Admins only
        # 2 - Owner only
    :param userid: int
    :return: integer
        # 0 - Not a command
        # 1 - Command recognized and argument detected
        # 2 - Command recognized but missing argument
        # 3 - Command recognized but not enough clearance level
    """
    if is_command(message):

        userid = str(userid)
        everthing_except_prefix = message[1:]
        message_spliced = everthing_except_prefix.split()
        command = message_spliced[0]

        # It is the command we are currently comparing! Return values will be true now
        if command.lower() in keywords:

            # The command needs at least one argument
            if needs_argument:

                # We have the correct number of args
                if len(message_spliced) == needs_argument + 1:

                    # Everyone can use the command
                    if clearance_level == 0:
                        return 1

                    # Bot admins only
                    elif clearance_level == 1:
                        return 1 if userid in BOT_ADMINS else 3

                    # Bot owners only
                    elif clearance_level == 2:
                        return 1 if userid in BOT_OWNER else 3

                # Incorrect number of args
                else:
                    return 2

            # No arguments needed
            else:

                # Everyone can use the command
                if clearance_level == 0:
                    return 1

                # Bot admins only
                elif clearance_level == 1:
                    return 1 if userid in BOT_ADMINS else 3

                # Bot owners only
                elif clearance_level == 2:
                    return 1 if userid in BOT_OWNER else 3

        # It's not this command
        else:
            return 0


# Activate the darkener houserule
async def darkener(message):
    global darkener_houserule
    if darkener_houserule:
        vowels = {"a", "e", "i", "o", "u", "A", "E", "I", "O", "U"}
        if not message.content.startswith(WHALE_WOLF_PREFIX):
            if any(char in vowels for char in message.content):
                await message.author.send(message.author.name + " You have sent a vowel: \n> " + message.content)
                moderator = client.get_user(int(BOT_OWNER[0]))
                await moderator.send(message.author.name + " has sent a vowel: \n> " + message.content)


# Check if the author of the message is whale-wolf
def is_author_whale_wolf(message):
    return message.author.id == int(WEREWOLF_BOT)


# Check if the message is sent in the lobby
def is_in_lobby_channel(message):
    return message.channel.id == int(LOBBY_CHANNEL)


# Check if the message is a game start message - using lobby message
def is_game_start_message(message):
    if is_author_whale_wolf(message) and is_in_lobby_channel(message):
        return message.content.endswith("If you did not receive a pm, please let belungawhale know.")


# Check if the message is a game over message - using lobby message
def is_game_over_message(message):
    if is_author_whale_wolf(message) and is_in_lobby_channel(message):
        return "Game over!" in message.content or "Cancelling game." in message.content


# Get all players in game - using lobby message
def get_all_players(message):
    splited = message.content.split(",")
    players = splited[0].split()
    players_id = [int(player.strip("<@>")) for player in players]
    return players_id


# Check if a message is sent in debug logs
def is_in_debug_channel(message):
    return message.channel.id == int(DEBUG_LOGS_CHANNEL)


# Check if a message is winner message - using logs
def is_winner_message(message):
    if is_author_whale_wolf(message) and is_in_debug_channel(message):
        return message.content.startswith("[INFO] WINNERS:")


# Get the winner id - using logs
def parse_winners(message):
    if message.content == "[INFO] WINNERS: None":
        return None
    raw_string = message.content
    temp = raw_string.strip("[INFO] WINNERS:")
    temp = temp.split(",")
    temp = [part.strip("' ") for part in temp]
    return temp


# Check if a message is a game object message - using logs
def is_game_object_message(message):
    if is_author_whale_wolf(message) and is_in_debug_channel(message):
        return message.content.startswith("[INFO] Game object:")


# Check if a string is a werewolf role name
def is_role_name(string):
    return string.lower() in all_roles


# Check if a string is a werewolf gamemode name
def is_gamemode_name(string):
    return string.lower() in gamemodes


# Parse the game object message - using logs
def parse_game_object_message(message):

    temp = re.split(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', message.content)
    clean_words = deque()

    for i in temp:
        i = i.strip()
        if i:
            word = ''.join(element for element in i if element.isalnum() or element == " ")
            if word:
                clean_words.append(word)

    # Check if a string is a player id who joined
    def is_player_id(string):
        return current_game.eliminate_player(string)

    looking_for_role = False
    final_key = []
    final_value = []

    for i in range(len(clean_words)):
        item = clean_words.popleft()
        if is_player_id(item):
            final_key.append(item)
            looking_for_role = True
        elif is_role_name(item) and looking_for_role:
            final_value.append(item)
            looking_for_role = False
        elif is_gamemode_name(item):
            current_game.set_gamemode(item)
            break

    zipped = dict(zip(final_key, final_value))
    current_game.set_correspondence(zipped)


# Send a message to logs
async def log(msg):
    channel = client.get_channel(int(LOGGING_CHANNEL))
    await channel.send(msg)


@client.event
async def on_message(message):

    global darkener_houserule
    global current_game
    messenger = message.author

    # ----- EXIT CONDITIONS -------------------------------------------------------------------------------------------
    # Proceed only if none of these exiting conditions are met
    # -----------------------------------------------------------------------------------------------------------------

    # Bot should not reply to itself
    if messenger == client.user:
        return

    # Another bot is talking
    elif messenger.bot:

        # Lobby game start message detected
        if is_game_start_message(message):
            current_game.clear()
            current_game.set_player_list(get_all_players(message))
            await log("Game started with these players: " + str(get_all_players(message)))

        # Logs game start message detected
        elif is_game_object_message(message):
            parse_game_object_message(message)
            #await log("**LOGS** Game info temporary data (to-do!): " + current_game.display())

        # Lobby game over message detected
        elif is_game_over_message(message):
            await log("Game over")
            if darkener_houserule:
                await log(make_ping(BOT_OWNER[0]) + " Darkener Houserule is now disabled.")
            darkener_houserule = False

        # Logs game over message detected
        elif is_winner_message(message):
            current_game.set_winners(parse_winners(message))
            await log(current_game.preview_db_query())
            current_game.push_to_database()
            await log("**LOGS** Winners detected: " + str(parse_winners(message)))
            current_game.clear()

        # Ignore bots other than whale-wolf
        else:
            return

    # Bot should ignore utility messages (green arrows)
    elif message.type != discord.MessageType.default:
        return

    post = message.content
    werewolf_bot = client.get_guild(int(SERVER_ID)).get_member(int(WEREWOLF_BOT))

    # ----- BOT COMMANDS ----------------------------------------------------------------------------------------------
    # Bot commands
    # -----------------------------------------------------------------------------------------------------------------

    # Using commands outside of channel
    if post.startswith(PREFIX):
        if str(message.channel.id) != TALKING_CHANNEL:
            if str(messenger.id) not in BOT_ADMINS:
                restrict_spammers(messenger.id)
                return
            # Only bot admins may use commands elsewhere
            else:
                pass

    ############################################################################################################################ UNFINISHED - start

    if handles_command(post, ["debug"], False, 2, messenger.id):
        await message.channel.send(":ok_hand:")

    # ===== Edit command
    elif handles_command(post, ["fedit"], 4, 1, messenger.id):
        check = handles_command(post, ["fedit"], 4, 1, messenger.id)
        # fedit <user_id> <field: points/messages/highest> <operator: +/-/=> <integer>
        if check == 1:
            await message.channel.send("TODO - not yet implemented")
        elif check == 2:
            await message.channel.send(make_ping(messenger.id) + " :x: Invalid format: incorrect number of arguments.")
        elif check == 3:
            await message.channel.send(make_ping(messenger.id) + " :heart_exclamation: "
                                                                 "You do not have the permissions to use this command.")

    ############################################################################################################################ UNFINISHED - end

    # ===== Ping command
    elif handles_command(post, ["ping", "pong"], False, 0, messenger.id):
        sentTime = message.created_at
        msg = make_ping(messenger.id) + " :ping_pong: **PONG!**"
        now = datetime.datetime.utcnow()
        lat = str(now - sentTime).split(":")[-1]
        await message.channel.send(msg + " Latency: **{}** milliseconds.".format(round(float(lat) * 1000)))

    # ===== Github command
    elif handles_command(post, ["github"], False, 0, messenger.id):
        msg = "The bot's code can be found at: https://github.com/Xinverse/crazed_shaman"
        await message.channel.send(msg)

    # ===== Darkener Houserule command
    elif handles_command(post, ["fdarkener"], False, 1, messenger.id):
        darkener_houserule = not darkener_houserule
        if darkener_houserule:
            await message.channel.send(":spider_web: **The Darkener Houserule is now in effect.** "
                                       "Don't forget to turn it off!")
            await log(make_ping(BOT_OWNER[0]) + " Darkener Houserule enabled.")
        else:
            await message.channel.send("**The Darkener Houserule is now cancelled.**")

    # ===== Role command
    elif handles_command(post, ["role"], False, 0, messenger.id):
        role_name = get_all_parameters(post)
        if role_name:
            role = discord.utils.get(message.guild.roles, name=role_name)
            if role:
                members_with_role = role.members
                nb = len(members_with_role)
                msg1 = "Found {} members.".format(str(nb))
                if members_with_role:
                    temp = [make_ping(str(member.id)) for member in members_with_role]
                    msg2 = " ".join(temp)
                else:
                    msg2 = "No member found."
                embed = discord.Embed(title="Discord Werewolf Crazed Shaman Bot", color=COLOR_NORMAL)
                embed.set_author(name=EMBED_HEADER, icon_url=client.get_guild(int(SERVER_ID)).icon_url)
                embed.set_footer(text=EMBED_FOOTER)
                embed.add_field(name="**Info for role {}**".format(role.name), value=msg1, inline=False)
                embed.add_field(name="**Members with role {}**".format(role.name), value=msg2, inline=False)
                try:
                    await message.channel.send(embed=embed)
                except discord.errors.HTTPException:
                    await message.channel.send("Found **{}** members with the specified role. "
                                               "Too lengthy to display the list.".format(nb))
            else:
                await message.channel.send(make_ping(messenger.id) + ":x: Role not found. "
                                                                     "Check your spelling and capitalization!")
        else:
            await message.channel.send(make_ping(messenger.id) + ":x: Please specify the role name")

    # ===== Remove HoW command
    elif handles_command(post, ["fremove_how"], False, 1, messenger.id):
        check = handles_command(post, ["fremove_how"], False, 1, messenger.id)
        if check == 1:
            how_role = discord.utils.get(message.guild.roles, name=HOW_ROLE)
            for member in message.guild.members:
                if how_role in member.roles:
                    await member.remove_roles(how_role)
            await message.channel.send(" :thumbsup: Hour of Werewolf role successfully removed from all users.")
        elif check == 3:
            await message.channel.send(make_ping(messenger.id) + " :heart_exclamation: "
                                                                 "You do not have the permissions to use this command.")

    # ===== Help command
    elif handles_command(post, ["help"], 1, 0, messenger.id):
        check = handles_command(post, ["help"], 1, 0, messenger.id)
        if check == 1:
            keyword = get_parameter(post)
            if keyword.lower() in usable_commands.keys():
                embed = discord.Embed(title="DISCORD WEREWOLF LEADERBOARD BOT", color=COLOR_NORMAL)
                name = "Command `{p}{c}`".format(p=PREFIX, c=keyword.lower())
                msg = "**Aliases** : {aliases} \n" \
                      "**Description** : {description} \n" \
                      "**Usage** : {usage} \n" \
                      "**Permissions** : {permissions}".format(
                                                                aliases=usable_commands[keyword.lower()]["aliases"],
                                                                description=usable_commands[keyword.lower()][
                                                                    "description"],
                                                                usage=usable_commands[keyword.lower()][
                                                                    "usage"],
                                                                permissions=usable_commands[keyword.lower()][
                                                                    "permissions"]
                                                            )
                embed.add_field(name=name, value=msg, inline=False)
                await message.channel.send(embed=embed)
            else:
                msg = make_ping(messenger.id) + " :x: Incorrect argument received."
                await message.channel.send(msg)
        elif check == 2:
            msg = "Type `{p}help <command>` to view the information on how to use the command. To view a list of " \
                   "commands, type `{p}list`.".format(p=PREFIX)
            await message.channel.send(msg)

    # ===== List command
    elif handles_command(post, ["list"], False, 0, messenger.id):
        cmd_list = list(usable_commands.keys())
        cmd_list.sort()
        separator = "`, `{p}".format(p=PREFIX)
        msg = "`{p}".format(p=PREFIX)
        msg += separator.join(cmd_list)
        msg += "`"
        await message.channel.send(make_ping(messenger.id) + " Here is a list of usable commands. The bot's prefix "
                                                             "is `{p}`. Type `{p}help <command>` to learn about its "
                                                             "usage. Commands starting with `f` (for 'force') "
                                                             "can only be used by Admins. \n".format(p=PREFIX) + msg)

    # ===== Sync command
    elif handles_command(post, ["fsync"], False, 1, messenger.id):
        check = handles_command(post, ["fsync"], False, 1, messenger.id)
        if check == 1:
            await message.channel.send("Please hold... **Syncing** operation may take a few seconds...")
            col_temp.drop()
            uniques = col_players.distinct("userid")
            for userid in uniques:
                query = {"userid": str(userid)}
                lookup = col_players.find(query)
                col_temp.insert(lookup)
            col_players.drop()
            for doc in col_temp.find():
                col_players.insert(doc)
            col_temp.drop()
            await message.channel.send("**Activity database successfully synced. All duplicates have been removed.**")
        elif check == 3:
            await message.channel.send(make_ping(messenger.id) + " :heart_exclamation: "
                                                                 "You do not have the permissions to use this command.")

    # ===== Backup command
    elif handles_command(post, ["fbackup"], False, 1, messenger.id):
        check = handles_command(post, ["fbackup"], False, 1, messenger.id)
        if check == 1:
            await message.channel.send("Please hold... **Backup** operation may take a few seconds...")
            col_backup.drop()
            for doc in col_players.find():
                col_backup.insert(doc)
            await message.channel.send("**Activity database successfully backed up. All stored data have been copied "
                                       "to the backup database.**")
        elif check == 3:
            await message.channel.send(make_ping(messenger.id) + " :heart_exclamation: "
                                                                 "You do not have the permissions to use this command.")

    # ===== Load Backup command
    elif handles_command(post, ["fload_backup"], False, 2, messenger.id):
        check = handles_command(post, ["fload_backup"], False, 2, messenger.id)
        if check == 1:
            await message.channel.send("Please hold... **Loading** operation may take a few seconds...")
            col_players.drop()
            for doc in col_backup.find():
                col_players.insert(doc)
            await message.channel.send("**Activity database successfully deleted. The data from the backup database "
                                       "have been fully loaded.**")
        elif check == 3:
            await message.channel.send(make_ping(messenger.id) + " :heart_exclamation: "
                                                                 "You do not have the permissions to use this command.")

    # ===== Uptime command
    elif handles_command(post, ["uptime"], False, 0, messenger.id):
        uptime = time.time() - bootTime
        uptime = round(uptime)
        uptimeStr = str(datetime.timedelta(seconds=uptime))
        msg = make_ping(messenger.id) + " :hourglass: **Uptime:** " + uptimeStr
        await message.channel.send(msg)

    # ===== Record command
    elif handles_command(post, ["record", "records", "rec"], False, 0, messenger.id):

        msg = ""
        lb = col_players.find().sort("highest", -1)

        counter = 1

        for i in lb:
            i = dict(i)
            user_id = i["userid"]
            pt = i["highest"]
            # Users with 0 point should not show up on the leaderboard
            if pt == 0:
                break
            # Skip users that are not in the server
            if is_in_server(user_id):
                user = client.get_user(int(user_id))
                line = "{}. **{}**\#{} has an all-time record of **{}** activity points.".format(str(
                    counter), user.name, user.discriminator, pt)
                msg += line
                msg += "\n"
                counter += 1
                # Leaderboard max
                if counter > RECORD_MAX:
                    break

        embed = discord.Embed(title="Discord Werewolf Activity LEADERBOARD", color=COLOR_RECORD)
        embed.set_author(name=EMBED_HEADER, icon_url=client.get_guild(int(SERVER_ID)).icon_url)
        embed.set_footer(text=EMBED_FOOTER)

        if not msg:
            msg = "The database may have been reset recently which causes it to be empty, or everyone has " \
                  "0 point. Start being active in the community to raise your activity score!"

        embed.add_field(name="**Top Scores Ever Achieved**", value=msg, inline=False)
        await message.channel.send(embed=embed)

    # ===== Leader board command
    elif handles_command(post, ["lead", "leaderboard", "top", "lb"], False, 0, messenger.id):

        msg = ""
        lb = col_players.find().sort("points", -1)

        counter = 1

        for i in lb:
            i = dict(i)
            user_id = i["userid"]
            pt = i["points"]
            # Users with 0 point should not show up on the leaderboard
            if pt == 0:
                break
            # Skip users that are not in the server
            if is_in_server(user_id):
                user = client.get_user(int(user_id))
                line = "{}. **{}**\#{} has **{}** activity points.".format(str(counter),
                                                                           user.name, user.discriminator, pt)
                msg += line
                msg += "\n"
                counter += 1
                # Leaderboard max
                if counter > LEADERBOARD_MAX:
                    break

        embed = discord.Embed(title="Discord Werewolf Activity LEADERBOARD", color=COLOR_LEADERBOARD)
        embed.set_author(name=EMBED_HEADER, icon_url=client.get_guild(int(SERVER_ID)).icon_url)
        embed.set_footer(text=EMBED_FOOTER)

        if not msg:
            msg = "The database may have been reset recently which causes it to be empty, or everyone has " \
                  "0 point. Start being active in the community to raise your activity score!"

        embed.add_field(name="**Top Active Players**", value=msg, inline=False)
        await message.channel.send(embed=embed)

    # ===== Activity command
    elif handles_command(post, ["act", "activity", "me"], False, 0, messenger.id):
        query = {"userid": str(messenger.id)}
        lookup = col_players.find(query)
        temp = list(lookup)
        print(temp)
        if temp:
            lookup_dict = dict(temp[0])
            points = lookup_dict.get("points")
            highscore = lookup_dict.get("highest")
            if points:
                lb_by_points = enumerate(col_players.find().sort("points", -1), 1)
                for i in lb_by_points:
                    if i[1].get("userid") == str(messenger.id):
                        position = i[0]
                msg2_part1 = "Your current position on the activity leaderboard is **{}**.".format(str(position))
            else:
                msg2_part1 = "You don't currently have a registered activity score."
            if highscore:
                lb_by_record = enumerate(col_players.find().sort("highest", -1), 1)
                for i in lb_by_record:
                    if i[1].get("userid") == str(messenger.id):
                        position = i[0]
                msg2_part2 = "Your current position on the all-time highscore leaderboard is " \
                             "**{}**.".format(str(position))
            else:
                msg2_part2 = "You don't currently have a registered personal record yet."
            msg2 = msg2_part1 + "\n" + msg2_part2
        else:
            points = 0
            highscore = 0
            msg2 = "You don't have a score yet! Start being active in the community to earn activity points!"
        embed = discord.Embed(title="DISCORD WEREWOLF LEADERBOARD BOT", color=COLOR_ACTIVITY)
        embed.set_author(name=EMBED_HEADER, icon_url=client.get_guild(int(SERVER_ID)).icon_url)
        embed.set_footer(text=EMBED_FOOTER)
        embed.set_thumbnail(url=messenger.avatar_url)
        msg1 = "You currently have **{}** activity points.\n" \
               "Your highest score ever achieved is **{}** activity points.".format(str(points),
                                                                                     str(highscore))
        embed.add_field(name="Activity Statistics for **{}**#{}".format(messenger.name, messenger.discriminator),
                        value=msg1, inline=False)
        embed.add_field(name="**{}**#{}'s current position on the "
                             "leaderboards:".format(messenger.name, messenger.discriminator),
                        value=msg2, inline=False)
        await message.channel.send(embed=embed)

    # ===== Check command
    elif handles_command(post, ["check"], 1, 0, messenger.id):
        check = handles_command(post, ["check"], 1, 0, messenger.id)
        if check == 1:
            to_check = get_parameter(message.content)
            checked_person = get_person(to_check)
            if checked_person:
                checked_person_id = checked_person.id
                query = {"userid": str(checked_person_id)}
                lookup = col_players.find(query)
                temp = list(lookup)
                print(temp)
                if temp:
                    lookup_dict = dict(temp[0])
                    points = lookup_dict.get("points")
                    highscore = lookup_dict.get("highest")
                    if points:
                        lb_by_points = enumerate(col_players.find().sort("points", -1), 1)
                        for i in lb_by_points:
                            if i[1].get("userid") == str(checked_person.id):
                                position = i[0]
                        msg2_part1 = "Their current position on the activity leaderboard is **{}**.".format(
                            str(position))
                    else:
                        msg2_part1 = "They don't currently have a registered activity score."
                    if highscore:
                        lb_by_record = enumerate(col_players.find().sort("highest", -1), 1)
                        for i in lb_by_record:
                            if i[1].get("userid") == str(checked_person.id):
                                position = i[0]
                        msg2_part2 = "Their current position on the all-time highscore leaderboard is " \
                                     "**{}**.".format(str(position))
                    else:
                        msg2_part2 = "They don't currently have a registered personal record yet."
                    msg2 = msg2_part1 + "\n" + msg2_part2
                else:
                    points = 0
                    highscore = 0
                    msg2 = "They don't have a score yet! Encourage them to be active in the community " \
                           "to earn activity points!"
                embed = discord.Embed(title="DISCORD WEREWOLF LEADERBOARD BOT", color=COLOR_ACTIVITY)
                embed.set_author(name=EMBED_HEADER, icon_url=client.get_guild(int(SERVER_ID)).icon_url)
                embed.set_footer(text=EMBED_FOOTER)
                embed.set_thumbnail(url=checked_person.avatar_url)
                msg1 = "They currently have **{}** activity points.\n" \
                       "Their highest score ever achieved is **{}** activity points.".format(str(points),
                                                                                             str(highscore))
                embed.add_field(name="Activity Statistics for **{}**#{}".format(checked_person.name,
                                                                                checked_person.discriminator),
                                value=msg1, inline=False)
                embed.add_field(name="**{}**#{}'s current position on the "
                                     "leaderboards:".format(checked_person.name, checked_person.discriminator),
                                value=msg2, inline=False)
                await message.channel.send(embed=embed)
            else:
                await message.channel.send(make_ping(messenger.id) + " :x: User not found, or user not in server.")
        elif check == 2:
            await message.channel.send(make_ping(messenger.id) + " :x: Invalid format: incorrect number of arguments.")

    # ===== Reset command: deletes the activity database
    elif handles_command(post, ["freset_activity"], False, 2, messenger.id):
        check = handles_command(post, ["freset_activity"], False, 2, messenger.id)
        if check == 1:
            col_players.drop()
            await message.channel.send("**Activity database dropped, all stored data deleted. "
                                       "The activity leaderboard has been reset.**")
        elif check == 3:
            await message.channel.send(make_ping(messenger.id) + " :heart_exclamation: "
                                                                 "You do not have the permissions to use this command.")

    # ===== Reset command: deletes the ratings database
    elif handles_command(post, ["freset_ratings"], False, 2, messenger.id):
        check = handles_command(post, ["freset_ratings"], False, 2, messenger.id)
        if check == 1:
            col_ratings.drop()
            await message.channel.send("**Ratings database dropped, all stored data deleted. "
                                       "The database has been reset.**")
        elif check == 3:
            await message.channel.send(make_ping(messenger.id) + " :heart_exclamation: "
                                                                 "You do not have the permissions to use this command.")

    # ===== Joke command
    elif handles_command(post, ["j", "join"], False, 0, messenger.id):
        temp_reply = "**{}** joined the game of ~~One Night Ultimate Werewolf~~ and raised the number of " \
                     "players to **{}**. *I'm sorry I'm just kidding ;-;*"
        reply = temp_reply.format(messenger.name, random.choice(list(range(1, 10))))
        await message.channel.send(reply)

    # ===== Info command
    elif handles_command(post, ["info", "information"], False, 0, messenger.id):
        embed = discord.Embed(title="DISCORD WEREWOLF LEADERBOARD BOT", color=COLOR_NORMAL)
        embed.set_author(name=EMBED_HEADER, icon_url=client.get_guild(int(SERVER_ID)).icon_url)
        embed.set_footer(text=EMBED_FOOTER)
        msg1 = "This bot keeps track of players' activity level on the server. Future expansions evolving " \
               "around game statistics, such as win-rate and player rating, are possible, so stay tuned! " \
               "If you have any suggestions, bug reports, or interesting new ideas, please DM an admin " \
               "or send them to the <#{}> channel.".format(SUGGESTIONS_CHANNEL)
        embed.add_field(name="**What is this bot all about?**", value=msg1, inline=False)
        msg2 = "Activity points are points awarded to users based on their level of activity and presence " \
               "in the Discord Werewolf community, by awarding a certain amount of points per message on the " \
               "server. Short posts won't be awarded points, and spamming will trigger a spam filter that " \
               "automatically deducts points from your overall score. Playing in Werewolf games " \
               "will help you gain points faster! In addition, your score decays over time, so stay active in " \
               "the community to keep up! At the end of each season, possible surprises and rewards await the " \
               "top active members of our community. More information to come, and suggestions are always welcome!"
        embed.add_field(name="**What are activity points?**", value=msg2, inline=False)
        msg3 = "Type `{p}help` for more information, or `{p}list` to see a list of usable commands.".format(p=PREFIX)
        embed.add_field(name="**Getting Started**", value=msg3, inline=False)
        await message.channel.send(embed=embed)

    # ===== Credits command
    elif handles_command(post, ["credit", "cred", "credits"], False, 0, messenger.id):
        embed = discord.Embed(title = "CREDITS", color = COLOR_NORMAL)
        embed.set_author(name=EMBED_HEADER, icon_url=client.get_guild(int(SERVER_ID)).icon_url)
        embed.set_footer(text=EMBED_FOOTER)
        msg1 = "Programming by **Xinverse#4011**. Please privately message them for any bugs or suggestions."
        embed.add_field(name="**Developer**", value=msg1, inline=False)
        msg2 = "Original idea and concept by **Randium#6521**. Special thanks to the " \
               "team of administrators of Discord Werewolf for their valuable input, suggestions and support, " \
               "as well as our small but valuable team of alpha testers who dedicated their time to help " \
               "with debugging and testing."
        embed.add_field(name="**Acknowledgements**", value=msg2, inline=False)
        await message.channel.send(embed=embed)

    # ----- EXIT CONDITIONS FOR MESSAGES UNQUALIFIED FOR POINTS  ------------------------------------------------------
    # Short messages, messages sent in #garbage, and messages in DM
    # -----------------------------------------------------------------------------------------------------------------

    # We don't award points for short messages or messages starting with bot prefix or messages sent in ignored channels
    if len(post) < MIN_CHARACTERS \
            or post.startswith(WHALE_WOLF_PREFIX) \
            or post.startswith(PREFIX) \
            or str(message.channel.id) in IGNORE_CHANNEL :

        query = {"userid": str(messenger.id)}
        lookup = col_players.find(query)
        temp = list(lookup)
        print(temp)

        # A werewolf game is going on
        if werewolf_bot.status == discord.Status.dnd:

            member = client.get_guild(int(SERVER_ID)).get_member(messenger.id)

            # If the messenger has the player role, double the awarded points
            if PLAYER_ROLE_NAME in [role.name for role in member.roles]:

                # ---------- Darkener Houserule in Effect ----------
                if darkener_houserule:
                    if not message.content.startswith(WHALE_WOLF_PREFIX):
                        await darkener(message)

        # If the player already has an entry within the database
        if temp:
            lookup_dict = dict(temp[0])
            old_score = lookup_dict["points"]
            old_messages = lookup_dict["messages"]
            new_messages = old_messages + 1
            old_high = lookup_dict["highest"]
            new_insert = {"userid": str(messenger.id),
                          "points": old_score,
                          "messages": new_messages,
                          "highest": old_high}
            col_players.delete_one(query)
            col_players.insert_one(new_insert)

        # If the player does not have an entry within the database
        else:
            insert = {"userid": str(messenger.id),
                      "points": 0,
                      "messages": 1,
                      "highest": 0}
            col_players.insert_one(insert)

        restrict_spammers(messenger.id)
        return

    # We don't award points for DM messages
    if message.guild is None:
        return

    # ----- BEGIN AWARD POINTS TO MESSENGERS --------------------------------------------------------------------------
    # This is the last thing that happens: all operations above must exit if we don't want to proceed to score increase
    # -----------------------------------------------------------------------------------------------------------------

    # A werewolf game is going on
    if werewolf_bot.status == discord.Status.dnd:

        member = client.get_guild(int(SERVER_ID)).get_member(messenger.id)

        # If the messenger has the player role, double the awarded points
        if PLAYER_ROLE_NAME in [role.name for role in member.roles]:

            points_added = POINTS_PER_MSG * 2
            query = {"userid": str(messenger.id)}
            lookup = col_players.find(query)
            temp = list(lookup)
            print(temp)

            # ---------- Darkener Houserule in Effect ----------
            if darkener_houserule:
                await darkener(message)

            # If the player already has an entry within the database
            if temp:
                lookup_dict = dict(temp[0])
                old_score = lookup_dict["points"]
                new_score = old_score + points_added
                old_messages = lookup_dict["messages"]
                new_messages = old_messages + 1
                old_high = lookup_dict["highest"]
                new_high = max(old_high, new_score)
                col_players.update_one({"userid": str(messenger.id)}, {"$set": {"points": new_score}})
                col_players.update_one({"userid": str(messenger.id)}, {"$set": {"messages": new_messages}})
                col_players.update_one({"userid": str(messenger.id)}, {"$set": {"highest": new_high}})

            # If the player does not have an entry within the database
            else:
                insert = {"userid": str(messenger.id),
                          "points": points_added,
                          "messages": 1,
                          "highest": points_added}
                col_players.insert_one(insert)

        # If the messenger does not have the player role
        else:

            points_added = POINTS_PER_MSG
            query = {"userid": str(messenger.id)}
            lookup = col_players.find(query)
            temp = list(lookup)
            print(temp)

            # If the player already has an entry within the database
            if temp:
                lookup_dict = dict(temp[0])
                old_score = lookup_dict["points"]
                new_score = old_score + points_added
                old_messages = lookup_dict["messages"]
                new_messages = old_messages + 1
                old_high = lookup_dict["highest"]
                new_high = max(old_high, new_score)
                col_players.update_one({"userid": str(messenger.id)}, {"$set": {"points": new_score}})
                col_players.update_one({"userid": str(messenger.id)}, {"$set": {"messages": new_messages}})
                col_players.update_one({"userid": str(messenger.id)}, {"$set": {"highest": new_high}})

            # If the player does not have an entry within the database
            else:
                insert = {"userid": str(messenger.id),
                          "points": points_added,
                          "messages": 1,
                          "highest": points_added}
                col_players.insert_one(insert)

        restrict_spammers(messenger.id)

    # No werewolf game is going on
    else:

        points_added = POINTS_PER_MSG
        query = {"userid": str(messenger.id)}
        lookup = col_players.find(query)
        temp = list(lookup)
        print(temp)

        # If the player already has an entry within the database
        if temp:
            lookup_dict = dict(temp[0])
            old_score = lookup_dict["points"]
            new_score = old_score + points_added
            old_messages = lookup_dict["messages"]
            new_messages = old_messages + 1
            old_high = lookup_dict["highest"]
            new_high = max(old_high, new_score)
            col_players.update_one({"userid": str(messenger.id)}, {"$set": {"points": new_score}})
            col_players.update_one({"userid": str(messenger.id)}, {"$set": {"messages": new_messages}})
            col_players.update_one({"userid": str(messenger.id)}, {"$set": {"highest": new_high}})

        # If the player does not have an entry within the database
        else:
            insert = {"userid": str(messenger.id),
                      "points": points_added,
                      "messages": 1,
                      "highest": points_added}
            col_players.insert_one(insert)

        restrict_spammers(messenger.id)


@client.event
async def on_ready():

    global bootTime

    game = discord.Game('{p}lead | {p}activity | {p}info'.format(p=PREFIX))
    await client.change_presence(status=discord.Status.online, activity=game)

    if bootTime:
        await log(":heavy_check_mark: on_ready triggered again.")

    else:
        bootTime = time.time()
        print("Ready")
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')
        channel = client.get_channel(int(LOGGING_CHANNEL))
        await channel.send(":white_check_mark: **Rebooted. Powered ON**.")


# Thread that lowers activity
def punish_inactives():
    threading.Timer(DOWN_TIME, punish_inactives).start()
    print("SCORE DECAY -- START")
    for entry in col_players.find():
        entry_dict = dict(entry)
        userid = entry_dict["userid"]
        old_activity = entry_dict["points"]
        decayed_activity = int(old_activity * 0.9958826236)
        col_players.update_one({"userid": userid}, {"$set": {"points": decayed_activity}})
        col_players.update_one({"userid": userid}, {"$set": {"messages": 0}})
    print("SCORE DECAY -- DONE; Points updated")


# Thread that punishes short burst spammers
def reset_spam_timer():
    threading.Timer(SPAM_TIMER, reset_spam_timer).start()
    global rate_limit_dict
    rate_limit_dict = {}
    print("Spam Timer - Reset")


# Thread that backups up the database
def backup():
    threading.Timer(BACKUP_TIMER, backup).start()
    col_backup.drop()
    for doc in col_players.find():
        col_backup.insert(doc)
    print("Backing up -- DONE;")


punish_inactives()
reset_spam_timer()
backup()
client.run(TOKEN)