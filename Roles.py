import discord
from discord.ext import commands
from discord.ext import tasks
import asyncio
import bot_util as bt
import math

def setup(bot):
    bt.INFO('Loading Roles.py')
    bot.add_cog(Roles(bot))

def teardown(bot):
    bt.INFO('Unloading Roles.py')

class Roles(commands.Cog):

    _channels = {}

    def __init__(self, bot):
        self._bot = bot
        bt.INFO('Initialised Roles Bot')

    @property
    def channels(self):
        return self._channels
    
    @channels.setter
    def channels(self, data):
        self._channels = data
        #bt.dprint(self._channels)

    def get_guild_data(self, gid):
        if gid in self._channels.keys():
            return self._channels.get(gid)
        return None

    def set_guild_data(self, gid, data):
        self._channels[str(gid)] = data

    def check_and_get_channel_id(self, ctx):
        guild = ctx.guild
        message_channel = str(ctx.message.channel.id)
        valid_channel = str(list(self._channels.get(f'{guild.id}').keys())[0])
        #print(valid_channel)
        #print(message_channel)
        return ((valid_channel == message_channel), str(valid_channel))

    async def check_allowed_role(self, ctx, role):
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

    async def get_reaction_message(self, ctx):
        history = await ctx.message.channel.history(oldest_first=True).flatten()
        message = history[1]
        return message

    async def on_reaction(self, payload):
        if not payload.member.bot:
            bt.INFO(f'Recieved reaction {payload.emoji.name} from {payload.member.name}')
            guild = bt.get_guild_by_id(self._bot, payload.guild_id)
            data_channel_id = list(self._channels.get(str(payload.guild_id)).keys())[0]
            data = self._channels.get(str(payload.guild_id))
            data = data.get(str(data_channel_id))
            #bt.INFO(f'Checking {data_channel_id} against {payload.channel_id}')
            if str(payload.channel_id) == str(data_channel_id):
                message = await bt.get_message_by_id(bt.get_channel_by_id(guild, payload.channel_id), payload.message_id)
                await message.remove_reaction(payload.emoji, payload.member)
                if payload.emoji.name in data:
                    role = bt.get_role_from_guild(guild, data.get(str(payload.emoji.name))[0])
                    await payload.member.add_roles(role)
                    bt.INFO(f'Gave {payload.member.name} {role} role in {guild.name}')
                else:
                    bt.INFO('Ignoring Emoji as not in reaction data')

    @commands.group(name='role', aliases=["roles"], invoke_without_command=True)
    async def do_role(self, ctx, role, emoji, name):
        bt.INFO(f'Adding role {role} with emoji {emoji}')
        await self.add(ctx, role, emoji, name)

    @do_role.command(aliases=["-a", "a"])
    async def add(self, ctx, role, emoji, name):
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
                    bt.INFO('Succesfully added reaction and description')
                    message = await ctx.send(embed=bt.embed_message('Done!', description=f'Added Role {role} with emoji {emoji} to the reactions list', colour='green'))
                    await message.delete(delay=4.0)
                    role_str = role[3:-1]
                    self._channels[f'{ctx.guild.id}'][str(channel)][str(emoji)] = [int(role_str), name]
                    bt.INFO('Added data entry')
                else:
                    bt.INFO(f'Not adding {emoji} for {ctx.guild.name} as it already exists')
                    message = await ctx.send(embed=bt.embed_message('Emoji already in use!', description='If you want to rebind that emoji, use !role remove <emoji> to first remove it', colour='orange'))
                    await message.delete(delay=6.0)
            else:
                valid = bt.get_channel_by_id(ctx.guild, channel)
                message = await ctx.send(embed=bt.embed_message('You can\'t use that here!', description=f'That command can only be executed in {valid}'))
                await message.delete(delay=4)
        else:
            message = await ctx.send(embed=bt.embed_message('Unable to add role', description=f'{role} role is above my top role. \n I can only add roles that are below or equal to my top rank', colour='red'))
            await message.delete(delay=4)

    @do_role.command(aliases=["-r", "r"])
    async def remove(self, ctx, emoji):
        await ctx.message.delete()
        result, channel = self.check_and_get_channel_id(ctx)
        if result:
            guild_data = self._channels.get(f'{ctx.guild.id}').get(channel)
            if emoji not in guild_data:
                message = await ctx.send(embed=bt.embed_message('Error!', description=f'Unable to remove {emoji} as it does not exist!'))
                await message.delete(delay=4.0)
            else:
                bt.INFO(f'Removing {emoji} from {ctx.guild.name}\'s reaction roles')
                keys = list(guild_data.keys())
                index = keys.index(str(emoji))
                bt.INFO('Editing roles message')
                message = await self.get_reaction_message(ctx)
                content = message.content
                split_content = content.split('\n')
                split_content.pop(index+1)
                content = ''
                for line in split_content:
                    content += line + '\n'
                await message.edit(content=content)
                await message.clear_reaction(emoji)
                bt.INFO('Edit complete!')
                del guild_data[str(emoji)]
                bt.INFO('Removed data entry')
            