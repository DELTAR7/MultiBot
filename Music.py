import asyncio
import datetime
import os
import re
import sys

import discord
import youtube_dl
from discord.ext import commands

import bot_util as bt
from bot_util import YoutubeSearch


def setup(bot):
    """Loads the Music extension into bot
    
    Args:
        bot commands.Bot: The bot to be loaded into
    """
    bt.INFO('Loading Music.py')
    bot.add_cog(Music(bot))


def teardown(bot):
    """Unloads the Music extension
    
    Args:
        bot commands.Bot: The bot unloading the Music extension
    """
    bt.INFO('Unloading Music.py')


default_text = """**__Queue list:__**
            Join a VoiceChannel and search a song by name or url.
            For playlists append `-a` after the url.
            Supports YouTube"""

default_preview = bt.embed_message("No song playing currently", colour=0xd462fd, footer='Use the prefix ! for commands')


class Music(commands.Cog):
    """The Music cog extension
    
    Attributes:
        players (dict): The dictionary of players and their current queue of songs 
    """

    players = {}  # dict with structure as : player: [songs]

    _channels = {}

    def __init__(self, bot):
        """Initialises the Music extension
        
        Args:
            bot (commands.Bot): The bot initialising the Music extension
        """
        self._bot = bot
        bt.INFO('Initialised Music Cog')

    #---------------------------------Channels Attribute---------------------------------

    @property
    def channels(self):
        """Returns the music channels for each guild
        
        Returns:
            dict: A dictionary of structure guild:channel for each channel that has a music channel
        """
        return self._channels

    @channels.setter
    def channels(self, data):
        """Sets the data of the channels dictionary
        
        Args:
            data (dict): The dictionary to set the channels data to
        """
        self._channels = data

    #------------------------------------------------------------------------------------

    #--------------------------------Getters and Setters---------------------------------

    def get_guild_data(self, gid):
        """Gets the channel attributed to the guild
        
        Args:
            gid (str): A string of the guild's id
        
        Returns:
            None: If the guild has no music channel setup
            int: The id of the music channel in the guild of id gid
        """
        if gid in self._channels.keys():
            return self._channels.get(gid)
        return None

    def set_guild_data(self, gid, data):
        """Sets the channel attributed to the guild
        
        Args:
            gid (str): A string of the guild's id
            data (int): The id of the channel being linked with the guild
        """
        self._channels[str(gid)] = data

    #------------------------------------General Use-------------------------------------

    def get_voice_client(self, channel):
        """Summary
        
        Args:
            channel (discord.VoiceChannel): The channel that the bot is in
        
        Returns:
            None: If there is no voice client in the specified channel
            discord.Client.voice_client: The voice client in the specified channel
        """
        clients = self.players.keys()
        for client in clients:
            if client.channel == channel:
                return client
        return None

    def get_channel(self, ctx):
        """Gets the voice channel of the user that messaged
        
        Args:
            ctx: The context of the call
        
        Returns:
            discord.VoiceChannel: The voice channel of the user
            None: If the user is not in a channel
        """
        member = ctx.message.author
        voice_channel = member.voice.channel
        return voice_channel

    #------------------------------------------------------------------------------------

    #------------------------------------Join Command------------------------------------

    @commands.command(name='join')
    async def join(self, ctx):
        """Gets the bot to join the current channel the user is in
        
        Args:
            ctx: The context of the call
        """
        await self.do_join(ctx)

    async def do_join(self, ctx):
        """Performs the join of the bot to a channel
        
        Args:
            ctx: The context of the call
        
        Returns:
            discord.Client.voice_client: The voice client instance of the bot in the channel
        """
        try:
            voice_client = await self.get_channel(ctx).connect()
            if voice_client not in self.players:
                self.players[voice_client] = []
            else:
                bt.WARN(f'{voice_client} is already in the players list!')
                message = await ctx.send(embed=bt.embed_message('Already in the channel!', colour='orange'))
                await message.delete(delay=5.0)

            return voice_client
        except BaseException as e:
            ex_type, ex_value, ex_traceback = sys.exc_info()
            bt.ERROR(f'Unable to join channel due to the following error: {ex_value}')

    #------------------------------------------------------------------------------------

    #------------------------------------Play Command------------------------------------

    @commands.command(name='play', aliases=['queue', 'q'])
    async def play_command(self, ctx, *args):
        """Adds the song to the queue, if the queue is empty it will play it. Usage: !play <url|song name>
        
        Args:
            ctx: The context of the call
            *args: The name of the song to search for or the url of the song
        """

        await ctx.message.delete()

        if self._channels.get(str(ctx.guild.id)) is not None:
            if ctx.channel.id == self._channels.get(str(ctx.guild.id)):

                channel = self.get_channel(ctx)
                client = self.get_voice_client(channel)

                if client is None:
                    client = await self.do_join(ctx)

                song = ""

                for arg in args:
                    song += " " + arg

                song = song.strip()

                if client is not None:
                    if not self.find_url(song):
                        data = await self.find_song(song)
                        song = 'https://youtube.com' + data.get('link')
                    if len(self.players[client]) == 0:
                        file_data = self.get_song(song)
                        if file_data is not None:
                            self.players[client].append(file_data)
                            bt.INFO(f'Playing song: {file_data["title"]}')
                            await self.play_song(client, file_data)
                    else:
                        file_data = self.get_song(song)
                        if file_data is not None:
                            self.players[client].append(file_data)
                            await self.edit_song_message(client)
            else:
                music_channel = bt.get_channel_by_id(ctx.guild, self._channels.get(str(ctx.guild.id)))
                await ctx.send(embed=bt.embed_message("Error!",
                                                      description=f"That command is only available "
                                                                  f"in the {music_channel} channel",
                                                      colour='red'))
        else:
            await ctx.send(embed=bt.embed_message(f'Setup is not complete!',
                                                  description="Run !setup for full setup or "
                                                              "'!setup music' for just music",
                                                  colour='red'))

    async def play_song(self, client, file_data):
        """Plays the song in file_data for the voice client client
        
        Args:
            client (discord.Client.voice_client): The voice client instance to play music to
            file_data (dict): A dictionary of the file data about the song 
        """
        client.play(discord.FFmpegPCMAudio(file_data['file']))
        client.volume = 100
        bt.INFO(f'{client} Playing status: {client.is_playing()}')
        await self.edit_preview(client)
        await self.edit_song_message(client)
        asyncio.create_task(self.play_next(client, file_data['duration']))

    def find_url(self, string):
        """Determines if the string parsed through is a url
        
        Args:
            string (str): The string to be checked
        
        Returns:
            bool: True if the string is a url, False if not
        """
        url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+] |[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)
        if len(url) != 0:
            bt.INFO('Song was a url')
            return True
        else:
            bt.INFO('Song was not a url')
            return False

    def get_song(self, url, retries=0):
        """Prunes the song's data that was retrieved
        
        Args:
            url (str): The url of the song to be downloaded
            retries (int, optional): The number of retries performed if the fetch has failed
        
        Returns:
            dict: The file data of the song
        """
        try:
            info = self.download_song(url)
            file_data = {'file': 'songs/' + info['title'] + '-' + info['id'] + '.mp3', 'title': info['title'],
                         'artist': info['artist'], 'duration': info['duration'], 'track': info['track'],
                         'id': info['id'], 'link': url}
            bt.INFO(f'Title: {file_data["title"]}')
            bt.INFO(f'Artist: {file_data["artist"]}')
            bt.INFO(f'Track: {file_data["track"]}')
            bt.INFO(f'Duration: {file_data["duration"]}')
            bt.INFO(f'File: {file_data["file"]}')
            bt.INFO(f'ID: {file_data["id"]}')
            return file_data
        except Exception as e:
            bt.ERROR(f'Unable to find the requested song: {url}')
            if retries < 3:
                return self.get_song(url, retries=retries + 1)
            else:
                return None

    def download_song(self, url):
        """Downloads the song and its information from url
        
        Args:
            url (str): The url of the song to be downloaded
        
        Returns:
            dict: The song data 
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'songs\\%(title)s-%(id)s.mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            file = 'songs\\' + info['title'] + '-' + info['id'] + '.mp3'
            if not os.path.isfile(file):
                ydl.download([url])
        return info

    async def find_song(self, query, retries=0):
        """Queries youtube for using a search term
        
        Args:
            query (str): The search terms used to search youtube
            retries (int, optional): The number of retries if the search fails
        
        Returns:
            str: The url of the found son
        """
        results = YoutubeSearch(query, max_results=10).to_dict()
        useful = []
        for result in results:
            if 'lyric' in result.get('title').lower() or 'audio' in result.get('title').lower():
                useful.append(result)

        if len(useful) == 1:
            return useful[0]
        elif len(useful) > 1:
            # TODO: Figure out a good way to choose between results
            return useful[0]
        elif retries < 5:
            await asyncio.sleep(1)
            return await self.find_song(query, retries=retries + 1)

    #------------------------------------------------------------------------------------

    #-----------------------------------Queue Updates------------------------------------

    async def play_next(self, player, timer):
        """Summary
        
        Args:
            player (discord.Client.voice_client): The voice client to get the queue of
            timer (str): The time in seconds to wait for
        """
        try:
            time = int(timer)
            await asyncio.sleep(time + 3)
            bt.INFO(f'Sleeping for {timer} seconds for player {player}')
            if len(self.players[player]) == 1:
                bt.INFO(f'No more songs to play for {player}')
                self.players[player] = []
                await self.edit_song_message(player)
                asyncio.create_task(self.empty(player, datetime.datetime.now()))
            elif len(self.players[player]) > 1:
                self.players[player].pop(0)
                next_song = self.players[player][0]
                bt.INFO(f'Playing next song in queue for {player} : {next_song["title"]}')
                await self.play_song(player, next_song)
        except BaseException as e:
            ex_type, ex_value, ex_traceback = sys.exc_info()
            bt.ERROR(f'Unable to play the next song due to an error: {ex_value}')

    async def empty(self, player, time):
        """Loops when a voice client's queue is empty for 50 seconds and then leaves if still empty
        
        Args:
            player (discord.Client.voice_client): The voice client that is being polled for being empty
            time (datetime): The time at which the queue first became empty
        """
        if len(self.players[player]) == 0:
            now_time = datetime.datetime.now()
            diff = now_time - time
            if diff.seconds >= 50:
                try:
                    bt.INFO(f'Leaving {player.channel} as no songs have been added')
                    await self.edit_preview(player, default=True)
                    del self.players[player]
                    await player.disconnect()
                except Exception:
                    bt.ERROR(f'Unable to delete {player} from my players')
            else:
                await asyncio.sleep(10)
                await self.empty(player, time)

    async def edit_song_message(self, client):
        """Edits the message in the music channel to represent the queue
        
        Args:
            client (discord.Client.voice_client): The client to retrieve the queue from
        """
        guild = client.guild
        channel_id = self._channels.get(str(guild.id))
        channel = bt.get_channel_by_id(guild, channel_id)
        last_message = await channel.history().flatten()
        last_message = last_message[0]
        contents = default_text
        for song in self.players.get(client):
            contents += self.get_song_title(song)
        await last_message.edit(content=contents)

    async def edit_preview(self, client, default=False):
        """Changes the preview message in the song channel to the currently playing song
        
        Args:
            client (discord.Client.voice_client): The client to retrieve the queue from
            default (bool, optional): A flag to determine if the queue is empty or not
        """
        guild = client.guild
        channel_id = self._channels.get(str(guild.id))
        channel = bt.get_channel_by_id(guild, channel_id)
        last_message = await channel.history().flatten()
        last_message = last_message[1]
        if not default:
            top_song = self.players.get(client)[0]
            title = self.get_song_title(top_song)
            preview = discord.Embed(title=title, colour=discord.Colour(0xd462fd), url=top_song.get('link'),
                                    video=top_song.get('link'))
            preview.set_image(url="http://img.youtube.com/vi/%s/0.jpg" % top_song.get('id'))
            preview.set_footer(text='Use the prefix ! for commands')
        else:
            preview = default_preview
        await last_message.edit(embed=preview)

    def get_song_title(self, song):
        """Makes the header of the preview embed and the queue name
        
        Args:
            song (dict): The songs file data
        
        Returns:
            str: The name displayed in the queue and the preview embed
        """
        mins = int(song["duration"]) // 60
        seconds = int(song["duration"]) % 60
        if song["track"] is None or song["artist"] is None:
            title = song["title"]
            title = re.sub('((\()?([Ll])yric(s)? (\))?)|((\()?([Aa])udio)(\))?', '', title)
            contents = f'\n{title} ({mins}:{seconds})'
        else:
            contents = f'\n{song["track"]} - {song["artist"]} ({mins}:{seconds})'
        return contents

    #------------------------------------------------------------------------------------

    #-------------------------------Playback Manipulation--------------------------------

    @commands.command()
    async def stop(self, ctx):
        """Stops playback and clears the queue
        
        Args:
            ctx: The context of the call
        """
        await ctx.message.delete()
        channel = self.get_channel(ctx)
        client = self.get_voice_client(channel)
        bt.INFO(f'Stopped playback for {client}')

        if client is not None:
            client.stop()
            self.players[client] = []

    @commands.command(name='pause', aliases=['p'])
    async def pause(self, ctx):
        """Pauses the current song
        
        Args:
            ctx: The context of the call
        """
        await ctx.message.delete()
        channel = self.get_channel(ctx)
        client = self.get_voice_client(channel)
        bt.INFO(f'Paused playback for {client}')

        if client is not None:
            client.pause()
            await self.edit_preview(client, default=True)

    @commands.command(name='resume', aliases=['r'])
    async def resume(self, ctx):
        """Resumes the current playback
        
        Args:
            ctx: The context of the call
        """
        await ctx.message.delete()
        channel = self.get_channel(ctx)
        client = self.get_voice_client(channel)
        bt.INFO(f'Resumed playback for {client}')

        if client is not None:
            if client.is_paused():
                client.resume()
                await self.edit_preview(client)

    @commands.command()
    async def leave(self, ctx):
        """Removes the bot from the channel
        
        Args:
            ctx: The context of the call
        """
        await ctx.message.delete()
        channel = self.get_channel(ctx)
        client = self.get_voice_client(channel)

        if client is not None:
            bt.INFO(f'Leaving {channel}')
            await client.disconnect()
            await self.edit_preview(client, default=True)
            try:
                del self.players[client]
            except BaseException as e:
                ex_type, ex_value, ex_traceback = sys.exc_info()
                bt.ERROR(f'Tried to remove {client} from list but it did not exist')
                bt.ERROR(f'Encountered the following error: {ex_value}')

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song and plays the next one
        
        Args:
            ctx: The context of the call
        """
        await ctx.message.delete()
        channel = self.get_channel(ctx)
        client = self.get_voice_client(channel)

        if client is not None:
            bt.INFO(f'Skipping song for client {client}')
            client.pause()
            asyncio.create_task(self.play_next(client, -3))

    #------------------------------------------------------------------------------------