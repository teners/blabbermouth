import attr
import autologging
import telepot


@attr.s
class IntelligenceRegistry:
    core_constructor = attr.ib()
    cores = attr.ib(default=dict)

    def create_core(self, chat_id):
        self.cores[chat_id] = self.core_constructor(chat_id)

    def get_core(self, chat_id):
        return self.cores[chat_id]


@autologging.logged
class ChatIntelligence(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, intelligence_registry, **kwargs):
        super(ChatIntelligence, self).__init__(*args, **kwargs)

        intelligence_registry.create_core(self.chat_id)

        self.__log.info("Created {}".format(id(self)))

    def on__idle(self, _):
        self.__log.debug("Ignoring on__idle")
