import argparse
import asyncio
import datetime

import telepot

from telepot.aio.loop import MessageLoop
from telepot.aio.delegate import (per_chat_id, create_open, pave_event_space,
                                  include_callback_query_chat_id)

import deaf_detector
import query_detector
import top_reddit_post

USER_AGENT = 'linux:anna-karina-bot:1.0 (by /u/subsinthe)'
USERNAME = 'anna_karina_bot'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', required=True)
    parser.add_argument('--proxy')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.proxy:
        telepot.aio.api.set_proxy(args.proxy)

    bot = telepot.aio.DelegatorBot(args.token, [
        pave_event_space()(
            per_chat_id(),
            create_open,
            top_reddit_post.TopRedditPost,
            sort_type=top_reddit_post.SortType.HOT,
            period=datetime.timedelta(hours=4),
            user_agent=USER_AGENT,
            personal_query_detector=query_detector.personal_query_detector(
                USERNAME),
            timeout=10),
        pave_event_space()(
            per_chat_id(), create_open, deaf_detector.DeafDetector, timeout=10)
    ])

    loop = asyncio.get_event_loop()
    loop.create_task(MessageLoop(bot).run_forever())

    loop.run_forever()


if __name__ == '__main__':
    main()
