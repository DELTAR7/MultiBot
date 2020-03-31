import inspect
import json
import urllib.parse

import discord
import requests
from bs4 import BeautifulSoup


class bcolours:
    """The ANSI colour codes
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class YoutubeSearch:
    """The YouTube search query
    
    Attributes:
        max_results (int): The maximum number of results to return
        search_terms (str): The search terms to be used on YouTube
        videos (list): The list of videos obtained
    """

    def __init__(self, search_terms: str, max_results=None):
        """Runs the search on YouTube
        
        Args:
            search_terms (str): The search terms to be used on YouTube
            max_results (None, optional): The maximum number of results to return
        """
        self.search_terms = search_terms
        self.max_results = max_results
        self.videos = self.search()

    def search(self):
        """Performs the actual search 
        
        Returns:
            list: The list of videos found on YouTube from the given query 
        """
        encoded_search = urllib.parse.quote(self.search_terms)
        BASE_URL = "https://youtube.com"
        url = f"{BASE_URL}/results?search_query={encoded_search}"
        INFO(url)
        response = BeautifulSoup(requests.get(url).text, "html.parser")
        results = self.parse_html(response)
        INFO('Got response from YouTube')
        if self.max_results is not None and len(results) > self.max_results:
            return results[:self.max_results]
        return results

    def parse_html(self, soup):
        """Finds the urls of the videos in the html
        
        Args:
            soup: The BeautifulSoup data obtained from the website
        
        Returns:
            list: A list of all the video urls on the page
        """
        results = []
        for video in soup.select(".yt-uix-tile-link"):
            if video["href"].startswith("/watch?v="):
                video_info = {
                    "title": video["title"],
                    "link": video["href"],
                    "id": video["href"][video["href"].index("=") + 1:]
                }
                results.append(video_info)
        return results

    def to_dict(self):
        """Converts the videos list to a dictionary
        
        Returns:
            dict: The videos list as a dictionary
        """
        return self.videos

    def to_json(self):
        """Converts the videos list to a json
        
        Returns:
            json: The json of the videos list
        """
        return json.dumps({"videos": self.videos})


def embed_message(title, colour=None, description='', footer=''):
    """Creates a discord embedded message with some formatting
    
    Args:
        title (str): The title of the embedded message
        colour (hex, optional): The colour of the embed
        description (str, optional): The description of the embed
        footer (str, optional): The footer of the embed
    
    Returns:
        discord.Embed: The embedded message
    """
    if colour == 'error' or colour == 'red':
        colour = 0xe74c3c
    elif colour == 'warn' or colour == 'orange':
        colour = 0xe67e22
    elif colour == 'good' or colour == 'green':
        colour = 0x1f8b4c
    elif colour is None:
        colour = 0xffffff

    colour = discord.Colour(colour)

    embed = None
    if description == '':
        embed = discord.Embed(title=title, colour=colour)
    else:
        embed = discord.Embed(title=title, colour=colour, description=description)

    if footer != '':
        embed.set_footer(text=footer)

    return embed


#---------------------------------------Formatting---------------------------------------

def dprint(data, parent='data', level=0):
    """Prints a dictionary with formatting
    
    Args:
        data (dict): The dictionary to be printed
        parent (str, optional): The key from the parent for nested dictionaries
        level (int, optional): How many nested dictionaries in the recursion is
    """
    tabs = '\t' * level
    cprint('{}' + tabs + parent + '{}: ', bcolours.OKBLUE)
    tabs = '\t' * (level + 1)
    for key, value in data.items():
        if isinstance(value, dict):
            dprint(value, parent=key, level=level + 1)
        elif isinstance(value, list):
            cprint('{}' + tabs + key + '{}: {}{}{}', bcolours.ERROR, bcolours.WARNING, value, bcolours.ENDC)
        elif isinstance(value, int):
            cprint('{}' + tabs + key + '{}: {}{}{}', bcolours.ERROR, bcolours.OKGREEN, value, bcolours.ENDC)
        elif isinstance(value, str):
            cprint('{}' + tabs + key + '{}: {}', bcolours.ERROR, value)


def cprint(text, colour, *args):
    """Prints a message with colour
    
    Args:
        text (str): The text to be coloured
        colour (bcolours.COLOR): The colour of the text
        *args: Any extra strings to be printed
    """
    print(text.format(colour, bcolours.ENDC, *args))

#----------------------------------------------------------------------------------------

#----------------------------------------Logging-----------------------------------------

def get_caller():
    """Gets the name of the file from which the call came from
    
    Returns:
        str: The filename
    """
    previous_frame = inspect.currentframe().f_back.f_back
    (filename, line_number, function_name, lines, index) = inspect.getframeinfo(previous_frame)
    filename = filename.split('\\')[-1].split('.')[0].upper()
    return filename


def INFO(string):
    """Prints an INFO log
    
    Args:
        string (str): The string to be logged
    """
    cprint('[{2}][{0}INFO{1}] ' + string, bcolours.OKGREEN, get_caller())


def ERROR(string):
    """Prints an ERROR log
    
    Args:
        string (str): The string to be logged
    """
    cprint('[{2}][{0}ERROR{1}] ' + string, bcolours.ERROR, get_caller())


def WARN(string):
    """Prints a WARN log
    
    Args:
        string (str): The string to be logged
    """
    cprint('[{2}][{0}WARN{1}] ' + string, bcolours.WARNING, get_caller())


def SETUP(string):
    """Prints a SETUP log
    
    Args:
        string (str): The string to be logged
    """
    cprint('[{2}][{0}SETUP{1}] ' + string, bcolours.OKBLUE, get_caller())

#----------------------------------------------------------------------------------------

#------------------------------------Discord Searches------------------------------------

def check_channel_by_name(guild, channel):
    """Checks if a channel is in a guild using its name
    
    Args:
        guild (discord.Guild): The guild to check in
        channel (str): The name of the channel being checked
    
    Returns:
        bool: If the channel exists in the guild
    """
    return channel in [x.name for x in guild.channels]


def get_guild_by_id(bot, gid):
    """Gets the guild from the bots guilds using its id
    
    Args:
        bot (commands.Bot): The bot to get the guild from
        gid (str): The id of the guild to retrieve
    
    Returns:
        discord.Guild: The guild
    """
    guilds = bot.guilds
    for guild in guilds:
        if guild.id == gid:
            return guild
    ERROR(f'No guild with with id: {gid} exists in my guilds list')
    return None


def get_channel_by_id(guild, cid):
    """Gets the channel from a guild using its id
    
    Args:
        guild (discord.Guild): The guild to search in
        cid (int): The id of the channel to find
    
    Returns:
        discord.abc.GuildChannel: The channel
    """
    channels = guild.channels
    for channel in channels:
        if channel.id == cid:
            return channel
    ERROR(f'Unable to find channel: {cid} in guild {guild.name}')
    return None


async def get_message_by_id(channel, mid):
    """Gets the message from a channel using its id
    
    Args:
        channel (discord.TextChannel): The channel to be searched
        mid (int): The id of the message to be found
    
    Returns:
        discord.Message: The message
    """
    messages = await channel.history().flatten()
    for message in messages:
        if message.id == mid:
            return message
    ERROR(f'Unable to find message with id: {mid} in channel {channel.name}')
    return None


def get_channel_by_name(guild, name):
    """Gets the channel in a guild using its name
    
    Args:
        guild (discord.Guild): The guild to search in
        name (str): The name of the channel to find
    
    Returns:
        discord.abc.GuildChannel: The channel
    """
    channels = guild.channels
    for channel in channels:
        if channel.name == name:
            return channel
    ERROR(f'No channel with name {name} exists in guild {guild.name}')
    return None


def get_role_from_guild(guild, rid):
    """Get the role from a guild using its id
    
    Args:
        guild (discord.Guild): The guild to search in 
        rid (int): The id of the role to find
    
    Returns:
        discord.Role: The role
    """
    roles = guild.roles
    for role in roles:
        if role.id == rid:
            return role
    ERROR(f'Unable to find role with id {rid} in {guild.name}')
    return None

#----------------------------------------------------------------------------------------