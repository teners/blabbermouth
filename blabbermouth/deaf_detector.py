import re

import attr
import autologging
import telepot

from util.chain import BrokenChain, check, not_none


@autologging.logged
class PreviousMessageRetriever:
    @attr.s(slots=True, frozen=True)
    class Info:
        text = attr.ib()
        user = attr.ib()

    def __init__(self):
        self._previous_info = None
        self._retrievers = [self._try_retrieve_from_reply, self._try_infer_from_previous_message]

    def retrieve(self, message, text, user):
        for retriever in self._retrievers:
            previous_message = retriever(message=message, text=text, user=user)
            if previous_message is not None:
                return previous_message
        return None

    def record(self, text, user):
        self._previous_info = self.Info(text=text, user=user)

    def clean(self):
        self._previous_info = None

    def _try_retrieve_from_reply(self, message, **_):
        try:
            reply = not_none(message.get("reply_to_message"))
            previous_text = not_none(reply.get("text"))
            previous_source = not_none(reply.get("from"))
            previous_user = not_none(previous_source.get("username"))
            return self.Info(text=previous_text, user=previous_user)
        except BrokenChain:
            return None

    def _try_infer_from_previous_message(self, user, **_):
        try:
            not_none(self._previous_info)
            check(self._previous_info.user != user)
            return self._previous_info
        except BrokenChain:
            return None


class DeafDetector:
    WHAT_REGEX = re.compile(r"^([ч|ш]т?[о|а|ё|е]|ч[е|и][г|в]о)(\s(блять|бля|нахуй))?\.?$", re.IGNORECASE)

    TO_THIRD_CONVERSION_MAP = {"я": "Он", "меня": "Его", "мне": "Ему", "мной": "Им"}

    def __init__(self):
        self._previous_message_retriever = PreviousMessageRetriever()

    def try_reply(self, message):
        try:
            check("photo" not in message)
            text = not_none(message.get("text"))
            source = not_none(message.get("from"))
            user = not_none(source.get("username"))
        except BrokenChain:
            return None

        if re.match(self.WHAT_REGEX, text) is None:
            self._previous_message_retriever.record(text, user)
            return None

        try:
            previous_message = not_none(self._previous_message_retriever.retrieve(message, text, user))
        except BrokenChain:
            return None

        self._previous_message_retriever.clean()

        return self._reply_to_deaf(previous_message.text, previous_message.user)

    def _reply_to_deaf(self, previous_message, deaf_user):
        self.__log.info("Replying to {}".format(deaf_user))

        return " ".join([self._convert_to_third(word) for word in previous_message.split(" ")])

    def _convert_to_third(self, word):
        return self.TO_THIRD_CONVERSION_MAP.get(word.lower(), word)


class DeafDetectorHandler(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, event_loop, **kwargs):
        super(DeafDetectorHandler, self).__init__(*args, **kwargs)

        self._event_loop = event_loop
        self._backend = DeafDetector()

        self.__log.info("Created {}".format(id(self)))

    async def on_chat_message(self, message):
        self._event_loop.create_task(self._on_chat_message(message))

    async def _on_chat_message(self, message):
        try:
            answer = not_none(self._backend.try_reply(message))
            await self.sender.sendMessage("_{}_".format(answer), parse_mode="Markdown")
        except BrokenChain:
            pass

    def on__idle(self, _):
        self.__log.debug("Ignoring on__idle")
