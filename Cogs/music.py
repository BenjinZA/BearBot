import asyncio
import wavelink
import random
import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import ctypes.util
import platform
import re

RURL = re.compile('https?:\/\/(?:www\.)?.+')

client_credentials_manager = SpotifyClientCredentials('spotify_client_id', 'spotify_client_secret')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

if not discord.opus.is_loaded() and platform.system() == 'linux':
    discord.opus.load_opus(ctypes.util.find_library('opus'))


async def get_spotify_tracks(playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    tracks_list = list()
    for track in tracks:
        if track['track']:
            tracks_list.append(track['track']['artists'][0]['name'] + ' ' + track['track']['name'])

    return tracks_list


class BearQueue:

    def __init__(self, queue):
        self.queue = queue
        self.song_list = []

    async def put(self, song):
        await self.queue.put(song)
        self.song_list.append(song.title)

    async def get(self):
        return await self.queue.get()

    async def song_finish(self):
        self.song_list.pop(0)

    async def qsize(self):
        return self.queue.qsize()


class VoiceState:

    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id

        self.songs = BearQueue(asyncio.Queue())
        self.play_next_song = asyncio.Event()

        self.audio_player = self.bot.loop.create_task(self.audio_player_task())
        self.disconnect_if_not_playing = self.bot.loop.create_task(self.disconnect_if_not_playing())

        self.saved_volume = 10
        self.music_msg = None
        self.music_channel = None
        self.voice_channel = None

        self.playlist = []
        self.process_playlist = False

    async def get_tracks(self, link):
        if not RURL.match(link):
            link = f'ytsearch:{link}'

        tracks = []
        counter = 0
        while not tracks and counter < 10:
            tracks = await self.bot.wavelink.get_tracks(f'{link}')
            counter += 1
        return tracks

    async def audio_player_task(self):
        await self.bot.wait_until_ready()

        player = self.bot.wavelink.get_player(self.guild_id)
        await player.set_volume(self.saved_volume)

        while True:
            self.play_next_song.clear()
            song = await self.songs.get()

            await player.play(song)

            await self.set_music_msg(song)
            await self.play_next_song.wait()
            await self.songs.song_finish()
            if len(self.songs.song_list) == 0 and len(self.playlist) > 0:
                track = self.playlist[0]
                self.playlist.pop(0)
                await self.songs.put(track)

    async def set_music_msg(self, song):
        embed_music_msg = discord.Embed(title='BearBot Music Player', description='Now playing: %s' % song.title)
        embed_music_msg.set_image(url=song.thumb)
        if self.music_msg is None:
            self.music_msg = await self.music_channel.send(embed=embed_music_msg)
            await self.music_msg.add_reaction('⏯')
            await self.music_msg.add_reaction('⏩')
        else:
            await self.music_msg.edit(embed=embed_music_msg)

    async def disconnect_if_not_playing(self):
        counter = 0
        while True:
            await asyncio.sleep(60)
            if self.voice_channel:
                player = self.bot.wavelink.get_player(self.guild_id)

                if player.is_playing or len(self.voice_channel.members) > 1:
                    counter = 0
                else:
                    counter += 1

                if counter >= 5:
                    await player.disconnect()


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.voice_states = dict()

        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)

        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()
        node = await self.bot.wavelink.initiate_node(host='127.0.0.1',
                                                     port=2333,
                                                     rest_uri='http://127.0.0.1:2333',
                                                     password='uXEIieJRIszbFuXzMoR3',
                                                     identifier='BearBotZA',
                                                     region='southafrica')

        node.set_hook(self.on_event_hook)

    async def on_event_hook(self, event):
        if isinstance(event, (wavelink.TrackEnd, wavelink.TrackException)):
            voice_state = self.get_voice_state(event.player.guild_id)
            voice_state.play_next_song.set()

    def get_voice_state(self, guild_id):
        state = self.voice_states.get(guild_id)

        if state is None:
            state = VoiceState(self.bot, guild_id)
            self.voice_states[guild_id] = state

        return state

    @commands.command(brief='View the current songs in the playlist. By default will display 10 songs.')
    async def queue(self, ctx, number=10):
        if len(self.voice_states[ctx.guild.id].songs.song_list) == 0:
            await ctx.send('There are currently no songs in the playlist', delete_after=5)

        else:
            queue_message = '__**Current songs in queue:**__'
            for i in range(0, min(len(self.voice_states[ctx.guild.id].songs.song_list), number)):
                queue_message += '\n%d: %s' % (i + 1, self.voice_states[ctx.guild.id].songs.song_list[i])

            await ctx.send(queue_message, delete_after=10)

        await ctx.message.delete()

    @commands.command(brief='Let Bear play some music! Can create playlist with multiple calls')
    async def play(self, ctx, *, link):
        self.voice_states[ctx.guild.id].music_channel = ctx.channel
        state = self.get_voice_state(ctx.guild.id)

        if '/playlist?list=' in link:
            tracks = await self.bot.wavelink.get_tracks(f'{link}')

            if len(tracks.tracks) == 0:
                await ctx.send('An error occurred trying to process the playlist', delete_after=5)
                return

            await ctx.send('Processing YouTube playlist with %d songs.' % len(tracks.tracks), delete_after=5)
            await ctx.message.delete()

            await self.voice_states[ctx.guild.id].songs.put(tracks.tracks[0])
            tracks.tracks.pop(0)

            for track in tracks.tracks:
                self.voice_states[ctx.guild.id].playlist.append(track)

        elif 'open.spotify.com/playlist/' in link:
            spotify_tracks = await get_spotify_tracks(link.split('/')[-1])
            await ctx.send('Processing Spotify playlist with %d songs.' % len(spotify_tracks), delete_after=5)
            await ctx.message.delete()

            state.process_playlist = True

            tracks = await state.get_tracks(spotify_tracks[0])
            await self.voice_states[ctx.guild.id].songs.put(tracks[0])
            spotify_tracks.pop(0)

            for spotify_track in spotify_tracks:
                tracks = await state.get_tracks(spotify_track)
                if state.process_playlist:
                    self.voice_states[ctx.guild.id].playlist.append(tracks[0])
                else:
                    return

        else:
            try:
                tracks = await state.get_tracks(link)

                if not tracks:
                    await ctx.send('Could not find any songs with that query', delete_after=5)
                    await ctx.message.delete()
                    return

                track = tracks[0]

                await self.voice_states[ctx.guild.id].songs.put(track)

            except:
                await ctx.send('An error occurred trying to add the song to the queue', delete_after=5)
                return

            await ctx.send('Enqueued song %s' % track.title, delete_after=5)
            await ctx.message.delete()

    @commands.command(brief='Shuffle the background playlist.')
    async def shuffle(self, ctx):
        if len(self.voice_states[ctx.guild.id].playlist) == 0:
            await ctx.send('No background playlist to shuffle', delete_after=5)

        else:
            random.shuffle(self.voice_states[ctx.guild.id].playlist)
            await ctx.send('Background playlist shuffled', delete_after=5)

        await ctx.message.delete()

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.channel.name != 'music':
            await ctx.send('Use #music channel for music commands', delete_after=5)
            raise commands.CommandError('Author not using #music channel')

        self.get_voice_state(ctx.guild.id)
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if self.voice_states[ctx.guild.id].voice_channel is None:
            if ctx.author.voice:
                await player.connect(ctx.author.voice.channel.id)
                self.voice_states[ctx.guild.id].voice_channel = ctx.author.voice.channel
            else:
                await ctx.send('User not in a voice channel', delete_after=5)
                raise commands.CommandError('Author not connected to a voice channel.')

        elif self.voice_states[ctx.guild.id].voice_channel is not None:
            if player.is_playing and ctx.author.voice.channel != self.voice_states[ctx.guild.id].voice_channel:
                await ctx.send('Bear is playing music in a different voice channel', delete_after=5)
                raise commands.CommandError('Bear playing in different voice channel.')
            else:
                await player.connect(ctx.author.voice.channel.id)
                self.voice_states[ctx.guild.id].voice_channel = ctx.author.voice.channel

    @commands.command(brief='Set volume of music')
    async def volume(self, ctx, value: int):
        if self.voice_states[ctx.guild.id].voice_channel is None:
            ctx.send('Bear is not playing music', delete_after=5)

        else:
            player = self.bot.wavelink.get_player(ctx.guild.id)
            self.voice_states[ctx.guild.id].saved_volume = value
            await player.set_volume(value)
            await ctx.send('Volume set to %d%%' % value, delete_after=5)

        await ctx.message.delete()

    @commands.command(brief='Stop the music')
    async def stop(self, ctx):
        if self.voice_states[ctx.guild.id].voice_channel is not None and ctx.author.voice.channel == self.voice_states[ctx.guild.id].voice_channel:
            state = self.get_voice_state(ctx.guild.id)
            state.process_playlist = False
            player = self.bot.wavelink.get_player(ctx.guild.id)
            del self.voice_states[ctx.guild.id]
            await player.destroy()

        await ctx.message.delete()

    @commands.command(brief='Pause currently playing song')
    async def pause(self, ctx):
        if self.voice_states[ctx.guild.id].voice_channel is not None and ctx.author.voice.channel == self.voice_states[ctx.guild.id].voice_channel:
            player = self.bot.wavelink.get_player(ctx.guild.id)
            if not player.paused:
                await player.set_pause(True)
                await ctx.send('Music has been paused. Use the ?resume command to un-pause', delete_after=5)

        await ctx.message.delete()

    @commands.command(brief='Resume playing music')
    async def resume(self, ctx):
        if self.voice_states[ctx.guild.id].voice_channel is not None and ctx.author.voice.channel == self.voice_states[ctx.guild.id].voice_channel:
            player = self.bot.wavelink.get_player(ctx.guild.id)
            if player.paused:
                await player.set_pause(False)
                await ctx.send('Music resumed', delete_after=5)

        await ctx.message.delete()

    @commands.command( brief='Skip current song')
    async def skip(self, ctx, number_skip=1):
        if number_skip < 1:
            await ctx.send('Please specify a correct number of songs to skip', delete_after=5)
            return

        number_skip = min(number_skip, await self.voice_states[ctx.guild.id].songs.qsize())

        if number_skip == 0 and self.voice_states[ctx.guild.id].voice_channel is not None:
            number_skip = 1

        if self.voice_states[ctx.guild.id].voice_channel is not None and ctx.author.voice.channel == self.voice_states[ctx.guild.id].voice_channel:
            player = self.bot.wavelink.get_player(ctx.guild.id)
            for i in range(1, number_skip):
                await self.voice_states[ctx.guild.id].songs.get()
                await self.voice_states[ctx.guild.id].songs.song_finish()
            await player.stop()

            await ctx.send('%d song(s) skipped' % number_skip, delete_after=5)

        await ctx.message.delete()

    @queue.before_invoke
    @volume.before_invoke
    @stop.before_invoke
    @pause.before_invoke
    @resume.before_invoke
    @skip.before_invoke
    @shuffle.before_invoke
    async def ensure_music_channel(self, ctx):
        self.get_voice_state(ctx.guild.id)

        if ctx.channel.name != 'music':
            await ctx.send('Use #music channel for music commands', delete_after=5)
            raise commands.CommandError('Author not using #music channel')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        self.get_voice_state(reaction.message.guild.id)

        if reaction.message.channel.name == 'music':
            if user == self.bot.user or reaction.message.id != self.voice_states[reaction.message.guild.id].music_msg.id:
                return

            player = self.bot.wavelink.get_player(reaction.message.guild.id)

            if reaction.emoji == '⏯':
                if player.is_paused:
                    await player.set_pause(False)
                else:
                    await player.set_pause(True)
                await reaction.message.remove_reaction('⏯', user)

            if reaction.emoji == '⏩':
                await player.stop()
                await reaction.message.remove_reaction('⏩', user)


def setup(bot):
    bot.add_cog(Music(bot))
