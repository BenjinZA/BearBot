import json as j

import numpy as np
import aiohttp
from PIL import Image
from wordcloud import WordCloud

import Cogs.Utils.OD.id


async def getWordcloud(steamid):
    session = aiohttp.ClientSession()
    words = await session.get('https://api.opendota.com/api/players/%s/wordcloud' % steamid)
    data = j.loads(await words.text())
    await session.close()

    oval_mask = np.array(Image.open('Cogs/Utils/wordcloud/oval.jpg'))
    wordcloud = WordCloud(background_color='#474d56', prefer_horizontal=1, mask=oval_mask, colormap='hsv')
    wordcloud.generate_from_frequencies(frequencies=data['my_word_counts'])
    filename = 'Cogs/Utils/wordcloud/wordcloud.png'
    wordcloud.to_file(filename)

    return filename


async def getPlayerName(steamid):
    session = aiohttp.ClientSession()
    player = await session.get('https://api.opendota.com/api/players/%s' % steamid)
    playerData = j.loads(await player.text())
    await session.close()
    return playerData['profile']['personaname']


async def getWinLoss(steamid):
    session = aiohttp.ClientSession()
    wl = await session.get('https://api.opendota.com/api/players/%s/wl' % steamid)
    wlData = j.loads(await wl.text())
    await session.close()
    return wlData


async def getAverages(steamid):
    session = aiohttp.ClientSession()
    totals = await session.get('https://api.opendota.com/api/players/%s/totals' % steamid)
    totalsData = j.loads(await totals.text())
    await session.close()

    kills = round(totalsData[0]['sum'] / totalsData[0]['n'], 2)
    deaths = round(totalsData[1]['sum'] / totalsData[1]['n'], 2)
    assists = round(totalsData[2]['sum'] / totalsData[2]['n'], 2)
    gpm = round(totalsData[4]['sum'] / totalsData[4]['n'], 2)
    xpm = round(totalsData[5]['sum'] / totalsData[5]['n'], 2)
    lh = round(totalsData[6]['sum'] / totalsData[6]['n'], 2)
    denies = round(totalsData[7]['sum'] / totalsData[7]['n'], 2)
    gamelength = round(totalsData[9]['sum'] / totalsData[9]['n'] / 60, 2)

    averages = [['Kills', kills], ['Deaths', deaths], ['Assists', assists], ['GPM', gpm], ['XPM', xpm], ['Last hits', lh], ['Denies', denies], ['Game length', gamelength]]
    return averages


async def getRecentMatch(steamid):
    session = aiohttp.ClientSession()
    playerMatch = await session.get('https://api.opendota.com/api/players/%s/matches?limit=1' % steamid)
    playerMatchData = j.loads(await playerMatch.text())
    await session.close()
    matchid = playerMatchData[0]['match_id']
    return matchid


class getMatch():

    def __init__(self, matchid):

        self.matchid = matchid
        self.matchData = None
        self.winner = None
        self.duration = None
        self.radiant = None
        self.dire = None

    async def get_match_data(self):
        session = aiohttp.ClientSession()
        matchstats = await session.get('https://api.opendota.com/api/matches/%s' % self.matchid)
        self.matchData = j.loads(await matchstats.text())
        await session.close()

        self.winner = 'Radiant'
        if not self.matchData['radiant_win']:
            self.winner = 'Dire'

        self.duration = round(self.matchData['duration'] / 60, 2)

        self.radiant = [[], [], [], [], []]

        self.dire = [[], [], [], [], []]

        for i in range(0, 5):
            playerData = self.matchData['players'][i]
            if playerData['account_id'] == None:
                playerName = 'Anonymous'
            else:
                playerName = await getPlayerName(playerData['account_id'])
            hero = Cogs.Utils.OD.id.hero_dic[playerData['hero_id']]
            kills = playerData['kills']
            deaths = playerData['deaths']
            assists = playerData['assists']
            gpm = playerData['gold_per_min']
            xpm = playerData['xp_per_min']

            self.radiant[i] = [playerName[:20], hero, kills, deaths, assists, gpm, xpm]

        for i in range(5, 10):
            playerData = self.matchData['players'][i]
            if playerData['account_id'] == None:
                playerName = 'Anonymous'
            else:
                playerName = await getPlayerName(playerData['account_id'])
            hero = Cogs.Utils.OD.id.hero_dic[playerData['hero_id']]
            kills = playerData['kills']
            deaths = playerData['deaths']
            assists = playerData['assists']
            gpm = playerData['gold_per_min']
            xpm = playerData['xp_per_min']

            self.dire[i - 5] = [playerName[:20], hero, kills, deaths, assists, gpm, xpm]


async def getMatchIDs(steamid, limit):
    session = aiohttp.ClientSession()
    matches = await session.get('https://api.opendota.com/api/players/%s/matches?limit=%d' % (steamid, limit))
    matchesData = j.loads(await matches.text())
    await session.close()

    matchesIDs = []

    for i in range(0, len(matchesData)):
        matchesIDs.append([matchesData[i]['match_id'], Cogs.Utils.OD.id.hero_dic[matchesData[i]['hero_id']]])

    return matchesIDs


async def noData(givenID, type):
    return 'Opendota has no data for %s %s' % (type, givenID)

