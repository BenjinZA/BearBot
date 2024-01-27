import praw
import json

with open('bot_info.json', 'r') as file:
    bot_info = json.load(file)

reddit = praw.Reddit(client_id=bot_info['reddit_id'],
                     client_secret=bot_info['reddit_secret'],
                     user_agent=bot_info['reddit_agent'])


async def newUserPost(sr, redditName):
    u = reddit.redditor(redditName)

    for submission in u.submissions.new(limit=10):
        if submission.subreddit == sr:
            return [submission.url, submission.selftext]

async def hotPost(sr):
    submission = next(x for x in reddit.subreddit(sr).hot() if not x.stickied)
    return [submission.url, submission.selftext, submission.title]
