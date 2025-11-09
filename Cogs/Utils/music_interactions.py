import discord
import wavelink


class VolumeButtons(discord.ui.View):

    def __init__(self, player, state):
        super().__init__(timeout=None)
        self.player = player
        self.state = state

    @discord.ui.button(label='10', style=discord.ButtonStyle.grey)
    async def volume_10(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(10)
        self.state.saved_volume = 10
        await interaction.message.delete()

    @discord.ui.button(label='20', style=discord.ButtonStyle.grey)
    async def volume_20(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(20)
        self.state.saved_volume = 20
        await interaction.message.delete()

    @discord.ui.button(label='30', style=discord.ButtonStyle.grey)
    async def volume_30(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(30)
        self.state.saved_volume = 30
        await interaction.message.delete()

    @discord.ui.button(label='40', style=discord.ButtonStyle.grey)
    async def volume_40(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(40)
        self.state.saved_volume = 40
        await interaction.message.delete()

    @discord.ui.button(label='50', style=discord.ButtonStyle.grey)
    async def volume_50(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(50)
        self.state.saved_volume = 50
        await interaction.message.delete()

    @discord.ui.button(label='60', style=discord.ButtonStyle.grey)
    async def volume_60(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(60)
        self.state.saved_volume = 60
        await interaction.message.delete()

    @discord.ui.button(label='70', style=discord.ButtonStyle.grey)
    async def volume_70(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(70)
        self.state.saved_volume = 70
        await interaction.message.delete()

    @discord.ui.button(label='80', style=discord.ButtonStyle.grey)
    async def volume_80(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(80)
        self.state.saved_volume = 80
        await interaction.message.delete()

    @discord.ui.button(label='90', style=discord.ButtonStyle.grey)
    async def volume_90(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(90)
        self.state.saved_volume = 90
        await interaction.message.delete()

    @discord.ui.button(label='100', style=discord.ButtonStyle.grey)
    async def volume_100(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(100)
        self.state.saved_volume = 100
        await interaction.message.delete()


class MusicButtonsFirstRow(discord.ui.ActionRow):

    def __init__(self, player, state, parent_view):
        super().__init__()
        self.player = player
        self.state = state
        self.parent_view = parent_view

    @discord.ui.button(label='Pause', emoji='⏸️', style=discord.ButtonStyle.grey)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.paused:
            await self.player.pause(False)
            button.style=discord.ButtonStyle.grey
            button.label = 'Pause'
            button.emoji = '⏸️'
            await interaction.response.edit_message(view=self.parent_view)
        else:
            await self.player.pause(True)
            button.style=discord.ButtonStyle.green
            button.label = 'Play'
            button.emoji = '▶️'
            await interaction.response.edit_message(view=self.parent_view)

    @discord.ui.button(label='Skip', emoji='⏭️', style=discord.ButtonStyle.blurple)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.stop()
        await interaction.response.edit_message(view=self.parent_view)

    @discord.ui.button(label='Set volume', emoji='🔊', style=discord.ButtonStyle.green)
    async def volume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send('Pick volume', view=VolumeButtons(self.player, self.state))
        await interaction.response.edit_message(view=self.parent_view)

    @discord.ui.button(label='Disconnect', emoji='⏹️', style=discord.ButtonStyle.red)
    async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.state.music.player_disconnect(interaction.guild)


class MusicButtonsSecondRow(discord.ui.ActionRow):

    def __init__(self, player, state, parent_view):
        super().__init__()
        self.player = player
        self.state = state
        self.parent_view = parent_view

    @discord.ui.button(label='Queue', emoji='🔢', style=discord.ButtonStyle.blurple)
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        queue_modal = MusicQueueModal(self.player)
        await queue_modal.create_queue()

        await interaction.response.send_modal(queue_modal)

    @discord.ui.button(label='Search', emoji='🔍', style=discord.ButtonStyle.blurple)
    async def search_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        query_modal = MusicQueryModal(self.player)
        await interaction.response.send_modal(query_modal)


class MusicQueueModal(discord.ui.Modal):

    def __init__(self, player):
        super().__init__(title='BearBot Queue', timeout=60)
        self.player = player

    async def create_queue(self):
        if len(self.player.queue) == 0:
            popup = discord.ui.TextDisplay('There are currently no items in the queue')
        else:
            queue_text = ''
            for song in self.player.queue:
                queue_text += song.title + '\n'

            popup = discord.ui.TextDisplay(queue_text)

        self.add_item(popup)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()


class MusicQueryModal(discord.ui.Modal):

    def __init__(self, player):
        super().__init__(title='BearBot Search', timeout=60)
        self.player = player

    query = discord.ui.TextInput(label='Search YouTube for')

    async def on_submit(self, interaction: discord.Interaction):
        search_layout = MusicSearchConfirm(self.query, self.player)
        await interaction.response.send_message(view=search_layout, ephemeral=True, delete_after=30)


class MusicSearchConfirm(discord.ui.View):

    def __init__(self, query, player):
        super().__init__()
        self.query = query
        self.player = player

    @discord.ui.button(label='View search results', style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        search_modal = MusicSearchModal(self.query.value, self.player)
        await search_modal.search()
        await interaction.response.send_modal(search_modal)


class MusicSearchModal(discord.ui.Modal):

    def __init__(self, query, player):
        super().__init__(title='Search Results', timeout=60)
        self.query = query
        self.player = player

        self.found = False
        self.pick_result = None
        self.options = {}

    async def search(self):
        tracks = await wavelink.Playable.search(self.query, source=wavelink.TrackSource.YouTube)

        if not tracks:
            result = discord.ui.TextDisplay('Could not find any songs with that query')
        else:
            self.found = True
            self.pick_result = discord.ui.Select()
            for i in range(0, min(len(tracks), 25)):
                if tracks[i].title not in self.options:
                    self.options[tracks[i].title] = tracks[i]
                    self.pick_result.add_option(label=tracks[i].title)

            result = discord.ui.Label(text='Search Results', component=self.pick_result)

        self.add_item(result)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.found:
            await interaction.response.defer()
        else:
            track = self.options[self.pick_result.values[0]]
            await self.player.queue.put_wait(track)
            await interaction.response.send_message(f'Enqueued song {self.pick_result.values[0]}', delete_after=5)


class MusicView(discord.ui.LayoutView):

    def __init__(self, player, state, embed, timeout=None):
        super().__init__(timeout=timeout)
        self.player = player
        self.state = state
        self.embed = embed

    async def create_music_container(self, disconnect=False):
        title = '### BearBot Music Player'
        colour = discord.Colour.blurple()
        if disconnect:
            title += ' (disconnected)'
            colour = discord.Colour.greyple()

        container = discord.ui.Container(
            discord.ui.TextDisplay(title),
            discord.ui.TextDisplay(self.embed.description),
            discord.ui.MediaGallery(discord.MediaGalleryItem(self.embed.image.url)),
            accent_colour=colour
        )

        return container

    async def create_music_msg(self):
        container = await self.create_music_container()

        self.add_item(container)
        self.add_item(MusicButtonsFirstRow(self.player, self.state, self))
        self.add_item(MusicButtonsSecondRow(self.player, self.state, self))

    async def disconnect_msg(self):
        container = await self.create_music_container(True)

        self.clear_items()
        self.add_item(container)
