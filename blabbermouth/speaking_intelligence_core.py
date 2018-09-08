import enum
import random
import io

import aiohttp
import attr

import thought
from intelligence_core import IntelligenceCore
from util.log import logged


class Emotion(enum.Enum):
    NEUTRAL = "neutral"
    GOOD = "good"
    EVIL = "evil"


@logged
@attr.s(slots=True, frozen=True)
class SpeakingIntelligenceCore(IntelligenceCore):
    text_core = attr.ib(validator=attr.validators.instance_of(IntelligenceCore))
    voice = attr.ib()
    lang = attr.ib()
    audio_format = attr.ib()
    api_url = attr.ib()
    api_key = attr.ib()
    emotions = attr.ib(factory=lambda: list(Emotion))

    async def conceive(self):
        text = await self._form_voice(self.text_core.conceive())
        if text is None:
            return None
        if text.thought_type is not thought.Type.TEXT:
            raise ValueError("Wrapped core generated unexpected thought type: {}".format(text.thought_type))
        return await self._make_voice(text.payload)

    async def respond(self, user, message):
        text = await self.text_core.respond(user, message)
        if text is None:
            return None
        if text.thought_type is not thought.Type.TEXT:
            raise ValueError("Wrapped core generated unexpected thought type: {}".format(text.thought_type))
        return await self._make_voice(text.payload)

    async def _make_voice(self, text):
        emotion = random.choice(self.emotions)

        self._log.info("Using {} emotion".format(emotion))

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.api_url, params=self._make_request_params(text=text, emotion=emotion)
            ) as response:
                response_text = await response.read()
                if response.status != 200:
                    raise Exception("Got unwanted response {}: {}".format(response.status, response_text))

        return thought.speech(io.BytesIO(response_text))

    def _make_request_params(self, text, emotion):
        return {
            "speaker": self.voice,
            "format": self.audio_format,
            "key": self.api_key,
            "lang": self.lang,
            "emotion": emotion.value,
            "text": text,
        }
