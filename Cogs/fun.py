import discord
from discord.ext import commands
import random
import asyncio
import time
from Cogs.Utils import truth
from Cogs.Utils import reddit

truths = truth.truth()


class AddTruthButtons(discord.ui.View):

    def __init__(self):
        super().__init__()
        self.edited = False

    @discord.ui.button(label='Edit truth', style=discord.ButtonStyle.blurple)
    async def edit_truth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.edited = True
        await interaction.response.send_modal(AddTruthModal())

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def add_truth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.edited:
            await interaction.response.edit_message(view=self)
        else:
            newtruth = interaction.message.content[interaction.message.content.find('...'):].replace('... ', '')
            truths.storeTruth(newtruth)
            await interaction.response.edit_message(content=f'Truth has been added! Sample of new truth:\n... {newtruth}', view=None)

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def reject_truth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Truth was not added', view=None)


class AddTruthModal(discord.ui.Modal, title='Time to add a new truth!'):
    newtruth = discord.ui.TextInput(label='New truth', default='... is a cool guy')

    async def on_submit(self, interaction: discord.Interaction):
        newtruth = self.newtruth.value[self.newtruth.value.find('...'):].replace('... ', '')
        await interaction.response.edit_message(content=f'Is this the truth you want to add? Sample of new truth:\n... {newtruth}')


