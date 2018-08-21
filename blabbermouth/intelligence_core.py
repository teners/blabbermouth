import abc


class IntelligenceCore(abc.ABC):
    @abc.abstractmethod
    async def conceive(self):
        pass

    @abc.abstractmethod
    async def respond(self, user, message):
        pass
