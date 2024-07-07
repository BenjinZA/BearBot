from suno import Suno, ModelVersions
import json

with open('bot_info.json', 'r') as file:
    bot_info = json.load(file)

suno_cookie = bot_info['suno_cookie']

try:
    suno_client = Suno(cookie=suno_cookie, model_version=ModelVersions.CHIRP_V3_5)
except:
    suno_client = None


def get_suno_song(url):
    if 'https://suno.com/song/' not in url:
        return None, None, None

    if not suno_client:
        return 'update cookie', None, None

    song_id = url.replace('https://suno.com/song/', '')
    song = suno_client.get_song(song_id)

    return song.audio_url, song.image_url, song.title