class DeleteTruthButtons(discord.ui.View):

    def __init__(self, truth_number):
        super().__init__()
        self.truth_number = truth_number

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def delete_truth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        truths.deleteTruth(self.truth_number)
        await interaction.response.edit_message(content='Truth has been deleted', view=None)

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def keep_truth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message('Truth was not deleted', view=None)


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.vroomcount = 0
        self.numracers = 3
        self.racestarted = 0
        self.tracklength = 19
        self.racers = []

    @commands.hybrid_command(brief='The ultimate command')
    async def thetruth(self, ctx: commands.Context, name: str = 'Chris') -> None:
        await ctx.send(truths.returnTruth(name))

    @commands.hybrid_command(brief='Improve the ultimate command. Suggest a new truth to add')
    async def addtruth(self, ctx: commands.Context) -> None:
        await ctx.send(f'Time to add a new truth!', view=AddTruthButtons())

    @commands.hybrid_command(brief='List all available options for the ultimate command')
    async def listtruths(self, ctx: commands.Context) -> None:
        msg = 'These are the current truths:'
        for i in range(0, len(truths.truths)):
            msg += '\n%d: ...%s' % (i+1, truths.truths[i].replace('%s', ''))

        await ctx.send(msg)

    @commands.hybrid_command(brief='Suggest a truth to delete')
    async def deletetruth(self, ctx: commands.Context, truth_number: int = 0) -> None:
        if truth_number <= 0:
            await ctx.send('Please specify truth number that you want to vote on deleting. Use !listtruths to get list')
            return

        await ctx.send(f'Is this the truth you want to delete? \n{truths.truths[truth_number-1].replace("%s", "")}', view=DeleteTruthButtons(truth_number-1))

    @commands.hybrid_command(brief='Autists! Start your engines!')
    async def vroom(self, ctx: commands.Context, numracers: int = 3, tracklength: int = 19) -> None:

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

    @commands.hybrid_command(brief='Cancel a race before it has started')
    async def cancelvroom(self, ctx: commands.Context) -> None:
        self.vroomcount = 0
        self.racers = []
        self.numracers = 3
        self.racestarted = 0
        self.tracklength = 40
        await ctx.send('Race has been cancelled')

    @commands.hybrid_command(brief='Return hottest reddit post from subreddit')
    async def reddit(self, ctx: commands.Context, sr: str) -> None:
        hot = await reddit.hotPost(sr)
        reddit_post = '**' + hot[2] + '**\n' + hot[0]
        await ctx.send(reddit_post)

    @commands.hybrid_command(brief='Ask the magic 8ball a yes/no question')
    async def ball(self, ctx: commands.Context) -> None:
        answers = [
            ['Ek dink so, ja', 'Heel waarskynlik', 'Sonder twyfel', 'Ja-wat ek skat dis reg', 'Dis die waarheid'],
            ['Nee wat ou seuna', 'Dis nie waar nie', 'Ek vermoed nee', 'Onmoontlik', 'Dalk lank gelede, maar nie meer nie'],
            ['Wat MEEN jy?']]
        yesno = random.randint(0, (len(answers)-1)*5+1) // 5
        answer = random.randint(0, len(answers[yesno])-1)
        await ctx.send(':8ball: **%s** :8ball:' % answers[yesno][answer])

    @commands.hybrid_command(brief='Ask the ruler of the free world an important question. God bless America')
    async def asktrump(self, ctx: commands.Context, *, question: str) -> None:
        responses = ["AMERICA",
                     "MAKE AMERICA GREAT AGAIN",
                     "Grab 'em by the pussy. You can do anything",
                     "CHINA",
                     "I'm much more humble than you would understand.",
                     "I have the best temperament or certainly one of the best temperaments of anybody that’s ever run for the office of president. Ever.",
                     "I’m the most successful person ever to run for the presidency, by far. Nobody’s ever been more successful than me.",
                     "I'm the least racist person you will ever interview.",
                     "Number one, I am the least anti-Semitic person that you’ve ever seen in your entire life. Number two, racism. The least racist person",
                     "I’m the best thing that’s ever happened to the Secret Service.",
                     "I am the world’s greatest person that does not want to let people into the country.",
                     "No one has done more for people with disabilities than me.",
                     "Nobody in the history of this country has ever known so much about infrastructure as Donald Trump.",
                     "There's nobody who understands the horror of nuclear more than me.",
                     "There's nobody bigger or better at the military than I am.",
                     "There's nobody that feels stronger about the intelligence community and the CIA than Donald Trump,",
                     "There’s nobody that’s done so much for equality as I have",
                     "There's nobody that has more respect for women than I do,",
                     "I would build a great wall, and nobody builds walls better than me, believe me",
                     "I am going to save Social Security without any cuts. I know where to get the money from. Nobody else does .",
                     "Nobody respects women more than I do",
                     "And I was so furious at that story, because there's nobody that respects women more than I do,",
                     "Nobody respects women more than Donald Trump",
                     "She can't talk about me because nobody respects women more than Donald Trump,",
                     "Nobody has more respect for women than Donald Trump!",
                     "Nobody has more respect for women than I do.",
                     "Nobody has more respect for women than I do. Nobody.", "Nobody reads the Bible more than me.",
                     "Nobody loves the Bible more than I do",
                     "Nobody does self-deprecating humor better than I do. It’s not even close",
                     "Nobody knows more about taxes than I do, maybe in the history of the world.",
                     "Nobody knows more about trade than me",
                     "Nobody knows the (visa) system better than me. I know the H1B. I know the H2B. Nobody knows it better than me.",
                     "Nobody knows debt better than me.", "I think nobody knows the system better than I do",
                     "I hope all workers demand that their @Teamsters reps endorse Donald J. Trump. Nobody knows jobs like I do! Don’t let them sell you out!",
                     "I know more about renewables than any human being on earth.",
                     "I know more about ISIS than the generals do.", "I know more about contributions than anybody",
                     "I know more about offense and defense than they will ever understand, believe me. Believe me. Than they will ever understand. Than they will ever understand.",
                     "I know more about wedges than any human being that's ever lived",
                     "I know more about drones than anybody,", "I know more about Cory than he knows about himself.",
                     "I know our complex tax laws better than anyone who has ever run for president",
                     "It’s like the wheel, there is nothing better. I know tech better than anyone",
                     "I’m very highly educated. I know words; I have the best words.",
                     "I know some of you may think l'm tough and harsh but actually I'm a very compassionate person (with a very high IQ) with strong common sense",
                     "I watch these pundits on television and, you know, they call them intellectuals. They're not intellectuals, I'm much smarter than them. I think I have a much higher IQ. I think I went to a better college — better everything,",
                     "@ajodom60: @FoxNews and as far as that low-info voter base goes, I have an IQ of 132. So much for that theory. #MakeAmericaGreatAgain",
                     "Sorry losers and haters, but my I.Q. is one of the highest - and you all know it! Please don't feel so stupid or insecure, it's not your fault",
                     "We can’t let these people, these so called egg-heads--and by the way, I guarantee you my IQ is much higher than theirs, alright. Somebody said the other day, ‘Yes, well the intellectuals–‘ I said, ‘What intellectuals? I’m smarter than they are, many of people in this audience are smarter than they are.",
                     "You know, I’m, like, a smart person. I don’t have to be told the same thing in the same words every single day for the next eight years",
                     "I’m speaking with myself, number one, because I have a very good brain and I’ve said a lot of things.",
                     "I think that would qualify as not smart, but genius....and a very stable genius at that!"
                     ]

        pictures = ['https://image.cnbcfm.com/api/v1/image/106479371-1586300131122rts38dfs.jpg',
                    'https://media.vanityfair.com/photos/5c2fdb09ef10e32ca1332862/master/pass/trumpshutdownraises.jpg',
                    'https://www.newmandala.org/wp-content/uploads/cache/2016/04/DonaldTrump/2626785964.jpg',
                    'https://s.abcnews.com/images/Politics/donald-trump-this-week-02-ap-jc-181110_hpMain_16x9_992.jpg',
                    'https://www.kusi.com/content/uploads/2020/06/trump-tries-coronavirus-swab.png',
                    'https://www.askideas.com/media/48/Donald-Trump-Funny-Smiling-Picture.jpg',
                    'https://media.newyorker.com/photos/59096fa52179605b11ad76c5/master/pass/Denby-The-Honest-Face-of-Donald-Trump.jpg',
                    'https://www.insideedition.com/sites/default/files/styles/video_1920x1080/public/brightcove/videos/images/posters/8659_2.jpg',
                    'https://s1.r29static.com/bin/entry/63e/430x516,85/1599557/image.webp',
                    'https://bostonglobe-prod.cdn.arcpublishing.com/resizer/iDnjlRywlGbA543v3F4mdHcsNOc=/1440x0/arc-anglerfish-arc2-prod-bostonglobe.s3.amazonaws.com/public/ORLEUBRZCII6RF3ACFYYET343Q.jpg',
                    'https://images.indianexpress.com/2017/11/trump-water-bottle-main.jpg',
                    'https://www.thestatesman.com/wp-content/uploads/2018/12/potus-QT.jpg',
                    'https://www.thenational.ae/image/policy:1.923144:1571032664/005642-01-05.jpg'
                    ]

        response = random.choice(responses)
        picture = random.choice(pictures)

        trump_msg = discord.Embed(title='Ask Trump', description='%s asks: %s' % (ctx.author.name, question), colour=discord.Colour(16711680))
        trump_msg.set_image(url=picture)
        trump_msg.set_footer(text='Trump: %s' % response)
        await ctx.send(embed=trump_msg)


async def setup(bot):
    await bot.add_cog(Fun(bot))
