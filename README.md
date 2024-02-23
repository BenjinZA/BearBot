# BearBot
GitHub repo of custom Discord bot.

Requires Python version 3.10 or later.

Python dependencies:
- [discord.py[voice]](https://github.com/Rapptz/discord.py)
- [wavelink](https://github.com/PythonistaGuild/Wavelink)
- [asyncpraw](https://github.com/praw-dev/asyncpraw)
- [tabulate](https://github.com/astanin/python-tabulate)
- [Pillow](https://github.com/python-pillow/Pillow)
- [aiohttp](https://github.com/aio-libs/aiohttp)
- [wordcloud](https://github.com/amueller/word_cloud)
- [aiosqlite](https://github.com/omnilib/aiosqlite)

Requires a [Lavalink](https://github.com/lavalink-devs/Lavalink) server for audio to work.
When setting dev to false (see below), code will attempt to start Lavalink by itself.

If you wish to run this, you will need the following:
- Discord bot token
- Reddit API credentials
- Create `bot_info.json` file with the following:
  ```
  'dev'               -> True/False for development
  'token'             -> Discord bot token string
  'lavalink'          -> location of Lavalink jar
  'lavalink_ip'       -> IP of Lavalink server
  'lavalink_password' -> password of Lavalink server
  'reddit_id'         -> client_id of reddit account
  'reddit_secret'     -> client_secret of reddit account
  'reddit_agent'      -> user_agent of reddit account
   ```
This bot was coded as a learning project. As such, some of the code is very old and messy.