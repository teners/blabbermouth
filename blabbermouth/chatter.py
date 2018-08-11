import abc
import enum
import random
import time

import attr
import pymongo
import markovify
import telepot


class KnowledgeBase(abc.ABC):
    @abc.abstractmethod
    def record(self, chat_id, user, text):
        pass

    @abc.abstractmethod
    def produce_selection_by_chat(self, chat_id):
        pass

    @abc.abstractmethod
    def produce_selection_by_user(self, user):
        pass

    @abc.abstractmethod
    def produce_selection_by_full_knowledge(self):
        pass


class MongoKnowledgeBase(KnowledgeBase):
    def __init__(self, host, port, db_name, db_collection):
        self._client = pymongo.MongoClient(host, port)
        self._collection = self._client[db_name][db_collection]

    def record(self, chat_id, user, text):
        doc = {'chat_id': chat_id, 'user': user, 'text': text}
        self._collection.insert_one(doc)

    def produce_selection_by_chat(self, chat_id):
        for item in self._collection.find({'chat_id': chat_id}):
            yield item['text'].replace('\n', '. ')

    def produce_selection_by_user(self, user):
        for item in self._collection.find({'user': user}):
            yield item['text'].replace('\n', '. ')

    def produce_selection_by_full_knowledge(self):
        for item in self._collection.find():
            yield item['text'].replace('\n', '. ')


class IntellegenceCore(abc.ABC):
    @abc.abstractmethod
    def answer(self, chat_id, user, text):
        pass


@attr.s
class Timeout:
    timeout = attr.ib()
    stamp = attr.ib(factory=time.time)

    def is_expired(self):
        return time.time() - self.stamp >= self.timeout.seconds

    def reset(self):
        self.stamp = time.time()


@attr.s
class CachedMarkovText:
    knowledge_source = attr.ib()
    knowledge_timeout = attr.ib(converter=Timeout)
    make_sentence_attempts = attr.ib(int)
    text = attr.ib(default=None)

    def make_sentence(self, **source_args):
        if self.text is None or self.knowledge_timeout.is_expired():
            knowledge = '. '.join([sentence for sentence in self.knowledge_source(**source_args)])
            self.text = markovify.Text(knowledge)
            self.knowledge_timeout.reset()

        sentence = self.text.make_sentence(tries=self.make_sentence_attempts)

        if sentence is None:
            print('[CachedMarkovText]: Failed to build markov text')

        return sentence


class MarkovChainIntellegenceCore(IntellegenceCore):
    class Strategy(enum.Enum):
        BY_CURRENT_CHAT = enum.auto()
        BY_CURRENT_USER = enum.auto()
        BY_FULL_KNOWLEDGE = enum.auto()

    def __init__(self, knowledge_base, knowledge_lifespan, make_sentence_attempts, answer_placeholder):
        if not isinstance(knowledge_base, KnowledgeBase):
            raise TypeError('knowledge_base must be KnowledgeBase')

        self._answer_placeholder = answer_placeholder
        self._strategies = list(self.Strategy)

        self._markov_texts_by_strategy = {
            p[0]: CachedMarkovText(
                knowledge_source=p[1],
                knowledge_timeout=knowledge_lifespan,
                make_sentence_attempts=make_sentence_attempts,
            )
            for p in [
                (self.Strategy.BY_CURRENT_CHAT,
                 lambda **kwargs: knowledge_base.produce_selection_by_chat(kwargs['chat_id'])),
                (self.Strategy.BY_CURRENT_USER,
                 lambda **kwargs: knowledge_base.produce_selection_by_user(kwargs['user'])),
                (self.Strategy.BY_FULL_KNOWLEDGE,
                 lambda **kwargs: knowledge_base.produce_selection_by_full_knowledge()),
            ]
        }

    def answer(self, chat_id, user, text):
        strategy = random.choice(self._strategies)

        print('[MarkovChainIntellegenceCore] Using {} strategy'.format(strategy))

        sentence = self._markov_texts_by_strategy[strategy].make_sentence(
            chat_id=chat_id, user=user, text=text)
        return sentence if sentence is not None else self._answer_placeholder


class LearningEngine(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, knowledge_base, bot_name, **kwargs):
        if not isinstance(knowledge_base, KnowledgeBase):
            raise TypeError('knowledge_base must be KnowledgeBase')

        super(LearningEngine, self).__init__(*args, **kwargs)

        self._knowledge_base = knowledge_base
        self._bot_name = bot_name
        self._self_reference = '@{}'.format(bot_name)

        print('[LearningEngine] Created {}'.format(id(self)))

    async def on_chat_message(self, message):
        text = message.get('text')
        if text is None:
            return

        if self._is_talking_to_me(text):
            return

        user = message['from']['username']
        if user == self._bot_name:
            return

        chat_id = message['chat']['id']

        self._knowledge_base.record(chat_id=chat_id, user=user, text=text)

    def on__idle(self, _):
        print('[LearningEngine] Ignoring on__idle')

    def _is_talking_to_me(self, text):
        return self._self_reference in text


class AnswerEngine(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, intelligence_core, bot_name, **kwargs):
        if not isinstance(intelligence_core, IntellegenceCore):
            raise TypeError('intelligence_core must be IntellegenceCore')

        super(AnswerEngine, self).__init__(*args, **kwargs)

        self._intelligence_core = intelligence_core
        self._self_reference = '@{}'.format(bot_name)

        print('[AnswerEngine] Created {}'.format(id(self)))

    async def on_chat_message(self, message):
        text = message.get('text')
        if text is None:
            return

        if not self._is_talking_to_me(text):
            return

        chat_id = message['chat']['id']
        user = message['from']['username']

        print('[AnswerEngine] User {} in chat {} is talking to me'.format(user, chat_id))

        answer = self._intelligence_core.answer(chat_id=chat_id, user=user, text=text)
        if answer is None:
            print('[AnswerEngine] Got "None" answer from intellegence core')
            return

        await self.sender.sendMessage(answer)

    def on__idle(self, _):
        print('[AnswerEngine] Ignoring on__idle')

    def _is_talking_to_me(self, text):
        return self._self_reference in text
