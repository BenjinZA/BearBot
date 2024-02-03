import aiohttp
from Cogs.Utils import http_util


async def leagues_to_watch():
    session = aiohttp.ClientSession()
    league_data = await http_util.send_http(session, 'get', 'https://api.opendota.com/api/leagues', retries=10)
    leagues = await league_data.json()
    await session.close()

    to_watch = {}

    if league_data.status == 200:
        for i in range(0, len(leagues)):
            if leagues[i]['tier'] == 'premium':
                to_watch[leagues[i]['leagueid']] = leagues[i]['name']

    return to_watch


async def check_winner(match_id):
    session = aiohttp.ClientSession()
    match_data = await http_util.send_http(session, 'get', 'https://api.opendota.com/api/matches/%d' % match_id, retries=10)
    match = await match_data.json()
    await session.close()

    if match_data.status == 200:
        return match['radiant_win']
    else:
        return None
