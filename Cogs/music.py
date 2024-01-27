import asyncio
import wavelink
import random
import discord
from discord.ext import commands, tasks
import ctypes.util
import platform
import json

if not discord.opus.is_loaded() and platform.system() == 'linux':
    discord.opus.load_opus(ctypes.util.find_library('opus'))


class VoiceState:

    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild

        self.saved_volume = 10
        self.music_msg = None
        self.music_channel = None
        self.voice_channel = None

        self.playlist = []

    async def set_music_msg(self, song):
        embed_music_msg = discord.Embed(title='BearBot Music Player', description=f'Now playing: {song.title}')
        embed_music_msg.set_image(url=song.artwork)
        if self.music_msg is None:
            self.music_msg = await self.music_channel.send(embed=embed_music_msg)
            await self.music_msg.add_reaction('⏯')
            await self.music_msg.add_reaction('⏩')
        else:
            await self.music_msg.edit(embed=embed_music_msg)


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.voice_states = dict()

        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()
        try:
            check_node = wavelink.Pool.get_node()
        except wavelink.exceptions.InvalidNodeException as e:
            with open('bot_info.json', 'r') as file:
                bot_info = json.load(file)

            node: wavelink.Node = wavelink.Node(uri=bot_info['lavalink_ip'], password=bot_info['lavalink_password'])
            await wavelink.Pool.connect(client=self.bot, nodes=[node])

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload):
        state = self.voice_states.get(payload.player.guild.id)
        await state.set_music_msg(payload.track)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        voice_state = self.get_voice_state(payload.player.guild)
        voice_state.play_next_song.set()

    def get_voice_state(self, guild):
        state = self.voice_states.get(guild.id)

        if state is None:
            state = VoiceState(self.bot, guild)
            self.voice_states[guild.id] = state

        return state

    async def voice_connect(self, ctx):
        await ctx.author.voice.channel.connect(cls=wavelink.Player)
        self.voice_states[ctx.guild.id].voice_channel = ctx.author.voice.channel
        await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_mute=False, self_deaf=True)

    @commands.hybrid_command(brief='View the current songs in the playlist. By default will display 10 songs.')
    async def queue(self, ctx: commands.Context, number: int = 10) -> None:
        state = self.get_voice_state(ctx.guild)
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)
        if len(player.queue) == 0:
            await ctx.send('There are currently no songs in the queue', delete_after=5)

        else:
            queue_message = '__**Current songs in queue:**__'
            for i in range(0, min(len(player.queue), number)):
                queue_message += f'\n{i + 1}: {player.queue[i].title}'

            await ctx.send(queue_message, delete_after=10)

        await ctx.message.delete()

    @commands.hybrid_command(brief='Let Bear play some music! Can create playlist with multiple calls.')
    async def play(self, ctx: commands.Context, *, link: str) -> None:
        self.voice_states[ctx.guild.id].music_channel = ctx.channel
        state = self.get_voice_state(ctx.guild)
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)

        try:
            tracks = await wavelink.Playable.search(link, source=wavelink.TrackSource.YouTube)

            if not tracks:
                await ctx.send('Could not find any songs with that query', delete_after=5)
                await ctx.message.delete()
                return

            if isinstance(tracks, wavelink.Playlist):
                added = await player.queue.put_wait(tracks)
                await ctx.send(f'Enqueued playlist {tracks.name} with {added} tracks', delete_after=5)
            else:
                track = tracks[0]
                await player.queue.put_wait(track)
                await ctx.send('Enqueued song %s' % track.title, delete_after=5)

            if not player.playing:
                await player.play(player.queue.get(), volume=state.saved_volume)

        except:
            await ctx.send('An error occurred trying to add the song to the queue', delete_after=5)
            return

        await ctx.message.delete()

    @commands.hybrid_command(brief='Shuffle the background playlist.')
    async def shuffle(self, ctx: commands.Context) -> None:
        if len(self.voice_states[ctx.guild.id].playlist) == 0:
            await ctx.send('No background playlist to shuffle', delete_after=5)

        else:
            random.shuffle(self.voice_states[ctx.guild.id].playlist)
            await ctx.send('Background playlist shuffled', delete_after=5)

        await ctx.message.delete()

    async def check_node_and_voice(self, ctx):
        if ctx.channel.name != 'music':
            await ctx.send('Use #music channel for music commands', delete_after=5)
            raise commands.CommandError('Author not using #music channel')

        check_node = False
        counter = 0
        try:
            check_node = wavelink.Pool.get_node()
        except wavelink.exceptions.InvalidNodeException as e:
            check_node_msg = await ctx.send('Music process not connected yet. ' +
                                            'This could be caused by the bot restarting.\n\n' +
                                            'The bot will attempt to connect the music process. ' +
                                            'Sit tight, your request is in the queue. ' +
                                            'This message will update once connected.'
                                            )

        while not check_node:
            if counter >= 10:
                await check_node_msg.edit(content=f'Connection attempt failed after {counter} times')
                break

            await asyncio.sleep(5)
            try:
                check_node = wavelink.Pool.get_node()
            except wavelink.exceptions.InvalidNodeException as e:
                counter += 1
            else:
                await check_node_msg.edit(content='Music process has been connected!')

    @play.before_invoke
    async def ensure_voice(self, ctx):
        await self.check_node_and_voice(ctx)
        state = self.get_voice_state(ctx.guild)
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)

        if state.voice_channel is None:
            if ctx.author.voice:
                await self.voice_connect(ctx)
                player = node.get_player(ctx.guild.id)
                player.autoplay = wavelink.AutoPlayMode.partial
            else:
                await ctx.send('User not in a voice channel', delete_after=5)
                raise commands.CommandError('Author not connected to a voice channel.')

        elif state.voice_channel is not None:
            if player.playing and ctx.author.voice.channel != state.voice_channel:
                await ctx.send('Bear is playing music in a different voice channel', delete_after=5)
                raise commands.CommandError('Bear playing in different voice channel.')
            elif not player.playing and ctx.author.voice.channel != state.voice_channel:
                await self.voice_connect(ctx)

    @commands.hybrid_command(brief='Set volume of music')
    async def volume(self, ctx: commands.Context, value: int) -> None:
        if self.voice_states[ctx.guild.id].voice_channel is None:
            await ctx.send('Bear is not playing music', delete_after=5)

        else:
            node = wavelink.Pool.get_node()
            player = node.get_player(ctx.guild.id)
            self.voice_states[ctx.guild.id].saved_volume = value
            await player.set_volume(value)
            await ctx.send('Volume set to %d%%' % value, delete_after=5)

        await ctx.message.delete()

    @commands.hybrid_command(brief='Stop the music')
    async def stop(self, ctx: commands.Context) -> None:
        if self.voice_states[ctx.guild.id].voice_channel is not None and ctx.author.voice.channel == self.voice_states[ctx.guild.id].voice_channel:
            state = self.get_voice_state(ctx.guild)
            node = wavelink.Pool.get_node()
            player = node.get_player(ctx.guild.id)
            del self.voice_states[ctx.guild.id]
            await player.disconnect(force=True)

        await ctx.message.delete()

    @commands.hybrid_command(brief='Pause currently playing song')
    async def pause(self, ctx: commands.Context) -> None:
        if self.voice_states[ctx.guild.id].voice_channel is not None and ctx.author.voice.channel == self.voice_states[ctx.guild.id].voice_channel:
            node = wavelink.Pool.get_node()
            player = node.get_player(ctx.guild.id)
            if not player.paused:
                await player.pause(True)
                await ctx.send('Music has been paused. Use the ?resume command to un-pause', delete_after=5)

        await ctx.message.delete()

    @commands.hybrid_command(brief='Resume playing music')
    async def resume(self, ctx: commands.Context) -> None:
        if self.voice_states[ctx.guild.id].voice_channel is not None and ctx.author.voice.channel == self.voice_states[ctx.guild.id].voice_channel:
            node = wavelink.Pool.get_node()
            player = node.get_player(ctx.guild.id)
            if player.paused:
                await player.pause(False)
                await ctx.send('Music resumed', delete_after=5)

        await ctx.message.delete()

    @commands.hybrid_command(brief='Skip current song')
    async def skip(self, ctx: commands.Context, number_skip: int = 1) -> None:
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)

        if number_skip < 1:
            await ctx.send('Please specify a correct number of songs to skip', delete_after=5)
            return

        number_skip = min(number_skip, await self.voice_states[ctx.guild.id].songs.qsize(player))

        if number_skip == 0 and self.voice_states[ctx.guild.id].voice_channel is not None:
            number_skip = 1

        if self.voice_states[ctx.guild.id].voice_channel is not None and ctx.author.voice.channel == self.voice_states[
            ctx.guild.id].voice_channel:
            node = wavelink.Pool.get_node()
            player = node.get_player(ctx.guild.id)
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
        await self.check_node_and_voice(ctx)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        self.get_voice_state(reaction.message.guild)

        if reaction.message.channel.name == 'music':
            if user == self.bot.user or reaction.message.id != self.voice_states[reaction.message.guild.id].music_msg.id:
                return

            node = wavelink.Pool.get_node()
            player = node.get_player(reaction.message.guild.id)

            if reaction.emoji == '⏯':
                if player.paused:
                    await player.pause(False)
                else:
                    await player.pause(True)
                await reaction.message.remove_reaction('⏯', user)

            if reaction.emoji == '⏩':
                await player.stop()
                await reaction.message.remove_reaction('⏩', user)


async def setup(bot):
    await bot.add_cog(Music(bot))
