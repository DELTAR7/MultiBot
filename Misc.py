import discord
from discord.ext import commands

import bot_util as bt

category_name = 'multibot-channels'
roles_name = 'multibot-roles'
music_name = 'multibot-music'


def setup(bot):
    """Loads the Misc extensions into the bot
    
    Args:
        bot (commands.Bot): The bot to be added as a cog to
    """
    bt.INFO('Loading Misc.py')
    bot.add_cog(Misc(bot))


def teardown(bot):
    """Summary
    
    Args:
        bot (commands.Bot): The bot that is unloading this extension
    """
    bt.INFO('Unloading Misc.py')


class Misc(commands.Cog):
    """The Misc cog extension
    
    Attributes:
        category_name (str): The default name of the category to create
        music_cog (commands.Cog): The music extension cog 
        roles_cog (commands.Cog): The roles extension cog
    """

    def __init__(self, bot):
        """Initialise the misc extension cog
        
        Args:
            bot (commands.Cog): The bot that is calling the initialisation 
        """
        self._bot = bot
        self._categories = {}
        self.music_cog = self._bot.get_cog('Music')
        self.roles_cog = self._bot.get_cog('Roles')

    def gen_overwrites(self, ctx):
        """Summary
        
        Args:
            ctx: The context of the call
        
        Returns:
            dict: A dictionary of discord Permission overwrites and roles
        """
        overwrites = {
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True, add_reactions=True,
                                                      manage_messages=True, external_emojis=True, attach_files=True,
                                                      embed_links=True),
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        return overwrites

    @property
    def categories(self):
        """Returns the dict of categories
        
        Returns:
            dict: The dictionary of categories that exist per guild
        """
        return self._categories

    @categories.setter
    def categories(self, data):
        """Sets the dictionary of guild:categories for all guilds and categories
        
        Args:
            data (dict): The guild:category dictionary
        """
        self._categories = data
        # bt.dprint(self._categories)

    @commands.command()
    async def echo(self, ctx, *args):
        """Echoes your message, Usage: !echo <sentence>
        
        Args:
            ctx: The context of the call
            *args: The phrase to be echoed back
        """
        output = '>'
        for word in args:
            output += word + ' '
        await ctx.send(content=output)

    @commands.command(name='clear')
    async def clear_command(self, ctx):
        """Clears the current channel of the last 100 messages, Usage: !clear
        
        Args:
            ctx: The context of the call
        """
        bt.INFO(f'Clearing channel {ctx.channel} in {ctx.guild.name} (id: {ctx.guild.id})')
        channel = ctx.message.channel
        counter = await self.clear(channel)
        result = await ctx.send(
            embed=bt.embed_message("Cleared channel", description=f"Deleted {counter} messages from this channel"))
        await result.delete(delay=5)

    async def clear(self, channel):
        """Summary
        
        Args:
            channel (discord.TextChannel): The channel to be cleared
        
        Returns:
            int: The number of messages deleted from the channel
        """
        messages = await channel.history().flatten()
        counter = 0
        for message in messages:
            await message.delete()
            counter += 1
        return counter

    @commands.group(name='setup', invoke_without_command=True)
    async def do_setup(self, ctx):
        """Adds the required channels for the bot to function in, Usage: !setup [optional] <roles|music>
        
        Args:
            ctx: The context of the call
        """
        bt.INFO(f'Performing complete Setup for {ctx.guild.id}')
        await self.setup(ctx)
        await self.roles(ctx)
        await self.music(ctx)

    async def setup(self, ctx):
        """Summary
        
        Args:
            ctx: The context of the call
        """
        if self._categories.get(str(ctx.guild.id)) is None:
            category = await self.find_or_make_category(ctx)
            self._categories[str(ctx.guild.id)] = category.id
        else:
            bt.INFO(f'Category already identified for guild {ctx.guild.id}')

    @do_setup.command()
    async def roles(self, ctx):
        """Performs the setup for just the roles channel, Usage: !setup roles
        
        Args:
            ctx: The context of the call
        """
        bt.INFO(f'Setting up roles for {ctx.guild.id}')
        await self.setup(ctx)
        await self.find_or_make_roles(ctx)

    @do_setup.command()
    async def music(self, ctx):
        """Performs the setup for just the music channel, Usage: !setup music
        
        Args:
            ctx: The context of the call
        """
        bt.INFO(f'Setting up music for {ctx.guild.id}')
        await self.setup(ctx)
        await self.find_or_make_music(ctx)

    async def find_or_make_category(self, ctx):
        """Summary
        
        Args:
            ctx: The context of the call
        
        Returns:
            discord.CategoryChannel: Either the category found or the one created by the bot
        """
        bt.INFO(f'Finding category for {ctx.guild.id}')
        categories = ctx.guild.categories
        found = []
        for category in categories:
            if category.name == category_name or 'bot' in category.name:
                found.append(category)

        category = None

        if len(found) < 1:
            bt.INFO(f'Found no categories in {ctx.guild.name}, making one called {category_name}')
            category = await ctx.guild.create_category_channel(category_name)
        elif len(found) == 1:
            category = found[0]
        else:
            for category in found:
                if category.name == category_name:
                    return category
            category = found[0]

        return category

    async def find_channel(self, ctx, find):
        bt.INFO(f'Finding {find} channel in {ctx.guild.id}')
        channel = bt.get_channel_by_name(ctx.guild, find)
        if channel is None:
            bt.INFO(f'Unable to find {find} channel in {ctx.guild.id}, making one')
            channel = await ctx.guild.create_text_channel(find, category=bt.get_channel_by_id(ctx.guild,
                                                                                              self._categories.get(
                                                                                                  f'{ctx.guild.id}')),
                                                          overwrites=self.gen_overwrites(ctx))
        else:
            await self.clear(channel)

    async def find_or_make_roles(self, ctx):
        """Summary
        
        Args:
            ctx: The context of the call
        
        Returns:
            discord.TextChannel: Either the channel found or the one created by the bot
        """
        channel = await self.find_channel(ctx, roles_name)
        self.roles_cog.set_guild_data(ctx.guild.id, {str(channel.id): {}})
        text = """To add roles for reactions use the !role command in this channel\n
                    Ensure that you have \'Manage Roles\' permission to do this!"""

        embed = bt.embed_message('Welcome', description=text)

        await channel.send(embed=embed)
        await channel.send(content='Roles:\n')
        return channel

    async def find_or_make_music(self, ctx):
        """Summary
        
        Args:
            ctx: The context of the call
        
        Returns:
            discord.TextChannel: Either the channel found or the one created by the bot
        """
        channel = await self.find_channel(ctx, music_name)
        self.music_cog.set_guild_data(str(ctx.guild.id), channel.id)

        preview = bt.embed_message("No song playing currently", colour=0xd462fd, footer='Use the prefix ! for commands')

        text = """**__Queue list:__**
                Join a VoiceChannel and search a song by name or url.
                For playlists append `-a` after the url.
                Supports YouTube"""

        await channel.send(embed=preview)
        await channel.send(content=text)

        return channel
