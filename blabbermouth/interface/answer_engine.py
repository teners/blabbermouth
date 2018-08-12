import telepot

from intellegence.intellegence_core import IntellegenceCore


class AnswerEngine(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, intelligence_core, bot_name, **kwargs):
        if not isinstance(intelligence_core, IntellegenceCore):
            raise TypeError('intelligence_core must be IntellegenceCore')

        super(AnswerEngine, self).__init__(*args, **kwargs)

        self._intelligence_core = intelligence_core
        self._self_reference = '@{}'.format(bot_name)

        print('[AnswerEngine] Created {}'.format(id(self)))

    async def on_chat_message(self, message):
        text = message.get('text')
        if text is None:
            return

        if not self._is_talking_to_me(text):
            return

        chat_id = message['chat']['id']
        user = message['from']['username']

        print('[AnswerEngine] User {} in chat {} is talking to me'.format(user, chat_id))

        answer = self._intelligence_core.respond(chat_id=chat_id, user=user, message=text)
        if answer is None:
            print('[AnswerEngine] Got "None" answer from intellegence core')
            return

        await self.sender.sendMessage(answer)

    def on__idle(self, _):
        print('[AnswerEngine] Ignoring on__idle')

    def _is_talking_to_me(self, text):
        return self._self_reference in text
