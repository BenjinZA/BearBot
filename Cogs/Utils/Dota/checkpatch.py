import json
import aiohttp


async def get_patches():
    session = aiohttp.ClientSession()
    patches = await session.get('https://www.dota2.com/datafeed/patchnoteslist')
    data = json.loads(await patches.text())
    await session.close()

    return data
