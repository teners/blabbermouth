import re


def personal_query_detector(identity):
    identity_regex = re.compile('^/(.*)@{}$'.format(identity))

    def detector(message):
        text = message.get('text')
        if text is None:
            return None

        match = re.match(identity_regex, text)
        if match is None:
            return None

        return match.group(1)

    return detector


def self_reference_detector(identity):
    self_reference = '@{}'.format(identity)

    def detector(message):
        reply = message.get('reply_to_message')
        if reply is not None:
            return reply['from']['username'] == identity

        text = message.get('text')
        if text is None:
            return None

        return self_reference in text

    return detector
