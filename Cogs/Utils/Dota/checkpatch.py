import json
import aiohttp


async def get_patches():
    session = aiohttp.ClientSession()
    patches = await session.get('https://www.dota2.com/datafeed/patchnoteslist')
    if patches.text():
        data = json.loads(await patches.text())
    else:
        data = None
    await session.close()

    return data
