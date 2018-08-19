import telepot

from blabbermouth.intellegence_core import IntellegenceCore


class AnswerEngineHandler(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, intelligence_core, self_reference_detector, **kwargs):
        if not isinstance(intelligence_core, IntellegenceCore):
            raise TypeError("intelligence_core must be IntellegenceCore")

        super(AnswerEngineHandler, self).__init__(*args, **kwargs)

        self._intelligence_core = intelligence_core
        self._self_reference_detector = self_reference_detector

        print("[AnswerEngine] Created {}".format(id(self)))

    async def on_chat_message(self, message):
        if not self._self_reference_detector(message):
            return

        chat_id = message["chat"]["id"]
        user = message["from"]["username"]

        print("[AnswerEngine] User {} in chat {} is talking to me".format(user, chat_id))

        answer = self._intelligence_core.respond(chat_id=chat_id, user=user, message=message.get("text", ""))
        if answer is None:
            print('[AnswerEngine] Got "None" answer from intellegence core')
            return

        await self.sender.sendMessage(answer)

    def on__idle(self, _):
        print("[AnswerEngine] Ignoring on__idle")
