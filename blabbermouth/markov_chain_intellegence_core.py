import enum
import random

import attr
import markovify

from blabbermouth.intellegence_core import IntellegenceCore
from blabbermouth.knowledge_base import KnowledgeBase
from blabbermouth.util.lifespan import Lifespan


@attr.s(slots=True)
class CachedMarkovText:
    knowledge_source = attr.ib()
    knowledge_lifespan = attr.ib(converter=Lifespan)
    make_sentence_attempts = attr.ib(default=10)
    text = attr.ib(default=None)

    def make_sentence(self, **source_args):
        if self.text is None or not self.knowledge_lifespan:
            knowledge = ". ".join(sentence for sentence in self.knowledge_source(**source_args))
            self.text = markovify.Text(knowledge)
            self.knowledge_lifespan.reset()

        sentence = self.text.make_sentence(tries=self.make_sentence_attempts)

        if sentence is None:
            print("[CachedMarkovText]: Failed to build markov text")

        return sentence


@attr.s(slots=True)
class MarkovChainIntellegenceCore(IntellegenceCore):
    class Strategy(enum.Enum):
        BY_CURRENT_CHAT = enum.auto()
        BY_CURRENT_USER = enum.auto()
        BY_FULL_KNOWLEDGE = enum.auto()

    chat_id = attr.ib()
    knowledge_base = attr.ib(validator=attr.validators.instance_of(KnowledgeBase))
    knowledge_lifespan = attr.ib()
    make_sentence_attempts = attr.ib()
    answer_placeholder = attr.ib()
    markov_texts_by_strategy = attr.ib(dict)

    def __attrs_post_init__(self):
        self.markov_texts_by_strategy = {
            p[0]: CachedMarkovText(
                knowledge_source=p[1],
                knowledge_lifespan=self.knowledge_lifespan,
                make_sentence_attempts=self.make_sentence_attempts,
            )
            for p in [
                (
                    self.Strategy.BY_CURRENT_CHAT,
                    lambda **kwargs: self.knowledge_base.select_by_chat(kwargs["chat_id"]),
                ),
                (
                    self.Strategy.BY_CURRENT_USER,
                    lambda **kwargs: self.knowledge_base.select_by_user(kwargs["user"]),
                ),
                (
                    self.Strategy.BY_FULL_KNOWLEDGE,
                    lambda **kwargs: self.knowledge_base.select_by_full_knowledge(),
                ),
            ]
        }

    def conceive(self):
        return self._form_message(strategies=[self.Strategy.BY_CURRENT_CHAT, self.Strategy.BY_FULL_KNOWLEDGE])

    def respond(self, user, message):
        return self._form_message(
            strategies=[
                self.Strategy.BY_CURRENT_CHAT,
                self.Strategy.BY_CURRENT_USER,
                self.Strategy.BY_FULL_KNOWLEDGE,
            ],
            user=user,
        )

    def _form_message(self, strategies, **kwargs):
        strategy = random.choice(strategies)

        print("[MarkovChainIntellegenceCore] Using {} strategy".format(strategy))

        sentence = self.markov_texts_by_strategy[strategy].make_sentence(chat_id=self.chat_id, **kwargs)
        return sentence if sentence is not None else self.answer_placeholder
