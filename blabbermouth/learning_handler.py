import telepot

from blabbermouth.knowledge_base import KnowledgeBase


class LearningHandler(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, knowledge_base, self_reference_detector, bot_name, **kwargs):
        if not isinstance(knowledge_base, KnowledgeBase):
            raise TypeError("knowledge_base must be KnowledgeBase")

        super(LearningHandler, self).__init__(*args, **kwargs)

        self._knowledge_base = knowledge_base
        self._self_reference_detector = self_reference_detector
        self._bot_name = bot_name

        print("[LearningHandler] Created {}".format(id(self)))

    async def on_chat_message(self, message):
        text = message.get("text")
        if text is None:
            return
        if self._self_reference_detector(message):
            return

        user = message["from"]["username"]
        if user == self._bot_name:
            return

        chat_id = message["chat"]["id"]

        await self._knowledge_base.record(chat_id=chat_id, user=user, text=text)

    def on__idle(self, _):
        print("[LearningHandler] Ignoring on__idle")
