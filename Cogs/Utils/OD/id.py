import requests as r
import json as j


def GetHeroID():
    hero_data = r.get('https://api.opendota.com/api/heroes')
    hero_id = j.loads(hero_data.text)
    return hero_id


hero_dic = {}

heroes = GetHeroID()

for hero in heroes:
    hero_dic[hero['id']] = hero['localized_name']


def GetItemID():
    item_data = r.get('https://api.opendota.com/api/explorer', {'sql': 'select * from items'})
    item_id = j.loads(item_data.text)
    return item_id['rows']


item_dic = {}

items = GetItemID()

for item in items:
    item_dic[item['id']] = item['localized_name']


game_mode_dic = {
    0: 'None',
    1: 'All Pick',
    2: 'Captain’s Mode',
    3: 'Random Draft',
    4: 'Single Draft',
    5: 'All Random',
    6: 'Intro',
    7: 'Diretide',
    8: 'Reverse Captain’s Mode',
    9: 'The Greeviling',
    10: 'Tutorial',
    11: 'Mid Only',
    12: 'Least Played',
    13: 'New Player Pool',
    14: 'Compendium Matchmaking',
    16: 'Captain’s Draft',
    22: 'Ranked All Pick'
    }
