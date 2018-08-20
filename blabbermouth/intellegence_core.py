import abc


class IntellegenceCore(abc.ABC):
    @abc.abstractmethod
    def conceive(self):
        pass

    @abc.abstractmethod
    def respond(self, user, message):
        pass
