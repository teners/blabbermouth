import telepot


class AnswerEngineHandler(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, intelligence_registry, self_reference_detector, **kwargs):
        super(AnswerEngineHandler, self).__init__(*args, **kwargs)

        self._intelligence_registry = intelligence_registry
        self._self_reference_detector = self_reference_detector

        print("[AnswerEngine] Created {}".format(id(self)))

    async def on_chat_message(self, message):
        if not self._self_reference_detector(message):
            return

        chat_id = message["chat"]["id"]
        user = message["from"]["username"]

        print("[AnswerEngine] User {} in chat {} is talking to me".format(user, chat_id))

        intelligence_core = self._intelligence_registry.get_core(chat_id)
        answer = intelligence_core.respond(user=user, message=message.get("text", ""))
        if answer is None:
            print('[AnswerEngine] Got "None" answer from intelligence core')
            return

        await self.sender.sendMessage(answer)

    def on__idle(self, _):
        print("[AnswerEngine] Ignoring on__idle")
