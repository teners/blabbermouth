import enum
import json

import aiohttp
import attr


class FeedSortType(enum.Enum):
    HOT = "hot"
    NEW = "new"
    BEST = "best"
    TOP = "top"


@attr.s(slots=True, frozen=True)
class RedditBrowser:
    reddit_url = attr.ib()
    request_headers = attr.ib()

    @classmethod
    def build(cls, reddit_url, user_agent):
        return cls(reddit_url=reddit_url, request_headers={"User-Agent": user_agent})

    async def lookup_top_posts(self, subreddit, sort_type, limit):
        url = "{}/r/{}/{}.json?limit={}".format(self.reddit_url, subreddit, sort_type.value, limit)

        async with aiohttp.ClientSession(headers=self.request_headers) as session:
            async with session.get(url) as response:
                response_text = await response.text()
                if response.status != 200:
                    raise Exception("Got unwanted response {}: {}".format(response.status, response_text))

        response = json.loads(response_text)

        for post in reversed(response["data"]["children"]):
            yield self._reddit_url + post["data"]["permalink"]
