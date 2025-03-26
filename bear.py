import discord
from discord.ext import commands
from Cogs.music import stop_lavalink
import os
import pickle
import time
import json
import logging
import wavelink
import platform


class Bear(commands.Bot):

    def __init__(self, *,
                 command_prefix: commands.when_mentioned_or,
                 case_insensitive: bool,
                 intents: discord.Intents,
                 help_command
                 ):
        super().__init__(command_prefix=command_prefix,
                         case_insensitive=case_insensitive,
                         intents=intents,
                         help_command=help_command
                         )

        self.extension_list = ['Cogs.dota',
                               'Cogs.fun',
                               'Cogs.music',
                               'Cogs.giveaway',
                               'Cogs.bloodontheclocktower']

    async def setup_hook(self):
        for ext in self.extension_list:
            await self.load_extension(ext)

    if os.path.isfile('banned_users.txt'):
        banned_users = pickle.load(open('banned_users.txt', 'rb'))
    else:
        banned_users = []


def discord_client():
    with open('bot_info.json', 'r') as file:
        bot_info = json.load(file)

    dev = bot_info['dev']

    if dev:
        bot_prefix_str = '!'
        bot_prefix = commands.when_mentioned_or('!')
    else:
        bot_prefix_str = '?'
        bot_prefix = commands.when_mentioned_or('?')

    intents = discord.Intents.default()

    intents.messages = True
    intents.message_content = True
    intents.members = True
    intents.voice_states = True
    intents.reactions = True
    intents.emojis = True
    intents.dm_messages = True
    intents.guilds = True
    intents.guild_scheduled_events = True

    client = Bear(command_prefix=bot_prefix,
                  case_insensitive=True,
                  intents=intents,
                  help_command=commands.DefaultHelpCommand(dm_help=True)
                  )

    if os.path.isfile('banned_users.txt'):
        banned_users = pickle.load(open('banned_users.txt', 'rb'))
    else:
        banned_users = []

    @client.event
    async def on_ready():
        await client.change_presence(activity=discord.Game('Metal Gear Bearsh'))
        print('Bear bot is online')

    @client.hybrid_command(brief='Test if bot is running')
    @commands.is_owner()
    async def ping(ctx: commands.Context) -> None:
        await ctx.send('Pong!')

    @client.hybrid_command(brief='Reload all extensions')
    @commands.is_owner()
    async def reload(ctx: commands.Context) -> None:
        for ext in client.extension_list:
            try:
                await client.reload_extension(ext)
            except Exception as e:
                await ctx.send(f'Something went wrong when reloading cogs:\n `{e}`')

        await ctx.send('Reloads of cogs complete')

    @client.hybrid_command(brief='Ban user from using commands')
    @commands.has_any_role('Admin', 'Führer')
    async def ban(ctx: commands.Context, ban_user: int) -> None:
        if ban_user in banned_users:
            await ctx.send('User already banned from commands')
        else:
            banned_users.append(ban_user)
            user_info = client.get_user(ban_user)
            pickle.dump(banned_users, open('banned_users.txt', 'wb'))
            await ctx.send('User %s has been banned from using commands' % user_info.name)

    @client.hybrid_command(brief='Unban user from using commands')
    @commands.has_any_role('Admin', 'Führer')
    async def unban(ctx: commands.Context, ban_user: int) -> None:
        if ban_user not in banned_users:
            await ctx.send('User is not banned from commands')
        else:
            banned_users.remove(ban_user)
            user_info = client.get_user(ban_user)
            pickle.dump(banned_users, open('banned_users.txt', 'wb'))
            await ctx.send('User %s has been unbanned from using commands' % user_info.name)

    @client.hybrid_command(brief='Reboot the entire Pi')
    @commands.is_owner()
    async def reboot(ctx: commands.Context) -> None:
        if platform.system() == 'Linux':
            os.system('sudo reboot')

    @client.hybrid_command(brief='Disconnect from voice channels and restart the bot')
    async def restart(ctx: commands.Context) -> None:
        try:
            for vc in client.voice_clients:
                await vc.disconnect(force=True)

        except:
            pass

        try:
            stop_lavalink(client.get_cog('Music').lavalink)
        except NameError:
            pass

        try:
            await wavelink.Pool.close()
        except:
            pass

        await ctx.send('Attempting to restart Bear bot')
        await client.close()

    @client.command(brief='Sync commands')
    async def sync(ctx):
        await ctx.bot.tree.sync()

    @client.event
    async def on_message(message):
        if message.author.id in banned_users:
            await message.channel.send('You have been banned from using commands')
            return

        await client.process_commands(message)

        bot_mention_str = client.user.mention.replace('@', '@!') + ' '
        bot_mention_len = len(bot_mention_str) + 4
        if (message.content[:5] == bot_prefix_str + 'help' or message.content[:bot_mention_len] == bot_mention_str + 'help') and isinstance(message.channel, discord.TextChannel):
            await message.delete()

    token = bot_info['token']

    return client, token


def run_client():
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')
    while True:
        client, token = discord_client()
        try:
            client.run(token, log_handler=handler, log_level=logging.ERROR)
        except Exception as e:
            print('Error: ', e)
        print('Restarting')
        time.sleep(5)


run_client()
