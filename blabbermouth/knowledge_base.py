import abc


class KnowledgeBase(abc.ABC):
    @abc.abstractmethod
    async def record(self, chat_id, user, text):
        pass

    @abc.abstractmethod
    async def select_by_full_knowledge(self):
        pass

    @abc.abstractmethod
    async def select_by_chat(self, chat_id):
        pass

    @abc.abstractmethod
    async def select_by_user(self, user):
        pass
