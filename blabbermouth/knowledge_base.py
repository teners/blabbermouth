import abc


class KnowledgeBase(abc.ABC):
    @abc.abstractmethod
    def record(self, chat_id, user, text):
        pass

    @abc.abstractmethod
    def select_by_full_knowledge(self):
        pass

    @abc.abstractmethod
    def select_by_chat(self, chat_id):
        pass

    @abc.abstractmethod
    def select_by_user(self, user):
        pass
