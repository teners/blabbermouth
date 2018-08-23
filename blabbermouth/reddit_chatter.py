import random

import attr
import autologging

from intelligence_core import IntelligenceCore
from reddit_browser import FeedSortType, RedditBrowser


@autologging.logged
@attr.s
class RedditChatter(IntelligenceCore):
    top_post_comments = attr.ib()
    subreddits_of_interest = attr.ib()
    reddit_browser = attr.ib(attr.validators.instance_of(RedditBrowser))
    sort_types = attr.ib(factory=lambda: list(FeedSortType))

    async def conceive(self):
        subreddit = random.choice(self.subreddits_of_interest)
        sort_type = random.choice(self.sort_types)

        top_post = None
        async for post in self.reddit_browser.lookup_top_posts(subreddit, sort_type, limit=1):
            top_post = post
            break
        else:
            self.__log.warning("Top post was not found")
            return

        self.__log.info("Top post of choice is {}".format(top_post))

        return self._format_top_post_message(top_post)

    async def respond(self, *_):
        return None

    def _format_top_post_message(self, top_post):
        comment = random.choice(self.top_post_comments)
        return "{}\n{}".format(comment, top_post)
