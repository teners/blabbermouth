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
