import os
import discord
import pickle
from discord.ext import commands


class SelectDawnChannel(discord.ui.ChannelSelect):

    def __init__(self, guild_configs, guild_categories):
        super().__init__(
            channel_types=[discord.ChannelType.voice],
            placeholder='Select the channel to move users to at dawn'
        )
        self.guild_configs = guild_configs
        self.guild_categories = guild_categories

    async def callback(self, interaction: discord.Interaction):
        dawn_channel_id = interaction.data['values'][0]
        dawn_channel_name = interaction.data['resolved']['channels'][dawn_channel_id]['name']

        self.guild_configs[interaction.guild_id] = {'dawn': int(dawn_channel_id)}

        await interaction.response.edit_message(content=f'Dawn channel set as {dawn_channel_name}',
                                                view=SelectNightGroupView(self.guild_configs, self.guild_categories)
                                                )


class SelectDawnChannelView(discord.ui.View):

    def __init__(self, guild_configs, guild_categories):
        super().__init__()
        self.guild_configs = guild_configs
        self.add_item(SelectDawnChannel(self.guild_configs, guild_categories))


class SelectNightGroup(discord.ui.Select):

    def __init__(self, guild_configs, guild_categories):
        options = []

        for category in guild_categories:
            options.append(discord.SelectOption(label=category.name, value=f'{category.id},{category.name}'))

        super().__init__(placeholder="Select an option", max_values=1, min_values=1, options=options)
        self.guild_configs = guild_configs

    async def callback(self, interaction: discord.Interaction):
        night_category_data = interaction.data['values'][0]
        night_category_id = int(night_category_data.split(',')[0])
        night_category_name = night_category_data.split(',')[1]

        self.guild_configs[interaction.guild_id]['night'] = night_category_id

        pickle.dump(self.guild_configs, open('Cogs/Utils/botc/guild_config.txt', 'wb'))

        await interaction.response.edit_message(content=interaction.message.content + f'\nNight category set as {night_category_name}',
                                                view=None
                                                )


class SelectNightGroupView(discord.ui.View):

    def __init__(self, guild_configs, guild_categories):
        super().__init__()
        self.guild_configs = guild_configs
        self.add_item(SelectNightGroup(self.guild_configs, guild_categories))


class BloodOnTheClocktower(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.night_players = {}
        if os.path.isfile('Cogs/Utils/botc/guild_config.txt'):
            self.guild_configs = pickle.load(open('Cogs/Utils/botc/guild_config.txt', 'rb'))
        else:
            self.guild_configs = {}



    @commands.hybrid_command(brief='Setup command to select channel and group to move users back and forth')
    async def botc_setup(self, ctx: commands.Context) -> None:
        await ctx.send(view=SelectDawnChannelView(self.guild_configs, ctx.guild.categories))

    @commands.hybrid_command(brief='Send players to sleep')
    async def night(self, ctx: commands.Context) -> None:
        if ctx.guild.id not in self.guild_configs:
            await ctx.send('No config for this server, use command `botc_setup`')
            return

        dawn_channel = await ctx.guild.fetch_channel(self.guild_configs[ctx.guild.id]['dawn'])
        night_category = discord.utils.get(ctx.guild.categories, id=self.guild_configs[ctx.guild.id]['night'])

        self.night_players[ctx.guild.id] = dawn_channel.members

        for i in range(0, len(self.night_players[ctx.guild.id])):
            await self.night_players[ctx.guild.id][i].move_to(night_category.channels[i])

    @commands.hybrid_command(brief='Wake players from sleep')
    async def dawn(self, ctx: commands.Context) -> None:
        if ctx.guild.id not in self.guild_configs:
            await ctx.send('No config for this server, use command `botc_setup`')
            return

        dawn_channel = (ctx.guild.get_channel(self.guild_configs[ctx.guild.id]['dawn']) or await ctx.guild.fetch_channel(self.guild_configs[ctx.guild.id]['dawn']))

        for member in self.night_players[ctx.guild.id]:
            await member.move_to(dawn_channel)

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event):
        if event.guild.id in self.guild_configs:
            for member in event.guild.members:
                for role in member.roles:
                    if role.name == 'Player':
                        await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_scheduled_event_user_add(self, event, user):
        if event.guild.id in self.guild_configs:
            for role in event.guild.roles:
                if role.name == 'Player':
                    member = event.guild.get_member(user.id)
                    await member.add_roles(role)

    @commands.Cog.listener()
    async def on_scheduled_event_user_remove(self, event, user):
        if event.guild.id in self.guild_configs:
            for role in event.guild.roles:
                if role.name == 'Player':
                    member = event.guild.get_member(user.id)
                    await member.remove_roles(role)


async def setup(bot):
    await bot.add_cog(BloodOnTheClocktower(bot))
