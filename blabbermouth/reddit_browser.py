import enum
import json

import aiohttp


class FeedSortType(enum.Enum):
    HOT = "hot"
    NEW = "new"
    BEST = "best"
    TOP = "top"


class RedditBrowser:
    REDDIT_URL = "https://reddit.com"

    async def lookup_top_posts(self, subreddit, sort_type, limit):
        print("[RedditBrowser] Looking up top posts")

        url = "{}/r/{}/{}.json?limit={}".format(self.REDDIT_URL, subreddit, sort_type.value, limit)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response_text = await response.text()
                if response.status != 200:
                    raise Exception("Got unwanted response {}: {}".format(response.status, response_text))

        response = json.loads(response_text)

        for post in reversed(response["data"]["children"]):
            yield post["data"]["permalink"]
