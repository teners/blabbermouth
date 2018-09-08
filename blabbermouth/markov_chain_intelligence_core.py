import contextlib
import enum
import functools
import random

import attr
import markovify

from intelligence_core import IntelligenceCore
from knowledge_base import KnowledgeBase
from util.lifespan import Lifespan
from util.log import logged


async def _strip_dots(iterable):
    async for entry in iterable:
        if entry.endswith("."):
            yield entry[:-1]
        yield entry


@logged
@attr.s(slots=True)
class CachedMarkovText:
    event_loop = attr.ib()
    worker = attr.ib()
    knowledge_source = attr.ib()
    make_sentence_attempts = attr.ib()
    text_lifespan = attr.ib(converter=Lifespan)
    text = attr.ib(factory=lambda: markovify.Text("."))
    sentence_is_building = attr.ib(default=False)

    def __attrs_post_init__(self):
        self._schedule_new_text()

    async def make_sentence(self):
        if not self.text_lifespan:
            self._schedule_new_text()

        if self.sentence_is_building:
            self._log.info("Sentence is building")
            return None

        sentence = None
        with self._sentence_building_session():
            sentence = await self._build_sentence()
            if sentence is None:
                self._log.error("Failed to produce sentence")

        return sentence

    def _schedule_new_text(self):
        self.event_loop.create_task(self._build_text())
        self.text_lifespan.reset()

    async def _build_text(self):
        knowledge = ". ".join([sentence async for sentence in _strip_dots(self.knowledge_source())])
        self.text = await self.event_loop.run_in_executor(self.worker, lambda: markovify.Text(knowledge))
        self._log.info("Successfully built new text")

    @contextlib.contextmanager
    def _sentence_building_session(self):
        self.sentence_is_building = True
        try:
            yield
        except Exception as ex:
            self._log.error("[CachedMarkovText] Failed to build sentence: {}".format(ex))
        finally:
            self.sentence_is_building = False

    async def _build_sentence(self):
        text = self.text
        make_sentence_attempts = self.make_sentence_attempts
        return await self.event_loop.run_in_executor(
            self.worker, lambda: text.make_sentence(tries=make_sentence_attempts)
        )


@logged
@attr.s(slots=True)
class MarkovChainIntelligenceCore(IntelligenceCore):
    class Strategy(enum.Enum):
        BY_CURRENT_CHAT = enum.auto()
        BY_CURRENT_USER = enum.auto()
        BY_FULL_KNOWLEDGE = enum.auto()

    event_loop = attr.ib()
    worker = attr.ib()
    chat_id = attr.ib()
    knowledge_base = attr.ib(validator=attr.validators.instance_of(KnowledgeBase))
    knowledge_lifespan = attr.ib()
    make_sentence_attempts = attr.ib()
    answer_placeholder = attr.ib()
    text_constructor = attr.ib(default=None)
    markov_texts = attr.ib(factory=dict)

    def __attrs_post_init__(self):
        self.text_constructor = functools.partial(
            CachedMarkovText,
            event_loop=self.event_loop,
            worker=self.worker,
            make_sentence_attempts=self.make_sentence_attempts,
            text_lifespan=self.knowledge_lifespan,
        )
        self.markov_texts[self.Strategy.BY_CURRENT_CHAT] = self.text_constructor(
            knowledge_source=functools.partial(self.knowledge_base.select_by_chat, self.chat_id)
        )
        self.markov_texts[self.Strategy.BY_FULL_KNOWLEDGE] = self.text_constructor(
            knowledge_source=self.knowledge_base.select_by_full_knowledge
        )

    async def conceive(self):
        return await self._form_message(
            strategies=[self.Strategy.BY_CURRENT_CHAT, self.Strategy.BY_FULL_KNOWLEDGE]
        )

    async def respond(self, user, message):
        return await self._form_message(
            strategies=[
                self.Strategy.BY_CURRENT_CHAT,
                self.Strategy.BY_CURRENT_USER,
                self.Strategy.BY_FULL_KNOWLEDGE,
            ],
            placeholder=self.answer_placeholder,
            user=user,
        )

    async def _form_message(self, strategies, placeholder=None, user=None):
        strategy = random.choice(strategies)
        if strategy == self.Strategy.BY_CURRENT_USER:
            text_key = (strategy, user)
            if text_key not in self.markov_texts:
                self.markov_texts[text_key] = self.text_constructor(
                    knowledge_source=functools.partial(self.knowledge_base.select_by_user, user)
                )
        else:
            text_key = strategy

        self._log.info("Using text for {}".format(text_key))

        sentence = await self.markov_texts[text_key].make_sentence()
        return sentence if sentence is not None else placeholder
