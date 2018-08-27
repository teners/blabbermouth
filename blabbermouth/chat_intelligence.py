import attr
import telepot


@attr.s
class IntelligenceRegistry:
    core_constructor = attr.ib()
    cores = attr.ib(factory=dict)

    def create_core(self, chat_id):
        self.cores[chat_id] = self.core_constructor(chat_id)

    def get_core(self, chat_id):
        return self.cores[chat_id]


class ChatIntelligence(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, intelligence_registry, **kwargs):
        super(ChatIntelligence, self).__init__(*args, **kwargs)

        intelligence_registry.create_core(self.chat_id)

        print("[ChatIntelligence] Created {}".format(id(self)))

    async def on_chat_message(self, message):
        pass

    def on__idle(self, _):
        print("[ChatIntelligence] Ignoring on__idle")
