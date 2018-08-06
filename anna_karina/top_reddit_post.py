import enum
import json
import random

import aiohttp

import telepot

import timer


class SortType(enum.Enum):
    HOT = 'hot'
    NEW = 'new'
    BEST = 'best'
    TOP = 'top'


class TopRedditPost(telepot.aio.helper.ChatHandler):
    TOP_POST_QUERY = 'top_reddit_post_toggle'

    REDDIT_URL = 'https://reddit.com'

    TOP_POST_COMMENTS = [
        'Классный пост',
        'Даня пидор',
        'Мальчики, классный пост с реддита',
        'Сижу на реддите весь день',
        'Обожаю реддит',
        'Простите',
        'Лол',
        'Азаза',
        'Миленько',
        'Приветики',
        'Вот бы в 2К18 так делать',
        'ISHYGDDT',
        'Эх',
        'Привет пидоры',
        'Хихик',
        'Оооо',
        'Привет педики UwU',
    ]

    SUBREDDITS_OF_INTEREST = [
        'analog',
        'amateurroomporn',
        'battlestations',
        'tifu',
        'shittylifeprotips',
        'linuxmemes',
        'unixporn',
        'linusrants',
        'machineporn',
        'outoftheloop',
        'python',
        'gunporn',
        'ooer',
        'prequelmemes',
        'dankmemes',
        'worldnews',
        'subredditsimulator',
        'futurology',
        'iama',
        'cooking',
    ]

    def __init__(self, tp, sort_type, period, user_agent,
                 personal_query_detector, **kwargs):
        super(TopRedditPost, self).__init__(tp, **kwargs)

        self._sort_type = sort_type
        self._period = period
        self._personal_query_detector = personal_query_detector
        self._enabled = False
        self._timer = None
        self._user_agent = user_agent

        print('[TopRedditPost] Created {}'.format(id(self)))

    async def on_chat_message(self, message):
        personal_query = self._personal_query_detector(message)
        if personal_query is None:
            return

        if personal_query != self.TOP_POST_QUERY:
            print('[TopRedditPost] Not my query')
            return

        print('[TopRedditPost] Got query: {}'.format(personal_query))

        self._enabled = not self._enabled
        if self._enabled:
            await self._start_listening()
        else:
            await self._stop_listening()

    def on_close(self, _):
        self._stop_listening()

    def on__idle(self, _):
        print('[TopRedditPost] Ignoring on__idle')

    async def _start_listening(self):
        print('[TopRedditPost] _start_listening()')

        self._timer = timer.Timer(self._period, self._lookup_top_post)

    async def _stop_listening(self):
        print('[TopRedditPost] _stop_listening()')

        self._timer.cancel()
        self._timer = None

    async def _lookup_top_post(self):
        print('[TopRedditPost] Looking up top post')

        subreddit = random.choice(self.SUBREDDITS_OF_INTEREST)
        url = '{}/r/{}/{}.json?limit=1'.format(self.REDDIT_URL, subreddit,
                                               self._sort_type.value)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response_text = await response.text()
                if response.status != 200:
                    raise Exception('Got unwanted response {}: {}',
                                    response.status, response_text)

        response = json.loads(response_text)
        top_post = response['data']['children'][-1]['data']['permalink']

        print('[TopRedditPost] Top post of choice is {}'.format(top_post))

        await self.sender.sendMessage(self._format_top_post_message(top_post))

    def _format_top_post_message(self, top_post):
        comment = random.choice(self.TOP_POST_COMMENTS)
        top_post = self.REDDIT_URL + top_post
        return '{}\n{}'.format(comment, top_post)
