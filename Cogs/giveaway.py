from discord.ext import commands
import os
import pickle
import asyncio
import random


class Giveaway(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        if os.path.isfile('giveaway/entered_users.txt'):
            self.entered_users = pickle.load(open('giveaway/entered_users.txt', 'rb'))
        else:
            self.entered_users = []

        if os.path.isfile('giveaway/live.txt'):
            self.live = pickle.load(open('giveaway/live.txt', 'rb'))
        else:
            self.live = False

        if os.path.isfile('giveaway/details.txt'):
            self.details = pickle.load(open('giveaway/details.txt', 'rb'))
        else:
            self.details = None

        if os.path.isfile('giveaway/msg_id.txt'):
            self.msg_id = pickle.load(open('giveaway/msg_id.txt', 'rb'))
        else:
            self.msg_id = None

        if os.path.isfile('giveaway/channel_id.txt'):
            self.channel_id = pickle.load(open('giveaway/channel_id.txt', 'rb'))
        else:
            self.channel_id = None

    @commands.hybrid_command(brief='Start a giveaway')
    @commands.has_any_role('Admin', 'Führer')
    async def startgiveaway(self, ctx: commands.Context, *, details: str) -> None:
        if self.live:
            await ctx.send('A giveaway is already in progress')
        elif details is None:
            await ctx.send('You must specify something to give away')
        else:
            self.live = True
            pickle.dump(self.live, open('giveaway/live.txt', 'wb'))

            self.entered_users = []
            pickle.dump(self.entered_users, open('giveaway/entered_users.txt', 'wb'))

            self.details = details
            pickle.dump(self.details, open('giveaway/details.txt', 'wb'))

            giveaway_message = 'A new giveaway has started! %s will be giving away %s' % (ctx.author.name, details)
            giveaway_message += '\nTo enter, use command giveaway or react to this message'
            giveaway_msg = await ctx.send(giveaway_message)
            await giveaway_msg.pin()

            for emoji in giveaway_msg.guild.emojis:
                if emoji.name in ['HighwayRoar', 'OMEGARYHARD', 'Spoon4Head', 'MustBeRayno']:
                    await giveaway_msg.add_reaction(emoji)

            self.msg_id = giveaway_msg.id
            pickle.dump(self.msg_id, open('giveaway/msg_id.txt', 'wb'))

            self.channel_id = ctx.channel.id
            pickle.dump(self.channel_id, open('giveaway/channel_id.txt', 'wb'))

    @commands.hybrid_command(brief='End a giveaway')
    @commands.has_any_role('Admin', 'Führer')
    async def endgiveaway(self, ctx: commands.Context) -> None:
        if not self.live:
            await ctx.send('No giveaway is currently live')
        else:
            self.live = False
            pickle.dump(self.live, open('giveaway/live.txt', 'wb'))

            await ctx.send('Giveaway has ended. Use the giveawaywinner command to select a winner')

    @commands.hybrid_command(brief='Select the giveaway winner')
    @commands.has_any_role('Admin', 'Führer')
    async def giveawaywinner(self, ctx: commands.Context) -> None:
        if self.live:
            await ctx.send('Giveaway is still live. Use endgiveaway before trying to select a winner')
        elif len(self.entered_users) == 0:
            await ctx.send('No users currently in the giveaway')
        else:
            winner = self.bot.get_user(self.entered_users[random.randint(0, len(self.entered_users)-1)])

            winner_msg = await ctx.send('The winner of %s will be selected in 3...' % self.details)
            await asyncio.sleep(1)
            await winner_msg.edit(content='The winner of %s will be selected in 2...' % self.details)
            await asyncio.sleep(1)
            await winner_msg.edit(content='The winner of %s will be selected in 1...' % self.details)
            await asyncio.sleep(1)
            await winner_msg.edit(content='The winner of %s is %s' % (self.details, winner.mention))

            self.entered_users.remove(winner)
            pickle.dump(self.entered_users, open('giveaway/entered_users.txt', 'wb'))

    @commands.hybrid_command(brief='Enter a giveaway')
    async def giveaway(self, ctx: commands.Context) -> None:
        if not self.live:
            await ctx.send('No giveaway is currently live')
        elif ctx.author.id in self.entered_users:
            await ctx.send('You are already entered in the giveaway')
        else:
            self.entered_users.append(ctx.author.id)
            pickle.dump(self.entered_users, open('giveaway/entered_users.txt', 'wb'))
            await ctx.send('You have entered the %s giveaway. Good luck!' % self.details)

    @commands.hybrid_command(brief='Leave a giveaway')
    async def exitgiveaway(self, ctx: commands.Context) -> None:
        if not self.live:
            await ctx.send('No giveaway is currently live')
        elif ctx.author.id not in self.entered_users:
            await ctx.send('You are not in the giveaway')
        else:
            self.entered_users.remove(ctx.author.id)
            pickle.dump(self.entered_users, open('giveaway/entered_users.txt', 'wb'))
            await ctx.send('You have left the %s giveaway.' % self.details)

    @commands.hybrid_command(brief='Clears any left over giveaway data')
    @commands.has_any_role('Admin', 'Führer')
    async def cleargiveaway(self, ctx: commands.Context) -> None:
        self.live = False
        pickle.dump(self.live, open('giveaway/live.txt', 'wb'))

        self.entered_users = []
        pickle.dump(self.entered_users, open('giveaway/entered_users.txt', 'wb'))

        self.details = None
        pickle.dump(self.details, open('giveaway/details.txt', 'wb'))

        self.msg_id = None
        pickle.dump(self.msg_id, open('giveaway/msg_id.txt', 'wb'))

        self.channel_id = None
        pickle.dump(self.channel_id, open('giveaway/channel_id.txt', 'wb'))

        await ctx.send('Giveaway contents have been cleared')

    @commands.hybrid_command(brief='Lists all users entered in the giveaway')
    async def giveawayusers(self, ctx: commands.Context) -> None:
        if self.entered_users == []:
            await ctx.send('No users have entered in the giveaway')
        else:
            list_msg = 'Here is the list of users entered in the giveaway:'
            for i in range(0, len(self.entered_users)):
                user = self.bot.get_user(self.entered_users[i])
                list_msg += '\n%d: %s' % (i+1, user.name)

            await ctx.send(list_msg)

    @commands.hybrid_command(brief='Remove someone from giveaway')
    @commands.has_any_role('Admin', 'Führer')
    async def removefromgiveaway(self, ctx: commands.Context, num_user: int) -> None:
        self.entered_users.remove(self.entered_users[int(num_user)-1])
        pickle.dump(self.entered_users, open('giveaway/entered_users.txt', 'wb'))
        await ctx.send("User %d has been removed" % int(num_user))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        reaction_channel = self.bot.get_channel(payload.channel_id)

        if reaction_channel.name == 'giveaway':
            if payload.member == self.bot.user or payload.message_id != self.msg_id:
                return

            giveaway_channel = self.bot.get_channel(self.channel_id)

            if not self.live:
                await giveaway_channel.send('No giveaway is currently live')
            elif payload.member.id in self.entered_users:
                await giveaway_channel.send('You are already entered in the giveaway')
            else:
                self.entered_users.append(payload.member.id)
                pickle.dump(self.entered_users, open('giveaway/entered_users.txt', 'wb'))
                await giveaway_channel.send('You have entered the %s giveaway. Good luck!' % self.details)

    @startgiveaway.before_invoke
    @endgiveaway.before_invoke
    @giveawaywinner.before_invoke
    @giveaway.before_invoke
    @cleargiveaway.before_invoke
    @giveawayusers.before_invoke
    @exitgiveaway.before_invoke
    @removefromgiveaway.before_invoke
    async def ensure_giveaway_channel(self, ctx):
        if ctx.channel.name != 'giveaway':
            await ctx.send('Use #giveaway channel for giveaway commands')
            raise commands.CommandError('Author not using #giveaway channel')


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
