import re

import telepot


class DeafDetector(telepot.aio.helper.ChatHandler):
    WHAT_REGEX = re.compile(r"^[ч|ш]т?[о|а|ё](\s(блять|бля|нахуй))?\.?$", re.IGNORECASE)

    TO_THIRD_CONVERSION_MAP = {"я": "Он", "меня": "Его", "мне": "Ему", "мной": "Им"}

    def __init__(self, *args, **kwargs):
        super(DeafDetector, self).__init__(*args, **kwargs)

        self._previous_message = None
        self._previous_sender = None

        print("[DeafDetector] Created {}".format(id(self)))

    async def on_chat_message(self, message):
        if "photo" in message:
            return

        text = message.get("text")
        if text is None:
            return

        user = message["from"]["username"]

        if (
            self._previous_message is not None
            and re.match(self.WHAT_REGEX, text) is not None
            and user != self._previous_sender
        ):
            await self.sender.sendMessage(
                self._reply_to_deaf(self._previous_message, user), parse_mode="Markdown"
            )
            self._previous_message = None
            self._previous_sender = None
        else:
            self._previous_message = text
            self._previous_sender = user

    def on__idle(self, _):
        print("[DeafDetector] Ignoring on__idle")

    def _reply_to_deaf(self, previous_message, deaf_user):
        print("[DeafDetector] Replying to {}".format(deaf_user))

        reply = [self._convert_to_third(word) for word in previous_message.split(" ")]
        return "_{}_".format(" ".join(reply))

    def _convert_to_third(self, word):
        return self.TO_THIRD_CONVERSION_MAP.get(word.lower(), word)
