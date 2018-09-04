import datetime
import random

import telepot

from util.chain import BrokenChain, check, not_none
from util.log import logged
from util.timer import Timer


@logged
class ChatterHandler(telepot.aio.helper.ChatHandler):
    def __init__(
        self,
        *args,
        intelligence_registry,
        self_reference_detector,
        personal_query_detector,
        conceive_interval,
        event_loop,
        **kwargs
    ):
        super(ChatterHandler, self).__init__(*args, **kwargs)

        self._intelligence_registry = intelligence_registry
        self._self_reference_detector = self_reference_detector
        self._personal_quary_detector = personal_query_detector
        self._event_loop = event_loop
        self._conceive_interval = conceive_interval
        self._conceive_timer = Timer(callback=self._conceive, interval=self._randomize_conceive_interval())

        self._log.info("Created {}".format(id(self)))

    async def on_chat_message(self, message):
        self._event_loop.create_task(self._on_chat_message(message))

    async def _on_chat_message(self, message):
        try:
            check(self._self_reference_detector(message))
            source = not_none(message.get("from"))
            user = not_none(source.get("username"))
        except BrokenChain:
            return

        self._log.info("User {} in chat {} is talking to me".format(user, self.chat_id))

        intelligence_core = self._intelligence_registry.get_core(self.chat_id)

        answer = await intelligence_core.respond(user=user, message=message.get("text", ""))
        if answer is None:
            self._log.info('Got "None" answer from intelligence core')
            return

        await self.sender.sendMessage(answer)

    def on__idle(self, _):
        self._log.debug("Ignoring on__idle")

    async def _conceive(self):
        intelligence_core = self._intelligence_registry.get_core(self.chat_id)

        thought = await intelligence_core.conceive()
        if thought is None:
            self._log.info("No new thoughts from intellegence core")
            return

        await self.sender.sendMessage(thought)

        self._conceive_timer.interval = self._randomize_conceive_interval()

    def _randomize_conceive_interval(self):
        return datetime.timedelta(seconds=random.uniform(0, self._conceive_interval.total_seconds()))
