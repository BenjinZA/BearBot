import json
import aiohttp


async def get_patches():
    session = aiohttp.ClientSession()
    url_response = await session.get('https://www.dota2.com/datafeed/patchnoteslist')
    patches = await url_response.text()
    if patches:
        data = json.loads(patches)
    else:
        data = None
    await session.close()

    return data
