import aiohttp
from Cogs.Utils import http_util


async def leagues_to_watch():
    session = aiohttp.ClientSession()
    league_data = await http_util.send_http(session, 'get', 'https://api.opendota.com/api/leagues', retries=10)
    leagues = await league_data.json()
    session.close()

    to_watch = {}

    if league_data.status == 200:
        for i in range(0, len(leagues)):
            if leagues[i]['tier'] == 'premium':
                to_watch[leagues[i]['leagueid']] = leagues[i]['name']

    return to_watch


async def get_live_games():
    session = aiohttp.ClientSession()
    live_data = await http_util.send_http(session, 'get', 'http://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v1?key=STEAM_API_KEY', retries=10)
    live_games = await live_data.json()
    session.close()

    try:
        to_watch = await leagues_to_watch()
    except:
        print('Error getting leagues - leagues_to_watch')
        return []

    matches = []

    if live_data.status == 200:
        for i in range(0, len(live_games['result']['games'])):
            if live_games['result']['games'][i]['league_id'] in to_watch and 'radiant_team' in live_games['result']['games'][i]:
                league_name = to_watch[live_games['result']['games'][i]['league_id']]
                match_id = live_games['result']['games'][i]['match_id']
                radiant_team = live_games['result']['games'][i]['radiant_team']['team_name']
                dire_team = live_games['result']['games'][i]['dire_team']['team_name']
                matches.append({'league_name': league_name, 'match_id': match_id, 'radiant_team': radiant_team, 'dire_team': dire_team})

    return matches


async def check_winner(match_id):
    session = aiohttp.ClientSession()
    match_data = await http_util.send_http(session, 'get', 'https://api.opendota.com/api/matches/%d' % match_id, retries=10)
    match = await match_data.json()
    session.close()

    if match_data.status == 200:
        return match['radiant_win']
    else:
        return None


async def check_if_still_live(match_id):
    session = aiohttp.ClientSession()
    match_data = await http_util.send_http(session, 'get', 'http://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v1?key=STEAM_API_KEY&match_id=%d' % match_id, retries=10)
    match = await match_data.json()
    session.close()

    if match_data.status == 200:
        if match['result']['games']:
            return True
        else:
            return False
    else:
        return None
