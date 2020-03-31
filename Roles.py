import math

from discord.ext import commands

import bot_util as bt


def setup(bot):
    """Loads the Roles extension into the bot given
    
    Args:
        bot (commands.Bot): The bot to be loaded into
    """
    bt.INFO('Loading Roles.py')
    bot.add_cog(Roles(bot))


def teardown(bot):
    """Unloads the Roles extension from the bot
    
    Args:
        bot (commands.Bot): The bot to be unloaded from
    """
    bt.INFO('Unloading Roles.py')


class Roles(commands.Cog):
    """The Roles extension
    """

    _channels = {}

    def __init__(self, bot):
        """Initialises the Roles extension
        
        Args:
            bot (commands.Bot): The bot initialising the extension
        """
        self._bot = bot
        bt.INFO('Initialised Roles Bot')

    #---------------------------------Channels Attribute---------------------------------

    @property
    def channels(self):
        """Returns the roles channels for each guild
        
        Returns:
            dict: A dictionary of structure guild:channel for each channel that has a roles channel
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

    #------------------------------------General Use-------------------------------------

    async def get_reaction_message(self, ctx):
        """Gets the monitored message in the roles channel
        
        Args:
            ctx: The context of the call
        
        Returns:
            discord.Message: The message that holds the reactions
        """
        history = await ctx.message.channel.history(oldest_first=True).flatten()
        message = history[1]
        return message

    def check_and_get_channel_id(self, ctx):
        """Tests if the channel exists and gets its ID if it does
        
        Args:
            ctx: The context of the call
        
        Returns:
            tuple: tuple containing:
                    bool: if the channel being called from is the correct one
                    str: the id of the channel being called from
        """
        guild = ctx.guild
        message_channel = str(ctx.message.channel.id)
        valid_channel = str(list(self._channels.get(f'{guild.id}').keys())[0])
        return (valid_channel == message_channel), str(valid_channel)

    #------------------------------------------------------------------------------------

    #--------------------------------Getters and Setters---------------------------------

    def get_guild_data(self, gid):
        """Gets the channel attributed to the guild
        
        Args:
            gid (str): The id of the guild to get the channel of
        
        Returns:
            int: The id of the channel attributed to the guild with id gid
            None: If the specified guild does not have a roles channel setup
        """
        if gid in self._channels.keys():
            return self._channels.get(gid)
        return None

    def set_guild_data(self, gid, data):
        """Sets the channel to be attributed to the guild
        
        Args:
            gid (str): The guild being setup
            data (int): The id of the channel being attributed
        """
        self._channels[str(gid)] = data

    #------------------------------------------------------------------------------------

    #------------------------------------Role Command------------------------------------

    @commands.group(name='role', aliases=["roles"], invoke_without_command=True)
    async def do_role(self, ctx, role, emoji, name):
        """Performs the role command
        
        Args:
            ctx: The context of the call
            role (str): The role being added
            emoji (str): The emoji being associated with the role
            name (str): The description of the role
        """
        bt.INFO(f'Adding role {role} with emoji {emoji}')
        await self.add(ctx, role, emoji, name)

    @do_role.command(aliases=["-a", "a"])
    async def add(self, ctx, role, emoji, name):
        """Performs the role add command
        
        Args:
            ctx: The context of the call
            role (str): The role being added
            emoji (str): The emoji being associated with the role
            name (str): The description of the role
        """
        await ctx.message.delete()
        allowed = await self.check_allowed_role(ctx, role)
        result, channel = self.check_and_get_channel_id(ctx)
        if allowed:
            if result:
                if emoji not in self._channels.get(f'{ctx.guild.id}').get(channel):
                    bt.INFO(f'Attempting to add {emoji} to {ctx.guild.id} with role {role} and text {name}')
                    message = await self.get_reaction_message(ctx)
                    content = message.content
                    content += "\n{0} - {1} ({2})".format(emoji, name, role)
                    await message.add_reaction(emoji)
                    await message.edit(content=content)
                    bt.INFO('Successfully added reaction and description')
                    message = await ctx.send(embed=bt.embed_message('Done!', description=f'Added Role {role} with emoji'
                                                                                         f' {emoji} to the reactions '
                                                                                         f'list',
                                                                    colour='green'))
                    await message.delete(delay=4.0)
                    role_str = role[3:-1]
                    self._channels[f'{ctx.guild.id}'][str(channel)][str(emoji)] = [int(role_str), name]
                    bt.INFO('Added data entry')
                else:
                    bt.INFO(f'Not adding {emoji} for {ctx.guild.name} as it already exists')
                    message = await ctx.send(embed=bt.embed_message('Emoji already in use!', description='If you want '
                                                                                                         'to rebind '
                                                                                                         'that emoji, '
                                                                                                         'use !role '
                                                                                                         'remove '
                                                                                                         '<emoji> to '
                                                                                                         'first '
                                                                                                         'remove it',
                                                                    colour='orange'))
                    await message.delete(delay=6.0)
            else:
                valid = bt.get_channel_by_id(ctx.guild, channel)
                message = await ctx.send(embed=bt.embed_message('You can\'t use that here!', description=f'That '
                                                                                                         f'command '
                                                                                                         f'can only '
                                                                                                         f'be '
                                                                                                         f'executed '
                                                                                                         f'in '
                                                                                                         f'{valid}'))
                await message.delete(delay=4)
        else:
            message = await ctx.send(embed=bt.embed_message('Unable to add role', description=f'{role} role is above '
                                                                                              f'my top role. \n I can'
                                                                                              f' only add roles that '
                                                                                              f'are below or equal to '
                                                                                              f'my top rank',
                                                            colour='red'))
            await message.delete(delay=4)

    @do_role.command(aliases=["-r", "r"])
    async def remove(self, ctx, emoji):
        """Performs the role remove command
        
        Args:
            ctx: The context of the call
            emoji (str): The emoji association to be removed
        """
        await ctx.message.delete()
        result, channel = self.check_and_get_channel_id(ctx)
        if result:
            guild_data = self._channels.get(f'{ctx.guild.id}').get(channel)
            if emoji not in guild_data:
                message = await ctx.send(embed=bt.embed_message('Error!', description=f'Unable to remove {emoji} as '
                                                                                      f'it does not exist!'))
                await message.delete(delay=4.0)
            else:
                bt.INFO(f'Removing {emoji} from {ctx.guild.name}\'s reaction roles')
                keys = list(guild_data.keys())
                index = keys.index(str(emoji))
                bt.INFO('Editing roles message')
                message = await self.get_reaction_message(ctx)
                content = message.content
                split_content = content.split('\n')
                split_content.pop(index + 1)
                content = ''
                for line in split_content:
                    content += line + '\n'
                await message.edit(content=content)
                await message.clear_reaction(emoji)
                bt.INFO('Edit complete!')
                del guild_data[str(emoji)]
                bt.INFO('Removed data entry')

    async def check_allowed_role(self, ctx, role):
        """Checks if the role being added is a valid one
        
        Args:
            ctx: The context of the call
            role (str): The role being added
        
        Returns:
            bool: If the role is less than the highest role of the bot
        """
        guild_roles = ctx.guild.roles
        me = ctx.guild.me
        role_str = role[3:-1]
        role_index = math.inf
        for i in range(len(guild_roles)):
            if role_str == str(guild_roles[i].id):
                role_index = i
                break
        highest_role_index = guild_roles.index(me.top_role)
        return highest_role_index >= role_index

    #------------------------------------------------------------------------------------

    #------------------------------------On Reaction-------------------------------------

    async def on_reaction(self, payload):
        """When someone reacts to a message in the guild
        
        Args:
            payload (discord.RawReactionActionEvent): The raw reaction data
        """
        if not payload.member.bot:
            bt.INFO(f'Received reaction {payload.emoji.name} from {payload.member.name}')
            guild = bt.get_guild_by_id(self._bot, payload.guild_id)
            data_channel_id = list(self._channels.get(str(payload.guild_id)).keys())[0]
            data = self._channels.get(str(payload.guild_id))
            data = data.get(str(data_channel_id))
            if str(payload.channel_id) == str(data_channel_id):
                message = await bt.get_message_by_id(bt.get_channel_by_id(guild, payload.channel_id),
                                                     payload.message_id)
                await message.remove_reaction(payload.emoji, payload.member)
                if payload.emoji.name in data:
                    role = bt.get_role_from_guild(guild, data.get(str(payload.emoji.name))[0])
                    await payload.member.add_roles(role)
                    bt.INFO(f'Gave {payload.member.name} {role} role in {guild.name}')
                else:
                    bt.INFO('Ignoring Emoji as not in reaction data')

    #------------------------------------------------------------------------------------