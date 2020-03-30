import signal
from discord.ext import commands
import bot_util as bt
from Secure import load, load_data, save_data


class BotClient(commands.Bot):
    """The instance of the bot
    """

    _channels = ['multibot-roles', 'multibot-music']

    async def on_ready(self):
        """Runs when the bot has successfully logged in
        """
        bt.SETUP('Logging In')
        bt.SETUP(f'\t name: {self.user.name}')
        bt.SETUP(f'\t id: {self.user.id}')
        bt.SETUP(f'\t guilds: {len(self.guilds)}')
        self.load_data()
        print('--------------------------------')

    async def on_raw_reaction_add(self, payload):
        """When a user reacts to a message in a guild that the bot is active in
        
        Args:
            payload (discord.RawReactionActionEvent): The reaction event of the react
        """
        cog = self.get_cog('Roles')
        await cog.on_reaction(payload)

    @property
    def channels(self):
        """The list of channels that the bot creates when it needs to
        
        Returns:
            list: The list of channels
        """
        return self._channels

    def load_data(self):
        """Loads the data from the file and gives each cog its respective data struture
        """
        data = load_data('data')

        if data is None:
            return

        react = {}
        music = {}
        category = {}

        for key in data.keys():
            music[key] = data[key]["music"]
            category[key] = data[key]["category"]
            react[key] = data[key]["react"]

        self.get_cog('Music').channels = music
        self.get_cog('Roles').channels = react
        self.get_cog('Misc').categories = category

    def gather_data(self):
        """Gets the data for each of the extensions part of the bot
        """
        bt.INFO('Getting data')
        keys = [str(x.id) for x in self.guilds]
        roles = self.get_cog('Roles').channels
        category = self.get_cog('Misc').categories
        music = self.get_cog('Music').channels

        data = {}

        for key in keys:
            data[key] = {}

        for key in keys:
            data[key]["react"] = roles[key]
            data[key]["music"] = music[key]
            data[key]["category"] = category[key]

        save_data(data)


bot = BotClient(command_prefix=commands.when_mentioned_or("!"), description="A multi-purpose bot")

list_extensions = ['Roles', 'Music', 'Misc']


@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx):
    """Reloads the bots commands, Usage !reload
    
    Args:
        ctx: The context of the call
    """
    bt.WARN('Reloading Extensions!')
    reload_extensions()
    bot.load_data()
    message = await ctx.send(embed=bt.embed_message('Done Reloading!', colour='green'))
    await message.delete(delay=3.0)
    bt.INFO('Done Reloading Extensions!')


def extensions(method):
    """A generic method for loading or unloading bot extensions
    
    Args:
        method: The method to be performed on the extension
    """
    for extension in list_extensions:
        method(extension)


def load_extensions():
    """Loads the bots extensions
    """
    extensions(bot.load_extension)


def reload_extensions():
    """Reloads the bots extensions
    """
    extensions(bot.reload_extension)


def keyboardInterruptHandler(signal, frame):
    """Handles when the program is shutdown with a keyboard interrupt
    
    Args:
        signal: The signal interrupt that is recieved
        frame: The current execution frame
    """
    bt.INFO('Doing cleanup')
    bot.gather_data()
    bt.INFO('Cleanup done!')
    exit(0)


token = load()
load_extensions()
signal.signal(signal.SIGINT, keyboardInterruptHandler)
# bot.run('NjgzMzYxMTg1OTc3OTkxMzAw.Xlqbyg.RAl2fKwwQfFV1eRageY1cOe8h2M')
bot.run(token)
