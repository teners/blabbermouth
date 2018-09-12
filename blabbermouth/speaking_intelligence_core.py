import random
import io

import attr

import thought
from intelligence_core import IntelligenceCore
from util.chain import BrokenChain, not_none
from util.log import logged


@logged
@attr.s(slots=True, frozen=True)
class SpeakingIntelligenceCore(IntelligenceCore):
    text_core = attr.ib(validator=attr.validators.instance_of(IntelligenceCore))
    speech_client = attr.ib()
    voice = attr.ib()
    lang = attr.ib()
    audio_format = attr.ib()
    emotions = attr.ib()

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

        response = await self.speech_client.vocalize(
            text=text, voice=self.voice, lang=self.lang, audio_format=self.audio_format, emotion=emotion
        )
        return thought.speech(io.BytesIO(await response))

    @staticmethod
    def _extract_text(core_response):
        if core_response.thought_type is not core_response.Type.TEXT:
            raise ValueError(
                "Wrapped core generated unexpected thought type: {}".format(core_response.thought_type)
            )
        return core_response.payload
