import discord
from discord.ext import commands
import asyncio
import os
import pickle
import time


def discord_client():
    dev = True

    if dev:
        bot_prefix = '!'
    else:
        bot_prefix = '?'

    client = commands.Bot(command_prefix=bot_prefix,
                          case_insensitive=True,
                          help_command=commands.DefaultHelpCommand(dm_help=True)
                          )

    client.load_extension('Cogs.dota')
    client.load_extension('Cogs.fun')
    client.load_extension('Cogs.music')
    client.load_extension('Cogs.giveaway')
    # client.load_extension('Cogs.fantasy')

    if os.path.isfile('banned_users.txt'):
        banned_users = pickle.load(open('banned_users.txt', 'rb'))
    else:
        banned_users = []

    @client.event
    async def on_ready():
        await client.change_presence(activity=discord.Game('Metal Gear Bearsh'))
        print('Bear bot is online')

    @client.event
    async def on_member_join(member):
        await member.send('Hi %s, Welcome to the %s server! I am Bear bot, resident bot of this server. Use ?help for a list of my commands. You can use this through PM or in any channel!\nFor any feature requests or bug reports, please PM Benjin' % (member, member.guild.name))

    @client.command(brief='Test if bot is running')
    async def ping(ctx):
        await ctx.send('Pong!')

    @client.command(brief='Ban user from using commands')
    @commands.has_any_role('Admin', 'Führer')
    async def ban(ctx, ban_user: int):
        if ban_user in banned_users:
            await ctx.send('User already banned from commands')
        else:
            banned_users.append(ban_user)
            user_info = client.get_user(ban_user)
            pickle.dump(banned_users, open('banned_users.txt', 'wb'))
            await ctx.send('User %s has been banned from using commands' % user_info.name)

    @client.command(brief='Unban user from using commands')
    @commands.has_any_role('Admin', 'Führer')
    async def unban(ctx, ban_user):
        if ban_user not in banned_users:
            await ctx.send('User is not banned from commands')
        else:
            banned_users.remove(ban_user)
            user_info = client.get_user(ban_user)
            pickle.dump(banned_users, open('banned_users.txt', 'wb'))
            await ctx.send('User %s has been unbanned from using commands' % user_info.name)

    @client.command(brief='Disconnect from voice channels and restart the bot')
    async def restart(ctx):
        await ctx.send('Attempting to restart Bear bot')
        try:
            for vc in client.voice_clients:
                await vc.disconnect()

        except:
            pass

        await client.logout()

    @client.event
    async def on_message(message):
        if message.author.id in banned_users and message.author.id != 123:
            await message.channel.send('You have been banned from using commands')
            return

        await client.process_commands(message)
        if message.content[:5] == bot_prefix + 'help' and isinstance(message.channel, discord.TextChannel):
            await message.delete()

    if dev:
        token = 'dev_token'
    else:
        token = 'live_token'

    return client, token


def run_client():
    while True:
        loop = asyncio.get_event_loop()
        client, token = discord_client()
        try:
            loop.run_until_complete(client.start(token))
        except Exception as e:
            print('Error: ', e)
        print('Restarting')
        time.sleep(5)


run_client()
