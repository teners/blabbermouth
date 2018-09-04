import attr
import telepot

from util.log import logged


@attr.s
class IntelligenceRegistry:
    core_constructor = attr.ib()
    cores = attr.ib(factory=dict)

    def create_core(self, chat_id):
        self.cores[chat_id] = self.core_constructor(chat_id)

    def get_core(self, chat_id):
        return self.cores[chat_id]


@logged
class ChatIntelligence(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, intelligence_registry, **kwargs):
        super(ChatIntelligence, self).__init__(*args, **kwargs)

        intelligence_registry.create_core(self.chat_id)

        self.__log.info("Created {}".format(id(self)))

    async def on_chat_message(self, message):
        pass

    def on__idle(self, _):
        self.__log.debug("Ignoring on__idle")
