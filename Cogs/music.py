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


class VolumeButtons(discord.ui.View):

    def __init__(self, player):
        super().__init__()
        self.player = player

    @discord.ui.button(label='10', style=discord.ButtonStyle.grey)
    async def volume_10(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(10)
        await interaction.message.delete()

    @discord.ui.button(label='20', style=discord.ButtonStyle.grey)
    async def volume_20(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(20)
        await interaction.message.delete()

    @discord.ui.button(label='30', style=discord.ButtonStyle.grey)
    async def volume_30(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(30)
        await interaction.message.delete()

    @discord.ui.button(label='40', style=discord.ButtonStyle.grey)
    async def volume_40(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(40)
        await interaction.message.delete()

    @discord.ui.button(label='50', style=discord.ButtonStyle.grey)
    async def volume_50(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(50)
        await interaction.message.delete()

    @discord.ui.button(label='60', style=discord.ButtonStyle.grey)
    async def volume_60(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(60)
        await interaction.message.delete()

    @discord.ui.button(label='70', style=discord.ButtonStyle.grey)
    async def volume_70(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(70)
        await interaction.message.delete()

    @discord.ui.button(label='80', style=discord.ButtonStyle.grey)
    async def volume_80(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(80)
        await interaction.message.delete()

    @discord.ui.button(label='90', style=discord.ButtonStyle.grey)
    async def volume_90(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(90)
        await interaction.message.delete()

    @discord.ui.button(label='100', style=discord.ButtonStyle.grey)
    async def volume_100(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(100)
        await interaction.message.delete()


class MusicButtons(discord.ui.View):

    def __init__(self, player, music):
        super().__init__()
        self.player = player
        self.music = music

    @discord.ui.button(label='Pause', emoji='⏸️', style=discord.ButtonStyle.grey)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.paused:
            await self.player.pause(False)
            button.style=discord.ButtonStyle.grey
            button.label = 'Pause'
            button.emoji = '⏸️'
            await interaction.response.edit_message(view=self)
        else:
            await self.player.pause(True)
            button.style=discord.ButtonStyle.green
            button.label = 'Play'
            button.emoji = '▶️'
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Skip', emoji='⏭️', style=discord.ButtonStyle.blurple)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.stop()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Set volume', emoji='🔊', style=discord.ButtonStyle.green)
    async def volume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send('Pick volume', view=VolumeButtons(self.player))
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Disconnect', emoji='⏹️', style=discord.ButtonStyle.red)
    async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music.player_disconnect(interaction.guild)


class VoiceState:

    def __init__(self, bot, guild, music):
        self.bot = bot
        self.guild = guild
        self.music = music

        self.saved_volume = 10
        self.music_msg = None
        self.music_channel = None
        self.voice_channel = None

    async def set_music_msg(self, song, player):
        embed_music_msg = discord.Embed(title='BearBot Music Player', description=f'Now playing: {song.title}')
        embed_music_msg.set_image(url=song.artwork)
        if self.music_msg is None:
            self.music_msg = await self.music_channel.send(embed=embed_music_msg, view=MusicButtons(player, self.music))
        else:
            await self.music_msg.edit(embed=embed_music_msg)

    async def start_audio_player(self):
        self.disconnect_if_not_playing.start()

    async def stop_audio_player(self):
        self.disconnect_if_not_playing.cancel()

    @tasks.loop()
    async def disconnect_if_not_playing(self):
        counter = 0
        while True:
            await asyncio.sleep(60)
            if self.voice_channel:
                node = wavelink.Pool.get_node()
                player = node.get_player(self.guild.id)

                if player.playing:
                    counter = 0
                else:
                    counter += 1

                if counter >= 5:
                    await self.music.player_disconnect(self.guild)


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
        await state.set_music_msg(payload.track, payload.player)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        state = self.get_voice_state(payload.player.guild)
        state.play_next_song.set()

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        await self.player_disconnect(player.guild)

    async def player_disconnect(self, guild):
        state = self.get_voice_state(guild)
        node = wavelink.Pool.get_node()
        player = node.get_player(guild.id)

        embed = state.music_msg.embeds[0]
        embed.title = embed.title + ' (disconnected)'
        await state.music_msg.edit(embed=embed, view=None)

        await player.disconnect(force=True)
        del self.voice_states[guild.id]

    def get_voice_state(self, guild):
        state = self.voice_states.get(guild.id)

        if state is None:
            state = VoiceState(self.bot, guild, self)
            self.voice_states[guild.id] = state

        return state

    async def voice_connect(self, ctx):
        await ctx.author.voice.channel.connect(cls=wavelink.Player)
        await self.voice_states[ctx.guild.id].start_audio_player()
        self.voice_states[ctx.guild.id].voice_channel = ctx.author.voice.channel
        await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_mute=False, self_deaf=True)
        node = wavelink.Pool.get_node()
        player = node.get_player(ctx.guild.id)
        player.autoplay = wavelink.AutoPlayMode.partial

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

        except Exception as e:
            error_message = 'An error occurred trying to add the song to the queue:'
            error_message += f'\n```\n{e}\n```'
            await ctx.send(error_message)
            raise e

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

        if state.voice_channel is None or player is None:
            if ctx.author.voice:
                await self.voice_connect(ctx)
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
            await self.player_disconnect(ctx.guild)

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
    async def ensure_music_channel(self, ctx):
        await self.check_node_and_voice(ctx)


async def setup(bot):
    await bot.add_cog(Music(bot))
