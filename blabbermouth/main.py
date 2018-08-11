import argparse
import asyncio
import datetime

import telepot

from telepot.aio.loop import MessageLoop
from telepot.aio.delegate import per_chat_id, create_open, pave_event_space

import chatter
import config
import deaf_detector
import query_detector
import top_reddit_post


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', required=True)
    parser.add_argument('--dev', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    config_env_overrides = {
        'is_prod': not args.dev,
        'token': args.token,
    }
    conf = config.load_config('config', 'env.yaml', config_env_overrides)

    telepot.aio.api.set_proxy(conf['core']['proxy'])

    knowledge_base = chatter.MongoKnowledgeBase(
        host=conf['mongo_knowledge_base']['db_host'],
        port=conf['mongo_knowledge_base']['db_port'],
        db_name=conf['mongo_knowledge_base']['db_name'],
        db_collection=conf['mongo_knowledge_base']['db_collection'],
    )
    intelligence_core = chatter.MarkovChainIntellegenceCore(
        knowledge_base=knowledge_base,
        knowledge_lifespan=datetime.timedelta(
            minutes=conf['markov_chain_intellegence_core']['knowledge_lifespan_minutes']),
        answer_placeholder=conf['markov_chain_intellegence_core']['answer_placeholder'],
        make_sentence_attempts=conf['markov_chain_intellegence_core']['make_sentence_attempts'],
    )

    bot_name = conf['bot_name']
    bot_token = conf['token']
    user_agent = conf['core']['user_agent']
    telepot_http_timeout = conf['telepot']['http_timeout']

    bot = telepot.aio.DelegatorBot(bot_token, [
        pave_event_space()(
            per_chat_id(),
            create_open,
            top_reddit_post.TopRedditPost,
            sort_type=top_reddit_post.SortType.HOT,
            period=datetime.timedelta(hours=conf['reddit_browser']['query_period_hours']),
            user_agent=user_agent,
            personal_query_detector=query_detector.personal_query_detector(bot_name),
            timeout=telepot_http_timeout),
        pave_event_space()(
            per_chat_id(), create_open, deaf_detector.DeafDetector, timeout=telepot_http_timeout),
        pave_event_space()(
            per_chat_id(),
            create_open,
            chatter.LearningEngine,
            knowledge_base=knowledge_base,
            bot_name=bot_name,
            timeout=telepot_http_timeout),
        pave_event_space()(
            per_chat_id(),
            create_open,
            chatter.AnswerEngine,
            intelligence_core=intelligence_core,
            bot_name=bot_name,
            timeout=telepot_http_timeout),
    ])

    loop = asyncio.get_event_loop()
    loop.create_task(MessageLoop(bot).run_forever())

    loop.run_forever()


if __name__ == '__main__':
    main()
