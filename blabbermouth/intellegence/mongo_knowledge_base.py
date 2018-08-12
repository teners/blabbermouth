import pymongo

from intellegence.knowledge_base import KnowledgeBase


class MongoKnowledgeBase(KnowledgeBase):
    def __init__(self, host, port, db_name, db_collection):
        self._client = pymongo.MongoClient(host, port)
        self._collection = self._client[db_name][db_collection]

    def record(self, chat_id, user, text):
        doc = {
            'chat_id': chat_id,
            'user': user,
            'text': text,
        }
        self._collection.insert_one(doc)

    def select_by_chat(self, chat_id):
        yield from self._select_by_restriction({'chat_id': chat_id})

    def select_by_user(self, user):
        yield from self._select_by_restriction({'user': user})

    def select_by_full_knowledge(self):
        yield from self._select_by_restriction({})

    def _select_by_restriction(self, restriction):
        yield from map(lambda doc: doc['text'], self._collection.find(restriction))
