from elasticsearch import Elasticsearch
from elasticsearch_dsl import connections, Document, Date, Text, Q, Search, Index


class esdb():
    def __init__(self, index):
        self.es_client = Elasticsearch()
        connections.create_connection(hosts=["elasticsearch:9200"], timeout=20)
        self.create_index(index)
        self.index = index

    def create_index(self, index_name):
        i = Index(index_name)

        doc = Attachment()

        try:
            doc.init(index_name)
        except Exception as e:
            print('Couldnt create index')
            print(e)
            i.delete()
            doc.init(index_name)

        self.index = i

    def exists(self, hash, index=None):
        search = Search(index=self.index)
        q = Q("term", hash=hash)
        s = search.query(q)

        res = s.execute()

        if len(res.hits) > 0:
            return True
        else:
            return False


class Attachment(Document):
    timestamp = Date()
    author_id = Text()
    author_username = Text()
    url = Text()
    filename = Text()
    text = Text()
    hash = Text()

db = esdb('index2')
print(db)
res = db.exists('yes')
print(res)