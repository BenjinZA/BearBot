import asyncpraw
import json

with open('bot_info.json', 'r') as file:
    bot_info = json.load(file)

reddit = asyncpraw.Reddit(client_id=bot_info['reddit_id'],
                          client_secret=bot_info['reddit_secret'],
                          user_agent=bot_info['reddit_agent'])


async def newUserPost(sr, redditName):
    u = await reddit.redditor(redditName)

    async for submission in u.submissions.new(limit=10):
        if submission.subreddit == sr:
            return [submission.url, submission.selftext]


async def hotPost(sr):
    subreddit = await reddit.subreddit(sr)
    async for submission in subreddit.hot(limit=10):
        if not submission.stickied:
            return [submission.url, submission.selftext, submission.title]
