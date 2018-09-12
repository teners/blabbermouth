import enum
import random
import io

import attr

import thought
from intelligence_core import IntelligenceCore
from util.chain import BrokenChain, not_none
from util.log import logged


class Emotion(enum.Enum):
    NEUTRAL = "neutral"
    GOOD = "good"
    EVIL = "evil"


@logged
@attr.s(slots=True, frozen=True)
class SpeakingIntelligenceCore(IntelligenceCore):
    http_session = attr.ib()
    text_core = attr.ib(validator=attr.validators.instance_of(IntelligenceCore))
    voice = attr.ib()
    lang = attr.ib()
    audio_format = attr.ib()
    api_url = attr.ib()
    api_key = attr.ib()
    emotions = attr.ib(factory=lambda: list(Emotion))

    async def conceive(self):
        try:
            return await self._make_voice(self._extract_text(not_none(await self.text_core.conceive())))
        except BrokenChain:
            return None

    async def respond(self, user, message):
        try:
            return await self._make_voice(
                self._extract_text(not_none(await self.text_core.respond(user, message)))
            )
        except BrokenChain:
            return None

    async def _make_voice(self, text):
        emotion = random.choice(self.emotions)

        self._log.info("Using {} emotion".format(emotion))

        async with self.http_session.get(
            self.api_url, params=self._make_request_params(text=text, emotion=emotion)
        ) as response:
            response_text = await response.read()
            if response.status != 200:
                raise Exception("Got unwanted response {}: {}".format(response.status, response_text))

        return thought.speech(io.BytesIO(response_text))

    @staticmethod
    def _extract_text(core_response):
        if core_response.thought_type is not core_response.Type.TEXT:
            raise ValueError(
                "Wrapped core generated unexpected thought type: {}".format(core_response.thought_type)
            )
        return core_response.payload

    def _make_request_params(self, text, emotion):
        return {
            "speaker": self.voice,
            "format": self.audio_format,
            "key": self.api_key,
            "lang": self.lang,
            "emotion": emotion.value,
            "text": text,
        }
