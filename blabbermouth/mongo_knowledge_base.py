import pymongo

from blabbermouth.knowledge_base import KnowledgeBase


class MongoKnowledgeBase(KnowledgeBase):
    def __init__(self, host, port, db_name, db_collection):
        self._client = pymongo.MongoClient(host, port)
        self._collection = self._client[db_name][db_collection]

    async def record(self, chat_id, user, text):
        doc = {"chat_id": chat_id, "user": user, "text": text}
        self._collection.insert_one(doc)

    async def select_by_chat(self, chat_id):
        for doc in self._select_by_restriction({"chat_id": chat_id}):
            yield doc

    async def select_by_user(self, user):
        for doc in self._select_by_restriction({"user": user}):
            yield doc

    async def select_by_full_knowledge(self):
        for doc in self._select_by_restriction({}):
            yield doc

    async def _select_by_restriction(self, restriction):
        for doc in map(lambda doc: doc["text"], self._collection.find(restriction)):
            yield doc
