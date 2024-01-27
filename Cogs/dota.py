import tabulate
import discord
from discord.ext import commands
from Cogs.Utils import opendota
from Cogs.Utils import user
from Cogs.Utils import reddit

sID = user.steamID()


class Dota(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(brief='Stores all Discord IDs of current server into database')
    async def loadids(self, ctx: commands.Context) -> None:
        for member in ctx.guild.members:
            sID.storeDiscordID(member.name, member.id)

        await ctx.send('Discord IDs for members of server %s have successfully been loaded' % ctx.guild.name)

    @commands.hybrid_command(brief='Saves Steam ID to database. Uses steamID3 (same ID as opendota)')
    async def steamid(self, ctx: commands.Context, s: str = '', name: str = '') -> None:
        if not s.isdigit():
            await ctx.send('Invalid Steam ID supplied for user %s.' % ctx.author)
            return

        if name == '':
            dID = ctx.author.id
            name = ctx.author.name
        else:
            try:
                dID = sID.nameLinks[name]
            except:
                await ctx.send('No member with name %s on server' % name)
                return

        sID.storeSteamID(dID, s)
        await ctx.send('Steam ID has been stored for user %s' % name)

    @commands.hybrid_command(brief='Generates Dota 2 word cloud for user')
    async def wordcloud(self, ctx: commands.Context, name: str = '') -> None:
        if name == '':
            s = sID.returnSteamID(ctx.author.id)
        else:
            s = sID.returnSteamID(sID.returnDiscordID(name))

        if s == -1:
            await ctx.send(sID.noID(ctx.author))
            return

        try:
            wc = await opendota.getWordcloud(s)
            await ctx.send('Here is the Dota 2 wordcloud for %s' % await opendota.getPlayerName(s), file=discord.File(wc))
        except:
            await ctx.send(await opendota.noData(s, 'Steam ID'))

    @commands.hybrid_command(brief='Dota 2 win rate of user')
    async def wr(self, ctx: commands.Context, name: str = '') -> None:
        if name == '':
            s = sID.returnSteamID(ctx.author.id)
        else:
            s = sID.returnSteamID(sID.returnDiscordID(name))

        if s == -1:
            await ctx.send(sID.noID(ctx.author))
            return

        try:
            wl = await opendota.getWinLoss(s)
            wins = wl['win']
            games = wl['win'] + wl['lose']
            winrate = str(round(wins * 100 / games, 2)) + '%'
            await ctx.send('%s has won %d out of %d Dota 2 matches (%s)' % (await opendota.getPlayerName(s), wins, games, winrate))
        except:
            await ctx.send(await opendota.noData(s, 'Steam ID'))

    @commands.hybrid_command(brief='Dota 2 averages of user')
    async def averages(self, ctx: commands.Context, name: str = '') -> None:
        if name == '':
            s = sID.returnSteamID(ctx.author.id)
        else:
            s = sID.returnSteamID(sID.returnDiscordID(name))

        if s == -1:
            await ctx.send(sID.noID(ctx.author))
            return

        try:
            averages = await opendota.getAverages(s)
            msgStr = 'Here are some Dota 2 averages for %s. Pro or scrub?\n\n' % await opendota.getPlayerName(s)
            msgStr += '`' + str(tabulate.tabulate(averages, headers=['Stat', 'Average'], floatfmt='.2f')) + '`'
            await ctx.send(msgStr)
        except:
            await ctx.send(await opendota.noData(s, 'Steam ID'))

    @commands.hybrid_command(brief='Stats from last Dota 2 match played by user')
    async def lastmatch(self, ctx: commands.Context, name: str = '') -> None:
        if name == '':
            s = sID.returnSteamID(ctx.author.id)
        else:
            s = sID.returnSteamID(sID.returnDiscordID(name))

        if s == -1:
            await ctx.send(sID.noID(ctx.author))
            return

        try:
            m = await opendota.getRecentMatch(s)
            matchInfo = opendota.getMatch(m)
            await matchInfo.get_match_data()

            msgStr = 'The winner of Match ID %s was The %s, with the game lasting %s minutes\n\n' % (m, matchInfo.winner, matchInfo.duration)
            radiantStr = '`THE RADIANT`\n`' + str(tabulate.tabulate(matchInfo.radiant, headers=['Name                ', 'Hero             ', 'Kills', 'Deaths', 'Assists', 'GPM', 'XPM'], floatfmt='.2f', tablefmt='fancy_grid')) + '`\n\n'
            direStr = '`THE DIRE`\n`' + str(tabulate.tabulate(matchInfo.dire, headers=['Name                ', 'Hero             ', 'Kills', 'Deaths', 'Assists', 'GPM', 'XPM'], floatfmt='.2f', tablefmt='fancy_grid')) + '`'

            await ctx.send(msgStr)
            await ctx.send(radiantStr)
            await ctx.send(direStr)
        except:
            await ctx.send(await opendota.noData(s, 'Steam ID'))

    @commands.hybrid_command(brief='Stats for Dota 2 game from given match ID')
    async def match(self, ctx: commands.Context, m: str = '') -> None:
        try:
            matchInfo = opendota.getMatch(m)
            await matchInfo.get_match_data()

            msgStr = 'The winner of Match ID %s was The %s, with the game lasting %s minutes\n\n' % (m, matchInfo.winner, matchInfo.duration)
            radiantStr = '`THE RADIANT`\n`' + str(tabulate.tabulate(matchInfo.radiant, headers=['Name                ', 'Hero             ', 'Kills', 'Deaths', 'Assists', 'GPM', 'XPM'], floatfmt='.2f', tablefmt='fancy_grid')) + '`\n\n'
            direStr = '`THE DIRE`\n`' + str(tabulate.tabulate(matchInfo.dire, headers=['Name                ', 'Hero             ', 'Kills', 'Deaths', 'Assists', 'GPM', 'XPM'], floatfmt='.2f', tablefmt='fancy_grid')) + '`'

            await ctx.send(msgStr)
            await ctx.send(radiantStr)
            await ctx.send(direStr)
        except:
            await ctx.send(await opendota.noData(m, 'Match ID'))

    @commands.hybrid_command(brief='Gives match IDs and heroes played of user. Default 5, can specify for more')
    async def matchids(self, ctx: commands.Context, limit: int = 5, name: str = '') -> None:
        if name == '':
            s = sID.returnSteamID(ctx.author.id)
        else:
            s = sID.returnSteamID(sID.returnDiscordID(name))

        matchIDs = await opendota.getMatchIDs(s, limit)

        msgStr = 'Here are the last %d matches played by %s\n\n' % (limit, await opendota.getPlayerName(s))
        msgStr += '`' + str(tabulate.tabulate(matchIDs, headers=['Match ID', 'Hero'], tablefmt='orgtbl')) + '`'

        await ctx.send(msgStr)

    @commands.hybrid_command(brief='Check Dota 2 subreddit vir latest update thread from SirBelvedere')
    async def update(self, ctx: commands.Context) -> None:
        r = await reddit.newUserPost('Dota2', 'SirBelvedere')
        await ctx.send(r[0] + '\n\n' + r[1])

    @commands.hybrid_command(brief='Check for latest Dota 2 blog post')
    async def blog(self, ctx: commands.Context) -> None:
        r = await reddit.newUserPost('Dota2', 'wykrhm')
        await ctx.send(r[0] + '\n\n' + r[1])


async def setup(bot):
    await bot.add_cog(Dota(bot))
