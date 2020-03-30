import discord
import sys
import traceback
import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
import inspect

class bcolours:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class YoutubeSearch:

    def __init__(self, search_terms: str, max_results=None):
        self.search_terms = search_terms
        self.max_results = max_results
        self.videos = self.search()

    def search(self):
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
        results = []
        for video in soup.select(".yt-uix-tile-link"):
            if video["href"].startswith("/watch?v="):
                video_info = {
                    "title": video["title"],
                    "link": video["href"],
                    "id": video["href"][video["href"].index("=")+1:]
                }
                results.append(video_info)
        return results

    def to_dict(self):
        return self.videos

    def to_json(self):
        return json.dumps({"videos": self.videos})

def embed_message(title, colour=None, description='', footer=''):
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

def dprint(data, parent='data', level=0):
    tabs = '\t' * level
    cprint('{}' + tabs + parent + '{}: ', bcolours.OKBLUE)
    tabs = '\t' * (level+1)
    for key,value in data.items():
        if isinstance(value, dict):
            dprint(value, parent=key, level=level+1)
        elif isinstance(value, list):
            cprint('{}' + tabs + key + '{}: {}{}{}', bcolours.ERROR, bcolours.WARNING, value, bcolours.ENDC)
        elif isinstance(value, int):
            cprint('{}' + tabs + key + '{}: {}{}{}', bcolours.ERROR, bcolours.OKGREEN, value, bcolours.ENDC)
        elif isinstance(value, str):
            cprint('{}' + tabs + key + '{}: {}', bcolours.ERROR, value)

def cprint(text, colour, *args):
    print(text.format(colour, bcolours.ENDC, *args))

def get_caller():
    previous_frame = inspect.currentframe().f_back.f_back
    (filename, line_number, function_name, lines, index) = inspect.getframeinfo(previous_frame)
    filename = filename.split('\\')[-1].split('.')[0].upper()
    return filename

def INFO(string):
    cprint('[{2}][{0}INFO{1}] ' + string, bcolours.OKGREEN, get_caller())

def ERROR(string):
    cprint('[{2}][{0}ERROR{1}] ' + string, bcolours.ERROR, get_caller())

def WARN(string):
    cprint('[{2}][{0}WARN{1}] ' + string, bcolours.WARNING, get_caller())

def SETUP(string):
    cprint('[{2}][{0}SETUP{1}] ' + string, bcolours.OKBLUE, get_caller())

def check_channel_by_name(guild, channel):
    return channel in [x.name for x in guild.channels]

def get_guild_by_id(bot, gid):
    guilds = bot.guilds
    for guild in guilds:
        if guild.id == gid:
            return guild
    ERROR(f'No guild with with id: {gid} exists in my guilds list')
    return None

def get_channel_by_id(guild, cid):
    channels = guild.channels
    for channel in channels:
        if channel.id == cid:
            return channel
    ERROR(f'Unable to find channel: {cid} in guild {guild.name}')
    return None

async def get_message_by_id(channel, mid):
    messages = await channel.history().flatten()
    for message in messages:
        if message.id == mid:
            return message
    ERROR(f'Unable to find message with id: {mid} in channel {channel.name}')
    return None

def get_channel_by_name(guild, name):
    channels = guild.channels
    for channel in channels:
        if channel.name == name:
            return channel
    ERROR(f'No channel with name {name} exists in guild {guild.name}')
    return None

def get_role_from_guild(guild, rid):
    roles = guild.roles
    for role in roles:
        if role.id == rid:
            return role
    ERROR(f'Unable to find role with id {rid} in {guild.name}')
    return None