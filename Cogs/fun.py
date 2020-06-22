from discord.ext import commands
import random
import asyncio
import time
from Cogs.Utils import truth
from Cogs.Utils import reddit

truths = truth.truth()


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.vroomcount = 0
        self.numracers = 3
        self.racestarted = 0
        self.tracklength = 19
        self.racers = []

    @commands.command(brief='The ultimate command')
    async def thetruth(self, ctx, name='Chris'):
        await ctx.send(truths.returnTruth(name))

    @commands.command(brief='Improve the ultimate command. Suggest a new truth to add')
    async def addtruth(self, ctx, *, newTruth=''):
        voters = []
        vote_count = 0
        timeout = False

        if newTruth == '':
            await ctx.send('Please supply a new truth after the command')
            return

        truth_msg = await ctx.send('%s wants to add a new truth. With enough 👍 votes, the truth will be added to the list.\nSample of new truth:\nMarno %s' % (ctx.author.name, newTruth))

        await truth_msg.add_reaction('👍')

        while timeout == False:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=lambda reaction, user: reaction.emoji == '👍')
            except asyncio.TimeoutError:
                timeout = True
            else:
                if reaction.message.id == truth_msg.id and user != self.bot.user and user not in voters:
                    voters.append(user)
                    vote_count += 1
                if vote_count >= 3:
                    break

        if vote_count >= 3:
            truths.storeTruth(newTruth)
            await ctx.send('Truth has been added!')
        else:
            await ctx.send('Truth not added. Timeout has been reached without enough votes.')

    @commands.command(brief='List all available options for the ultimate command')
    async def listtruths(self, ctx):
        msg = 'These are the current truths:'
        for i in range(0, len(truths.truths)):
            msg += '\n%d: ...%s' % (i+1, truths.truths[i].replace('%s', ''))

        await ctx.send(msg)

    @commands.command(brief='Suggest a truth to delete')
    async def deletetruth(self, ctx, truth_number=0):
        voters = []
        vote_count = 0
        timeout = False

        if truth_number <= 0:
            ctx.send('Please specify truth number that you want to vote on deleting. Use !listtruths to get list')
            return

        truth_msg = await ctx.send('%s wants to delete a truth. With enough 👍 votes, the truth will be deleted from the list.\nThe truth is:\n%s' % (ctx.author.name, truths.truths[truth_number-1] % 'Jan'))

        await truth_msg.add_reaction('👍')

        while timeout == False:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=lambda reaction, user: reaction.emoji == '👍')
            except asyncio.TimeoutError:
                timeout = True
            else:
                if reaction.message.id == truth_msg.id and user != self.bot.user and user not in voters:
                    voters.append(user)
                    vote_count += 1
                if vote_count >= 3:
                    break

        if vote_count >= 3:
            truths.deleteTruth(truth_number-1)
            await ctx.send('Truth has been deleted!')
        else:
            await ctx.send('Truth not deleted. Timeout has been reached without enough votes.')

    @commands.command(brief='Autists! Start your engines!')
    async def vroom(self, ctx, numracers=3, tracklength=19):

        if numracers == 1:
            await ctx.send('Cannot have a race with only 1 autist')
            return

        name = ctx.author.name

        if self.racestarted == 0:
            self.numracers = numracers
            self.tracklength = tracklength
            self.racestarted = 1

        if name in self.racers:
            await ctx.send('%s is already in the race' % name)
            return

        self.vroomcount += 1
        self.racers.append(name)

        if self.vroomcount == 1:
            await ctx.send('%s has initiated an autist race! Use the ?vroom command to enter' % name)
            return

        if self.vroomcount <= self.numracers:
            await ctx.send('%s has entered the autist race!' % name)
            if self.vroomcount != self.numracers:
                return

        winnerselected = 0

        await ctx.send('Cheer on your favourite autist!')
        tracksegment = '﹏'
        start_message = await ctx.send('Autists! Start your engines!')
        track = ':wheelchair:' + tracksegment * self.tracklength + ' --- %s' % self.racers[0]
        for i in range(1, self.numracers):
            track += '\n' + ':wheelchair:' + tracksegment * self.tracklength + ' --- %s' % self.racers[i]

        vroom_message = await ctx.send(track)

        await asyncio.sleep(2)

        await start_message.edit(content='On your marks...')
        await asyncio.sleep(1)
        await start_message.edit(content='Get set...')
        await asyncio.sleep(1)
        await start_message.edit(content='GO!')

        t = [0] * self.numracers
        times = [0] * self.numracers
        finished = [0] * self.numracers

        start_time = time.time()

        while True:
            for i in range(0, self.numracers):
                if t[i] != tracklength:
                    t[i] = min(t[i] + random.randint(1, 3), self.tracklength)

            if self.tracklength in t and winnerselected == 0:
                winnerselected = 1
                tiebreaker = [index for index, value in enumerate(t) if value == self.tracklength]
                if len(tiebreaker) >= 2:
                    winner = random.choice(tiebreaker)
                    tiebreaker.remove(winner)
                    for i in range(0, len(tiebreaker)):
                        t[tiebreaker[i]] += -1
                else:
                    winner = tiebreaker[0]

            track = ''

            for i in range(0, self.numracers):
                if i != 0:
                    track += '\n'

                if t[i] == self.tracklength:
                    if finished[i] == 0:
                        finished[i] = 1
                        times[i] = time.time() - start_time

                    track += tracksegment * t[i] + ':wheelchair:' + tracksegment * (self.tracklength - t[i]) + ' --- %s - %.2f' % (self.racers[i], times[i])
                else:
                    track += tracksegment * t[i] + ':wheelchair:' + tracksegment * (self.tracklength - t[i]) + ' --- %s' % self.racers[i]

            await vroom_message.edit(content=track)
            await asyncio.sleep(1)

            if self.tracklength in t and len(set(t)) <= 1:
                await start_message.edit(content='The winner of the autist race is %s with a time of %.2f seconds!' % (self.racers[winner], times[winner]))
                self.vroomcount = 0
                self.racers = []
                self.numracers = 3
                self.racestarted = 0
                self.tracklength = 40
                break

    @commands.command(brief='Cancel a race before it has started')
    async def cancelvroom(self, ctx):
        self.vroomcount = 0
        self.racers = []
        self.numracers = 3
        self.racestarted = 0
        self.tracklength = 40
        await ctx.send('Race has been cancelled')

    @commands.command(brief='Return hottest reddit post from subreddit')
    async def reddit(self, ctx, sr):
        hot = await reddit.hotPost(sr)
        reddit_post = '**' + hot[2] + '**\n' + hot[0]
        await ctx.send(reddit_post)

    @commands.command(brief='Ask the magic 8ball a yes/no question')
    async def ball(self, ctx):
        answers = [
            ['Ek dink so, ja', 'Heel waarskynlik', 'Sonder twyfel', 'Ja-wat ek skat dis reg', 'Dis die waarheid'],
            ['Nee wat ou seuna', 'Dis nie waar nie', 'Ek vermoed nee', 'Onmoontlik', 'Dalk lank gelede, maar nie meer nie'],
            ['Wat MEEN jy?']]
        yesno = random.randint(0, (len(answers)-1)*5+1) // 5
        answer = random.randint(0, len(answers[yesno])-1)
        await ctx.send(':8ball: **%s** :8ball:' % answers[yesno][answer])


def setup(bot):
    bot.add_cog(Fun(bot))
