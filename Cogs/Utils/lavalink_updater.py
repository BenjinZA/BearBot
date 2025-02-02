import aiohttp
import json
from pathlib import Path


async def download_lavalink():
    success = False
    lavalink_success = False
    youtube_success = False

    lavalink_path = Path(__file__).parents[2] / 'Lavalink'

    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.github.com/repos/lavalink-devs/Lavalink/releases/latest') as url_response:
            if url_response.status == 200:
                releases = await url_response.text()
                data = json.loads(releases)
                async with session.get(data['assets'][0]['browser_download_url']) as resp:
                    if resp.status == 200:
                        lavalink_success = True
                        with open(lavalink_path / 'Lavalink.jar', 'wb') as file:
                            async for chunk in resp.content.iter_chunked(10):
                                file.write(chunk)

        async with session.get('https://api.github.com/repos/lavalink-devs/youtube-source/releases/latest') as url_response:
            if url_response.status == 200:
                releases = await url_response.text()
                data = json.loads(releases)
                new_version = data['name']

                with open(lavalink_path / 'application.yml', 'r') as file:
                    lavalink_config = file.readlines()

                    for i in range(len(lavalink_config)):
                        if 'dev.lavalink.youtube:youtube-plugin' in lavalink_config[i]:
                            lavalink_config[i] = lavalink_config[i].replace(lavalink_config[i][55:-2], new_version)

                with open(lavalink_path / 'application.yml', 'w') as file:
                    file.writelines(lavalink_config)
                    youtube_success = True

    if lavalink_success and youtube_success:
        success = True

    return success
