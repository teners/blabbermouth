import enum
import json

import attr


class FeedSortType(enum.Enum):
    HOT = "hot"
    NEW = "new"
    BEST = "best"
    TOP = "top"


@attr.s(slots=True, frozen=True)
class RedditBrowser:
    http_session = attr.ib()
    reddit_url = attr.ib()
    request_headers = attr.ib()

    @classmethod
    def build(cls, http_session, reddit_url, user_agent):
        return cls(
            http_session=http_session, reddit_url=reddit_url, request_headers={"User-Agent": user_agent}
        )

    async def lookup_top_posts(self, subreddit, sort_type, limit):
        url = "{}/r/{}/{}.json?limit={}".format(self.reddit_url, subreddit, sort_type.value, limit)

        async with self.http_session.get(url, headers=self.request_headers) as response:
            response_text = await response.text()
            if response.status != 200:
                raise Exception("Got unwanted response {}: {}".format(response.status, response_text))

        response = json.loads(response_text)

        for post in reversed(response["data"]["children"]):
            yield self._reddit_url + post["data"]["permalink"]
