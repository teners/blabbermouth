import argparse
import asyncio
import datetime
import concurrent.futures

import telepot

from telepot.aio.loop import MessageLoop
from telepot.aio.delegate import per_chat_id, create_open, pave_event_space

import chatter_handler, chat_intelligence, deaf_detector, learning_handler
from aggregating_intelligence_core import AggregatingIntelligenceCore
from markov_chain_intelligence_core import MarkovChainIntelligenceCore
from mongo_knowledge_base import MongoKnowledgeBase
from reddit_browser import RedditBrowser
from reddit_chatter import RedditChatter
from speaking_intelligence_core import SpeakingIntelligenceCore
from util import config, log, query_detector


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--yandex-dev-api-key", required=True)
    parser.add_argument("--dev", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    config_env_overrides = {
        "is_prod": not args.dev,
        "token": args.token,
        "yandex_dev_api_key": args.yandex_dev_api_key,
    }
    conf = config.load_config("config", "env.yaml", config_env_overrides)

    log.setup_logging(conf)

    bot_name = conf["bot_name"]
    bot_token = conf["token"]
    user_agent = conf["core"]["user_agent"]
    telepot_http_timeout = conf["telepot"]["http_timeout"]

    telepot.aio.api.set_proxy(conf["core"]["proxy"])

    knowledge_base = MongoKnowledgeBase.build(
        host=conf["mongo_knowledge_base"]["db_host"],
        port=conf["mongo_knowledge_base"]["db_port"],
        db_name=conf["mongo_knowledge_base"]["db_name"],
        db_collection=conf["mongo_knowledge_base"]["db_collection"],
    )

    event_loop = asyncio.get_event_loop()
    markov_chain_worker = concurrent.futures.ThreadPoolExecutor(max_workers=5)

    def main_intelligence_core_constructor(chat_id):
        markov_chain_core = MarkovChainIntelligenceCore.build(
            event_loop=event_loop,
            worker=markov_chain_worker,
            chat_id=chat_id,
            knowledge_base=knowledge_base,
            knowledge_lifespan=datetime.timedelta(
                minutes=conf["markov_chain_intelligence_core"]["knowledge_lifespan_minutes"]
            ),
            make_sentence_attempts=conf["markov_chain_intelligence_core"]["make_sentence_attempts"],
        )
        return AggregatingIntelligenceCore(
            cores=[
                markov_chain_core,
                SpeakingIntelligenceCore(
                    text_core=markov_chain_core,
                    voice=conf["speaking_intelligence_core"]["voice"],
                    lang=conf["speaking_intelligence_core"]["lang"],
                    audio_format=conf["speaking_intelligence_core"]["audio_format"],
                    api_url=conf["speaking_intelligence_core"]["api_url"],
                    api_key=conf["yandex_dev_api_key"],
                ),
                RedditChatter(
                    top_post_comments=conf["reddit_chatter"]["top_post_comments"],
                    subreddits_of_interest=conf["reddit_chatter"]["subreddits_of_interest"],
                    reddit_browser=RedditBrowser.build(
                        reddit_url=conf["reddit_browser"]["reddit_url"], user_agent=user_agent
                    ),
                ),
            ]
        )

    intelligence_registry = chat_intelligence.IntelligenceRegistry(
        core_constructor=main_intelligence_core_constructor
    )

    bot = telepot.aio.DelegatorBot(
        bot_token,
        [
            pave_event_space()(
                per_chat_id(),
                create_open,
                deaf_detector.DeafDetectorHandler,
                event_loop=event_loop,
                timeout=telepot_http_timeout,
            ),
            pave_event_space()(
                per_chat_id(),
                create_open,
                chat_intelligence.ChatIntelligence,
                intelligence_registry=intelligence_registry,
                timeout=telepot_http_timeout,
            ),
            pave_event_space()(
                per_chat_id(),
                create_open,
                learning_handler.LearningHandler,
                knowledge_base=knowledge_base,
                self_reference_detector=query_detector.self_reference_detector(bot_name),
                bot_name=bot_name,
                event_loop=event_loop,
                timeout=telepot_http_timeout,
            ),
            pave_event_space()(
                per_chat_id(),
                create_open,
                chatter_handler.ChatterHandler,
                event_loop=event_loop,
                intelligence_registry=intelligence_registry,
                self_reference_detector=query_detector.self_reference_detector(bot_name),
                personal_query_detector=query_detector.personal_query_detector(bot_name),
                conceive_interval=datetime.timedelta(
                    hours=conf["chatter_handler"]["conceive_interval_hours"]
                ),
                answer_placeholder=conf["chatter_handler"]["answer_placeholder"],
                timeout=telepot_http_timeout,
            ),
        ],
    )

    event_loop.create_task(MessageLoop(bot).run_forever())
    event_loop.run_forever()


if __name__ == "__main__":
    main()
