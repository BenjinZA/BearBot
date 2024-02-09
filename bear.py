import subprocess
import discord
from discord.ext import commands
import asyncio
import os
import pickle
import time
import json
import logging


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
        lavalink = subprocess.Popen(['sudo', 'java', '-jar', 'Lavalink.jar'],
                                    cwd=bot_info['lavalink'],
                                    close_fds=True
                                    )

    intents = discord.Intents.default()

    intents.messages = True
    intents.message_content = True
    intents.members = True
    intents.voice_states = True
    intents.reactions = True
    intents.emojis = True
    intents.dm_messages = True
    intents.guilds = True

    client = commands.Bot(command_prefix=bot_prefix,
                          case_insensitive=True,
                          intents=intents,
                          help_command=commands.DefaultHelpCommand(dm_help=True)
                          )

    @client.event
    async def setup_hook():
        await client.load_extension('Cogs.dota')
        await client.load_extension('Cogs.fun')
        await client.load_extension('Cogs.music')
        await client.load_extension('Cogs.giveaway')

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

    @client.hybrid_command(brief='Disconnect from voice channels and restart the bot')
    async def restart(ctx: commands.Context) -> None:
        try:
            for vc in client.voice_clients:
                await vc.disconnect(force=True)

        except:
            pass

        if not dev:
            lavalink.terminate()

        await ctx.send('Attempting to restart Bear bot')
        await client.close()

    @client.command(brief='Sync commands')
    async def sync(ctx):
        for guild in client.guilds:
            client.tree.copy_global_to(guild=guild)
            await ctx.bot.tree.sync(guild=guild)

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
