import praw

reddit = praw.Reddit(client_id='reddit_client_id',
                     client_secret='reddit_client_secret',
                     user_agent='reddit_user_agent')


async def newUserPost(sr, redditName):
    u = reddit.redditor(redditName)

    for submission in u.submissions.new(limit=10):
        if submission.subreddit == sr:
            return [submission.url, submission.selftext]

async def hotPost(sr):
    submission = next(x for x in reddit.subreddit(sr).hot() if not x.stickied)
    return [submission.url, submission.selftext, submission.title]
