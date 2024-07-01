from suno import Suno, ModelVersions
from pathlib import Path
import json
import os

with open('bot_info.json', 'r') as file:
    bot_info = json.load(file)

suno_cookie = bot_info['suno_cookie']

suno_client = Suno(cookie=suno_cookie, model_version=ModelVersions.CHIRP_V3_5)


def download_suno_song(url):
    if 'https://suno.com/song/' not in url:
        return

    song_id = url.replace('https://suno.com/song/', '')

    abs_path = os.path.abspath('suno_cache')
    song_path = abs_path.replace('\\', '/') + '/SunoMusic-' + song_id + '.mp3'

    if Path(song_path).is_file():
        return song_path

    song = suno_client.get_song(song_id)
    suno_files = [f for f in sorted(Path('suno_cache/.').glob('**/*'), key=os.path.getmtime)]
    suno_cache_size = sum(f.stat().st_size for f in suno_files) / (1024 ** 2)

    while suno_cache_size > 100:
        suno_files[0].unlink()
        suno_files.pop(0)
        suno_cache_size = sum(f.stat().st_size for f in suno_files) / (1024 ** 2)

    suno_client.download(song, abs_path)

    return song_path
