import discord
from discord.ext import commands
from Cogs.Utils.OD import tournaments
import os
import pickle
import asyncio
import time
import re
import operator


class Fantasy:

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.match_checker())

        if os.path.isfile('fantasyDB/linked_matches.txt'):
            self.matches = pickle.load(open('fantasyDB/linked_matches.txt', 'rb'))
        else:
            self.matches = []

        if os.path.isfile('fantasyDB/linked_messages.txt'):
            self.messages = pickle.load(open('fantasyDB/linked_messages.txt', 'rb'))
        else:
            self.messages = {}

        if os.path.isfile('fantasyDB/linked_channels.txt'):
            self.channels = pickle.load(open('fantasyDB/linked_channels.txt', 'rb'))
        else:
            self.channels = []

        if os.path.isfile('fantasyDB/start_times.txt'):
            self.start_times = pickle.load(open('fantasyDB/start_times.txt', 'rb'))
        else:
            self.start_times = {}

        if os.path.isfile('fantasyDB/allow_bets.txt'):
            self.allow_bets = pickle.load(open('fantasyDB/allow_bets.txt', 'rb'))
        else:
            self.allow_bets = []

        if os.path.isfile('fantasyDB/total_bets.txt'):
            self.total_bets = pickle.load(open('fantasyDB/total_bets.txt', 'rb'))
        else:
            self.total_bets = {}

        if os.path.isfile('fantasyDB/bets.txt'):
            self.bets = pickle.load(open('fantasyDB/bets.txt', 'rb'))
        else:
            self.bets = {}

        if os.path.isfile('fantasyDB/balances.txt'):
            self.balances = pickle.load(open('fantasyDB/balances.txt', 'rb'))
        else:
            self.balances = {}

        self.live_counter = {}

        # if os.path.isfile('fantasyDB/balances_times.txt'):
        #     self.balances_times = pickle.load(open('fantasyDB/balances_times.txt', 'rb'))
        # else:
        #     self.balances_times = {}

    @commands.command(pass_context=True, brief='Link a channel to display fantasy league messages')
    async def link(self, ctx):
        if ctx.message.channel in self.channels:
            await self.bot.say('This channel has already been linked for fantasy league messages. Use unlink if you wish to remove it')
        else:
            self.channels.append(ctx.message.channel)
            await self.save_to_file(self.channels, 'fantasyDB/linked_channels.txt')
            await self.bot.say('Channel has been linked. It will now receive fantasy league messages and can accept fantasy league commands')

    @commands.command(pass_context=True, brief='Unlink a channel to no longer display fantasy league messages')
    async def unlink(self, ctx):
        if ctx.message.channel in self.channels:
            self.channels.remove(ctx.message.channel)
            await self.save_to_file(self.channels, 'fantasyDB/linked_channels.txt')
            await self.bot.say('Link to channel has been removed. It will no longer receive fantasy league messages')
        else:
            await self.bot.say('This channel was not linked for fantasy league messages. No action was taken')

    async def save_to_file(self, to_save, filename):
        pickle.dump(to_save, open(filename, 'wb'))

    async def match_checker(self):
        while not self.bot.is_closed:
            try:
                live_matches = await tournaments.get_live_games()
            except ValueError:
                live_matches = []
                print('Decoding JSON failed - get_live_games')

            if self.channels:
                for match in live_matches:
                    if match not in self.matches:
                        self.matches.append(match)
                        await self.save_to_file(self.matches, 'fantasyDB/linked_matches.txt')

                        self.start_times[match['match_id']] = time.time()
                        await self.save_to_file(self.start_times, 'fantasyDB/start_times.txt')

                        self.allow_bets.append(match['match_id'])
                        await self.save_to_file(self.allow_bets, 'fantasyDB/allow_bets.txt')

                        self.total_bets[match['match_id']] = [0, 0]
                        await self.save_to_file(self.total_bets, 'fantasyDB/total_bets.txt')

                        self.bets[match['match_id']] = {}
                        await self.save_to_file(self.bets, 'fantasyDB/bets.txt')

                        if self.channels:
                            messages = []
                            for channel in self.channels:
                                message_to_send = '**A new %s Dota 2 match has begun!**' % match['league_name']
                                message_to_send += '\n%s VS %s' % (match['radiant_team'], match['dire_team'])
                                message_to_send += '\nPlace your bets! Use bet command to bet for team 1 or 2'
                                message_to_send += '\nMatch ID = %d. Use this ID to bet on this match' % match['match_id']
                                message_to_send += '\nBetting closes in 10 minutes'
                                new_match_message = await self.bot.send_message(channel, message_to_send)
                                messages.append(new_match_message)
                                self.messages[match['match_id']] = messages
                                await self.save_to_file(self.messages, 'fantasyDB/linked_messages.txt')

                for match in self.matches:
                    new_time = int(time.time() - self.start_times[match['match_id']]) // 60
                    for i in range(0, len(self.messages[match['match_id']])):
                        message = self.messages[match['match_id']][i]
                        if new_time >= 10 and match['match_id'] in self.allow_bets:
                            new_message = str.replace(message.content, re.search('Betting closes in (.+?) minutes', message.content).group(0), 'Betting time is now over')
                            new_message += '\nTotal bets: %d - %d' % (self.total_bets[match['match_id']][0], self.total_bets[match['match_id']][1])

                            if self.total_bets[match['match_id']][0] == 0 or self.total_bets[match['match_id']][1] == 0:
                                new_message += '\n0 total bet detected. Refunding all bets'
                                await self.payout(match, True)
                                await self.payout(match, False)

                                for player in self.bets[match['match_id']]:
                                    self.bets[match['match_id']][player] = [0, 0]

                                await self.save_to_file(self.bets, 'fantasyDB/bets.txt')

                            self.messages[match['match_id']][i] = await self.bot.edit_message(message, new_message)

                            self.allow_bets.remove(match['match_id'])
                            await self.save_to_file(self.allow_bets, 'fantasyDB/allow_bets.txt')

                        elif match['match_id'] in self.allow_bets:
                            self.messages[match['match_id']][i] = await self.bot.edit_message(message, str.replace(message.content, re.search('Betting closes in (.+?) minutes', message.content).group(0), 'Betting closes in %d minutes' % (10 - new_time)))

                    try:
                        match_winner = await tournaments.check_winner(int(match['match_id']))
                    except:
                        match_winner = None
                        print('Decoding JSON failed - check_winner')

                    if match_winner is None:
                        try:
                            check_live = await tournaments.check_if_still_live(int(match['match_id']))
                        except:
                            check_live = None
                            print('Decoding JSON failed - check_if_still_live')

                        if not check_live and check_live is not None:
                            if match['match_id'] in self.live_counter:
                                self.live_counter[match['match_id']] += 1
                            else:
                                self.live_counter[match['match_id']] = 1

                            if self.live_counter[match['match_id']] == 10:
                                for i in range(0, len(self.messages[match['match_id']])):
                                    del self.live_counter[match['match_id']]

                                    for j in range(0, len(self.messages[match['match_id']])):
                                        message = self.messages[match['match_id']][j]
                                        self.messages[match['match_id']][i] = await self.bot.edit_message(message, message.content + '\nUnfinished match detected. Refunding all bets')

                                    await self.payout(match, True)
                                    await self.payout(match, False)

                                    await self.after_match_cleanup(match)

                        elif check_live:
                            self.live_counter[match['match_id']] = 0

                    elif match_winner is not None:

                        if match_winner:
                            winner = match['radiant_team']
                        else:
                            winner = match['dire_team']

                        await self.payout(match, match_winner)

                        for i in range(0, len(self.messages[match['match_id']])):
                            message = self.messages[match['match_id']][i]
                            self.messages[match['match_id']][i] = await self.bot.edit_message(message, message.content + '\nThe match has completed. The winner is %s' % winner)

                        await self.after_match_cleanup(match)

                    await self.save_to_file(self.messages, 'fantasyDB/linked_messages.txt')

            # for player in self.balances_times:
            #     current_time = time.time()
            #     if current_time - self.balances_times[player] >= 3600:
            #         self.balances[player] += 10 * (int(current_time - self.balances_times[player]) // 3600)
            #         await self.save_to_file(self.balances, 'fantasyDB/balances.txt')
            #
            #         self.balances_times[player] = current_time
            #         await self.save_to_file(self.balances_times, 'fantasyDB/balances_times.txt')

            await asyncio.sleep(10)

    @commands.command(pass_context=True, brief='Put your Honeypots on the line. Place a bet on a team!')
    async def bet(self, ctx, team=-1, bet_value=-1, given_match_id=0):
        if not ctx.message.channel.is_private:
            await self.bot.delete_message(ctx.message)
        if team not in (1, 2):
            await self.bot.send_message(ctx.message.author, 'Can only bet for team 1 or team 2')
        elif bet_value < 0:
            await self.bot.send_message(ctx.message.author, 'Please enter correct bet value')
        else:
            if self.messages:
                if given_match_id == 0 and self.allow_bets:
                    match_id = self.allow_bets[len(self.allow_bets)-1]
                else:
                    if given_match_id not in self.allow_bets:
                        await self.bot.send_message(ctx.message.author, 'Bets are closed or invalid match ID provided')
                        return

                    match_id = given_match_id

                for i in range(0, len(self.matches)):
                    if self.matches[i]['match_id'] == match_id:
                        match = self.matches[i]
                        break

                if match['match_id'] in self.allow_bets:
                    if ctx.message.author.id not in self.balances:
                        await self.bot.send_message(ctx.message.author, 'You are not registered to participate in betting. Use join command to register')
                    else:
                        if ctx.message.author.id not in self.bets[match['match_id']]:
                            self.bets[match['match_id']][ctx.message.author.id] = [0, 0]

                        if self.balances[ctx.message.author.id] + sum(self.bets[match['match_id']][ctx.message.author.id]) < bet_value:
                            await self.bot.send_message(ctx.message.author, 'Insufficient funds to place a bet')
                        else:
                            self.balances[ctx.message.author.id] += sum(self.bets[match['match_id']][ctx.message.author.id]) - bet_value
                            await self.save_to_file(self.balances, 'fantasyDB/balances.txt')

                            old_bet = self.bets[match['match_id']][ctx.message.author.id]

                            self.bets[match['match_id']][ctx.message.author.id] = [0, 0]
                            self.bets[match['match_id']][ctx.message.author.id][team-1] = bet_value
                            await self.save_to_file(self.bets, 'fantasyDB/bets.txt')

                            self.total_bets[match['match_id']][0] -= old_bet[0]
                            self.total_bets[match['match_id']][1] -= old_bet[1]

                            self.total_bets[match['match_id']][team-1] += bet_value

                            await self.save_to_file(self.total_bets, 'fantasyDB/total_bets.txt')

                            await self.save_to_file(self.messages, 'fantasyDB/linked_messages.txt')

                            if team == 1:
                                team_message = match['radiant_team']
                            else:
                                team_message = match['dire_team']

                            await self.bot.send_message(ctx.message.author, 'Your bet of %d on %s has been placed' % (bet_value, team_message))

                else:
                    await self.bot.send_message(ctx.message.author, 'Bets are closed')
            else:
                await self.bot.send_message(ctx.message.author, 'There are currently no live matches that are being tracked. Please wait for a match to be tracked')

    @commands.command(pass_context=True, brief='Register for fantasy league and receive 1000 Honeypots to bet')
    async def join(self, ctx):
        if not ctx.message.channel.is_private:
            await self.bot.delete_message(ctx.message)
        if ctx.message.author.id in self.balances:
            await self.bot.send_message(ctx.message.author, 'You are already registered for fantasy league')
        else:
            self.balances[ctx.message.author.id] = 1000
            await self.save_to_file(self.balances, 'fantasyDB/balances.txt')

            # self.balances_times[ctx.message.author.id] = time.time()
            # await self.save_to_file(self.balances_times, 'fantasyDB/balances_times.txt')

            await self.bot.send_message(ctx.message.author, 'You have been registered for fantasy league! You have 1000 Honeypots to spend')

    @commands.command(pass_context=True, brief='Check your Honeypot balance')
    async def balance(self, ctx):
        if not ctx.message.channel.is_private:
            await self.bot.delete_message(ctx.message)
        if ctx.message.author.id in self.balances:
            await self.bot.send_message(ctx.message.author, 'Your Honeypot balance is %d' % self.balances[ctx.message.author.id])
        else:
            await self.bot.send_message(ctx.message.author, 'You are not registered for fantasy league')

    @commands.command(pass_context=True, brief='Display top 10 Honeypot balances')
    async def leaderboard(self, ctx):
        if not ctx.message.channel.is_private:
            await self.bot.delete_message(ctx.message)
        if self.balances:
            leaderboard_message = '**Here are the current leaders of the fantasy league**'
            sorted_balances = sorted(self.balances.items(), key=operator.itemgetter(1), reverse=True)
            for i in range(0, min(len(self.balances), 10)):
                username = discord.utils.get(self.bot.get_all_members(), id=str(sorted_balances[i][0]))
                leaderboard_message += '\n%d: %s - %d' % ((i + 1), username, sorted_balances[i][1])

            await self.bot.send_message(ctx.message.author, leaderboard_message)

    async def payout(self, match, winner):
        if winner:
            win_ratio = 1 + self.total_bets[match['match_id']][1] / max(self.total_bets[match['match_id']][0], 1)
        else:
            win_ratio = 1 + self.total_bets[match['match_id']][0] / max(self.total_bets[match['match_id']][1], 1)

        for player in self.bets[match['match_id']]:
            if winner:
                self.balances[player] += int(round(self.bets[match['match_id']][player][0] * win_ratio, 0))
            else:
                self.balances[player] += int(round(self.bets[match['match_id']][player][1] * win_ratio, 0))

        for player in self.balances:
            if self.balances[player] == 0:
                self.balances[player] = 100
                await self.bot.send_message(discord.utils.get(self.bot.get_all_members(), id=str(self.balances[player])), 'Oh no! It seems you lost all your Honeypots. Do not worry, Bear bot will bail you out. Have 100 Honeypots, on the house!')

        await self.save_to_file(self.balances, 'fantasyDB/balances.txt')

    async def after_match_cleanup(self, match):
        self.matches.remove(match)
        await self.save_to_file(self.matches, 'fantasyDB/linked_matches.txt')

        del self.start_times[match['match_id']]
        await self.save_to_file(self.start_times, 'fantasyDB/start_times.txt')

        del self.total_bets[match['match_id']]
        await self.save_to_file(self.total_bets, 'fantasyDB/total_bets.txt')

        del self.bets[match['match_id']]
        await self.save_to_file(self.bets, 'fantasyDB/bets.txt')

        del self.messages[match['match_id']]


def setup(bot):
    bot.add_cog(Fantasy(bot))
