import abc


class IntelligenceCore(abc.ABC):
    @abc.abstractmethod
    def conceive(self):
        pass

    @abc.abstractmethod
    def respond(self, user, message):
        pass
