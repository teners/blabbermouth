import contextlib
import enum
import random

import attr
import markovify

from intelligence_core import IntelligenceCore
from knowledge_base import KnowledgeBase
from util.lifespan import Lifespan


async def _strip_dots(iterable):
    async for entry in iterable:
        if entry.endswith("."):
            yield entry[:-1]
        yield entry


@attr.s(slots=True)
class CachedMarkovText:
    make_async = attr.ib()
    knowledge_source = attr.ib()
    make_sentence_attempts = attr.ib()
    text_lifespan = attr.ib(converter=Lifespan)
    text = attr.ib(default=None)
    text_is_building = attr.ib(default=False)
    sentence_is_building = attr.ib(default=False)

    async def make_sentence(self, knowledge_dependency):
        if self.text is None and self.text_is_building:
            print("[CachedMarkovText] First text is currently building")
            return None

        if (self.text is None or not self.text_lifespan) and not self.text_is_building:
            with self._text_building_session():
                self.text = await self._build_text(knowledge_dependency)
                self.text_lifespan.reset()

        if self.sentence_is_building:
            print("[CachedMarkovText] Sentence is building")
            return None

        with self._sentence_building_session():
            sentence = await self._build_sentence()
        if sentence is None:
            print("[CachedMarkovText]: Failed to produce sentence")
        return sentence

    @contextlib.contextmanager
    def _text_building_session(self):
        print("[CachedMarkovText] Building new text")

        self.text_is_building = True
        try:
            yield
        except Exception as ex:
            print("[CachedMarkovText] Failed to build new text: {}".format(ex))
        else:
            print("[CachedMarkovText] Successfully built new text")
        finally:
            self.text_is_building = False

    async def _build_text(self, knowledge_dependency):
        knowledge = ". ".join(
            sentence async for sentence in _strip_dots(self.knowledge_source(knowledge_dependency))
        )
        return (await self.make_async(lambda: markovify.Text(knowledge))).result()

    @contextlib.contextmanager
    def _sentence_building_session(self):
        self.sentence_is_building = True
        try:
            yield
        except Exception as ex:
            print("[CachedMarkovText] Failed to build sentence: {}".format(ex))
        finally:
            self.sentence_is_building = False

    async def _build_sentence(self):
        text = self.text
        make_sentence_attempts = self.make_sentence_attempts
        return (await self.make_async(lambda: text.make_sentence(tries=make_sentence_attempts))).result()


@attr.s(slots=True)
class MarkovChainIntelligenceCore(IntelligenceCore):
    class Strategy(enum.Enum):
        BY_CURRENT_CHAT = enum.auto()
        BY_CURRENT_USER = enum.auto()
        BY_FULL_KNOWLEDGE = enum.auto()

    make_async = attr.ib()
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
                make_async=self.make_async,
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
            strategies=[self.Strategy.BY_CURRENT_CHAT, self.Strategy.BY_FULL_KNOWLEDGE], dependency={}
        )

    async def respond(self, user, message):
        return await self._form_message(
            strategies=[
                self.Strategy.BY_CURRENT_CHAT,
                self.Strategy.BY_CURRENT_USER,
                self.Strategy.BY_FULL_KNOWLEDGE,
            ],
            dependency={"user": user},
        )

    async def _form_message(self, strategies, dependency):
        strategy = random.choice(strategies)

        print("[MarkovChainIntelligenceCore] Using {} strategy".format(strategy))

        sentence = await self.markov_texts_by_strategy[strategy].make_sentence(dependency)
        return sentence if sentence is not None else self.answer_placeholder
