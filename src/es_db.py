from elasticsearch import Elasticsearch, exceptions
from elasticsearch_dsl import connections, Search, Document, Index, Text, Date, Long, Q, analyzer, tokenizer
from config import es_host


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


class Elastic_Database():
    def __init__(self, index_name: str):
        connections.create_connection(hosts=[es_host], timeout=20)
        self.create_index(index_name)
        self.index = index_name

    def create_index(self, index_name: str) -> None:
        """ Create the given index

        Arguments:
            index_name {str} -- Name of the index to create
        """
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

    def delete_index(self, index_name="") -> None:
        """ Delete the given index

        Keyword Arguments:
            index_name {str} -- Name of the index to delete (default: {""})
        """
        if index_name:
            i = Index(index_name)
            i.delete()
        else:
            self.index_name.delete()

    def save_attachment(self, attachment: Attachment, index_name="") -> None:
        """ Save the given Attachment to the given index

        Arguments:
            attachment {Attachment} -- Attachment derived from the original message and image

        Keyword Arguments:
            index_name {str} -- Name of the index to save the attachment to (default: {""})
        """
        if index_name:
            attachment.save(index=index_name)
        else:
            attachment.save(index=self.index)

    def exists(self, guild_id: str, es_id="", hash="") -> bool:
        """ Check if the given attachment exists in the give
        Elasticsearch index

        Arguments:
            guild_id {str} -- Discord guild ID

        Keyword Arguments:
            es_id {str} -- Elasticsearch document ID (default: {""})
            hash {str} -- MD5 hash of the image having its existence checked (default: {""})

        Returns:
            bool -- True if already indexed, False otherwise
        """
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

    def get_jump_url_by_id(self, es_id: str) -> str:
        """ Get the URL that will jump to the message in the Discord client

        Arguments:
            es_id {str} -- Elasticsearch ID of the message event

        Returns:
            str -- Jump URL
        """
        q = Q('match', _id=es_id)

        search = Search(index=self.index)
        s = search.query(q)

        res = s.execute()

        if len(res.hits) > 0:
            return res.hits[0].message_url
