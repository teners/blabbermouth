import contextlib
import enum
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
    text = attr.ib(default=None)
    sentence_is_building = attr.ib(default=False)

    async def make_sentence(self, knowledge_dependency):
        if self.text is None:
            self.text = markovify.Text(".")
            self._schedule_new_text(knowledge_dependency)

        if not self.text_lifespan:
            self._schedule_new_text(knowledge_dependency)

        if self.sentence_is_building:
            self.__log.info("Sentence is building")
            return None

        sentence = None
        with self._sentence_building_session():
            sentence = await self._build_sentence()
            if sentence is None:
                self.__log.error("Failed to produce sentence")

        return sentence

    def _schedule_new_text(self, knowledge_dependency):
        self.event_loop.create_task(self._build_text(knowledge_dependency))
        self.text_lifespan.reset()

    async def _build_text(self, knowledge_dependency):
        knowledge = ". ".join(
            [sentence async for sentence in _strip_dots(self.knowledge_source(knowledge_dependency))]
        )
        self.text = await self.event_loop.run_in_executor(self.worker, lambda: markovify.Text(knowledge))
        self.__log.info("Successfully built new text")

    @contextlib.contextmanager
    def _sentence_building_session(self):
        self.sentence_is_building = True
        try:
            yield
        except Exception as ex:
            self.__log.error("[CachedMarkovText] Failed to build sentence: {}".format(ex))
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
    markov_texts_by_strategy = attr.ib(dict)

    def __attrs_post_init__(self):
        chat_id = self.chat_id

        self.markov_texts_by_strategy = {
            p[0]: CachedMarkovText(
                event_loop=self.event_loop,
                worker=self.worker,
                knowledge_source=p[1],
                make_sentence_attempts=self.make_sentence_attempts,
                text_lifespan=self.knowledge_lifespan,
            )
            for p in [
                (self.Strategy.BY_CURRENT_CHAT, lambda _: self.knowledge_base.select_by_chat(chat_id)),
                (
                    self.Strategy.BY_CURRENT_USER,
                    lambda dependency: self.knowledge_base.select_by_user(dependency["user"]),
                ),
                (self.Strategy.BY_FULL_KNOWLEDGE, lambda _: self.knowledge_base.select_by_full_knowledge()),
            ]
        }

    async def conceive(self):
        return await self._form_message(
            strategies=[self.Strategy.BY_CURRENT_CHAT, self.Strategy.BY_FULL_KNOWLEDGE],
            dependency={},
            placeholder=None,
        )

    async def respond(self, user, message):
        return await self._form_message(
            strategies=[
                self.Strategy.BY_CURRENT_CHAT,
                self.Strategy.BY_CURRENT_USER,
                self.Strategy.BY_FULL_KNOWLEDGE,
            ],
            dependency={"user": user},
            placeholder=self.answer_placeholder,
        )

    async def _form_message(self, strategies, dependency, placeholder):
        strategy = random.choice(strategies)

        self.__log.info("Using {} strategy".format(strategy))

        sentence = await self.markov_texts_by_strategy[strategy].make_sentence(dependency)
        return sentence if sentence is not None else placeholder
