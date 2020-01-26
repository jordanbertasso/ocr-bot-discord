from elasticsearch import Elasticsearch, exceptions
from elasticsearch_dsl import connections, Search, Document, Index, Text, Date, Long, Q, analyzer, tokenizer


class Elastic_Database():
    def __init__(self, index):
        self.es_client = Elasticsearch(['elasticsearch'])
        connections.create_connection(hosts=["elasticsearch:9200"], timeout=20)
        self.create_index(index)
        self.index = index

    def create_index(self, index_name):
        i = Index(index_name)

        doc = Attachment()

        if not i.exists():
            try:
                i.document(Attachment)
                i.create()
            except Exception as e:
                print(e)
                return

        self.index = i

    def delete_index(self, index=None):
        if index:
            i = Index(index)
            i.delete()
        else:
            self.index.delete()

    def save_attachment(self, attachment, index=None):
        if index:
            attachment.save(index=index)
        else:
            attachment.save(index=self.index)

    def exists(self, guild_id, es_id=None, hash=None, index=None):
        search = Search(index=self.index)

        if es_id and hash:
            return False
        elif hash:
            q = Q('bool', must=[Q('match', hash=hash),
                                Q('match', guild_id=guild_id)])
        elif es_id:
            q = Q('bool', must=[Q('match', id=es_id),
                                Q('match', guild_id=guild_id)])
        else:
            return False

        s = search.query(q)

        res = s.execute()

        if len(res.hits) > 0:
            return True
        else:
            return False

    def get_jump_url_by_id(self, es_id):
        res = self.es_client.get(index=self.index, id=es_id)

        return res['_source']['message_url']


standard = analyzer('standard',
                    tokenizer=tokenizer('standard'),
                    filter=['lowercase']
                    )


class Attachment(Document):
    timestamp = Date()
    author_id = Text()
    author_username = Text()
    channel = Text()
    category_id = Text()
    guild = Text()
    guild_id = Text()
    url = Text()
    message_url = Text()
    filename = Text()
    text = Text(analyzer=standard)
    hash = Text()
