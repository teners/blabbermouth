import enum
import json

import aiohttp


class FeedSortType(enum.Enum):
    HOT = "hot"
    NEW = "new"
    BEST = "best"
    TOP = "top"


class RedditBrowser:
    def __init__(self, reddit_url, user_agent):
        self._reddit_url = reddit_url
        self._client_headers = {"User-Agent": user_agent}

    async def lookup_top_posts(self, subreddit, sort_type, limit):
        print("[RedditBrowser] Looking up top posts")

        url = "{}/r/{}/{}.json?limit={}".format(self._reddit_url, subreddit, sort_type.value, limit)

        async with aiohttp.ClientSession(headers=self._client_headers) as session:
            async with session.get(url) as response:
                response_text = await response.text()
                if response.status != 200:
                    raise Exception("Got unwanted response {}: {}".format(response.status, response_text))

        response = json.loads(response_text)

        for post in reversed(response["data"]["children"]):
            yield post["data"]["permalink"]
