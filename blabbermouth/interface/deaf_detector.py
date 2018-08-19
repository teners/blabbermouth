import re

import attr
import telepot

from blabbermouth.util.chain import BrokenChain, check, not_none


class PreviousMessageRetreiver:
    @attr.s(slots=True, frozen=True)
    class Info:
        text = attr.ib()
        user = attr.ib()

    def __init__(self):
        self._previous_info = None
        self._retreivers = [self._try_retreive_from_reply, self._try_infer_from_previous_message]

    def retreive(self, message, text, user):
        for retreiver in self._retreivers:
            previous_message = retreiver(message=message, text=text, user=user)
            if previous_message is not None:
                return previous_message
        return None

    def record(self, text, user):
        self._previous_info = self.Info(text=text, user=user)

    def _try_retreive_from_reply(self, message, **_):
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
            check(self._previous_info.user == user)
            return self._previous_info
        except BrokenChain:
            return None


class DeafDetector:
    WHAT_REGEX = re.compile(r"^[ч|ш]т?[о|а|ё|е](\s(блять|бля|нахуй))?\.?$", re.IGNORECASE)

    TO_THIRD_CONVERSION_MAP = {"я": "Он", "меня": "Его", "мне": "Ему", "мной": "Им"}

    def __init__(self):
        self._previous_message_retreiver = PreviousMessageRetreiver()

    def try_reply(self, message):
        try:
            check("photo" not in message)
            text = not_none(message.get("text"))
            source = not_none(message.get("from"))
            user = not_none(source.get("username"))

            self._previous_message_retreiver.record(user, text)
            not_none(re.match(self.WHAT_REGEX, text))
            self._previous_message_retreiver.record(user=None, text=None)

            previous_message = not_none(self._previous_message_retreiver.retreive(message, user, text))
            return self._reply_to_deaf(previous_message.text, previous_message.user)
        except BrokenChain:
            return None

    def _reply_to_deaf(self, previous_message, deaf_user):
        print("[DeafDetector] Replying to {}".format(deaf_user))

        return " ".join([self._convert_to_third(word) for word in previous_message.split(" ")])

    def _convert_to_third(self, word):
        return self.TO_THIRD_CONVERSION_MAP.get(word.lower(), word)


class DeafDetectorHandler(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(DeafDetectorHandler, self).__init__(*args, **kwargs)

        self._backend = DeafDetector()

        print("[DeafDetectorHandler] Created {}".format(id(self)))

    async def on_chat_message(self, message):
        try:
            answer = not_none(self._backend.try_reply(message))
            await self.sender.sendMessage("_{}_".format(answer), parse_mode="Markdown")
        except BrokenChain:
            pass

    def on__idle(self, _):
        print("[DeafDetectorHandler] Ignoring on__idle")
