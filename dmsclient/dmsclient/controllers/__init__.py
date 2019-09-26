import abc
from datetime import datetime

from elasticsearch.helpers import scan

from dmsclient.decorators import elasticsearch
from dmsclient.exceptions import DMSDocumentNotFoundError, DMSClientException, DMSConflictError


class DMSController(abc.ABC):
    """
    Basic controller abstract class providing common operations.

    Controllers interact with a particular DMS document type (drives, segments, sensors,
    etc.) and provide CRUD and other operations for them.

    :param client: instance of DMSClient used for Elasticsearch requests
    """

    def __init__(self, client):
        self.client = client

    @property
    @abc.abstractmethod
    def model_class(self):
        pass

    @elasticsearch()
    def index(self, document):
        """
        Index a document. Overrides the document if a document with the
        same ID already exists.

        :param document: the document object to be created
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """

        assert isinstance(document, self.model_class)

        self.client.elasticsearch.index(
            index=self.model_class.INDEX,
            doc_type=self.model_class.DOC_TYPE,
            id=document.id,
            body=document.to_dict(),
            params={
                'refresh': 'true'
            }
        )

    @elasticsearch()
    def create(self, document):
        """
        Create a document object

        :param document: the document object to be created
        """
        assert isinstance(document, self.model_class)

        # Need to check if a document with the same ID already exists.
        # This is necessary for documents on time-based indices like
        # segments or sensors, otherwise we could end up with multiple
        # documents with the same ID on different indices.
        # Example:
        # A sensor document created on March 2018 will be indexed in
        # "volvo-z1-resim-v1-201803". If we create the same document
        # a month later, it will be indexed in "volvo-z1-resim-v1-201804".
        # This check will prevent this from happening.
        if self.model_class.timebased:
            try:
                self.get(document.id)
                raise DMSConflictError("A %s with the same ID already exists." %
                                       (self.model_class.__name__,), status_code=409)
            except DMSDocumentNotFoundError:
                pass

        self.client.elasticsearch.create(
            index=self.model_class.INDEX,
            doc_type=self.model_class.DOC_TYPE,
            id=document.id,
            body=document.to_dict(),
            params={
                'refresh': 'true'
            }
        )

    @elasticsearch()
    def get(self, doc_id):
        """
        Retrieve the document object matching the given ID

        :param doc_id: the document ID to be retrieved
        :type doc_id: string
        :returns: the document object
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """

        result = self.client.elasticsearch.search(
            index=self.model_class.TEMPLATE,
            doc_type=self.model_class.DOC_TYPE,
            body={
                "query": {
                    "term": {
                        "_id": doc_id
                    }
                }
            },
            size=1
        )

        if result['hits']['total'] == 0:
            raise DMSDocumentNotFoundError("Could not find %s with ID '%s'" % (self.model_class.__name__, doc_id))
        return self.model_class.from_elasticsearch(result['hits']['hits'][0])

    @elasticsearch()
    def delete(self, doc_id):
        """
        Delete the document with the given ID.

        :param doc_id: the document ID to be deleted
        :type doc_id: string
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        result = self.client.elasticsearch.delete_by_query(
            index=self.model_class.TEMPLATE,
            doc_type=self.model_class.DOC_TYPE,
            body={
                'query': {
                    'term': {
                        '_id': doc_id
                    }
                }
            },
            params={
                'refresh': 'true'
            }
        )

        if result['total'] == 0:
            raise DMSDocumentNotFoundError("Could not find %s with ID '%s'" % (self.model_class.__name__, doc_id))
        if result['deleted'] != 1:
            raise DMSClientException("Unexpected error deleting %s with ID '%s': %s"
                                     % (self.model_class.__name__, doc_id, str(result)))

    @elasticsearch()
    def find_by_query(self, query, postprocess=True):
        """
        Find documents that match the given query. The `postprocess` parameter allows you to
        choose to convert the search results to objects or return raw Elasticsearch
        documents.

        Query example:

        query = {
            'query': {
                'bool': {
                    'must': [
                        {'term': {'status': 'created'}}
                    ]
                }
            }

        :param query: Elasticsearch query
        :type query: dict
        :param postprocess: transform search results to objects
        :type postprocess: bool
        :return: a collection of objects
        :rtype: iterator
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        result = scan(self.client.elasticsearch,
                      index=self.model_class.TEMPLATE,
                      doc_type=self.model_class.DOC_TYPE,
                      query=query,
                      size=1000)

        for item in result:
            yield self.model_class.from_elasticsearch(item) if postprocess else item

    def find_by_fields(self, **fields):
        """
        Find documents that match the given fields.

        :param fields: keyword arguments with the fields to use in the search
        :return: a collection of objects
        :rtype: iterator
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        query = {
            'query': {
                'bool': {
                    'must': []
                }
            }
        }

        for k, v in fields.items():
            query['query']['bool']['must'].append({'term': {k: v}})

        return self.find_by_query(query)

    @elasticsearch()
    def __update__(self, doc_id, fields):
        """
        Update fields for the document matching the given ID.

        WARNING: use this with caution as it will not prevent you from updating
        protected fields. To update or create new unprotected fields, use `set_fields`
        instead.

        :param doc_id: the document ID to be updated
        :type doc_id: string
        :param fields: fields to be updated
        :type fields: dict
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """

        fields['updated_at'] = datetime.utcnow()

        # Partial update via "doc" is not available in "update_by_query" call
        # https://github.com/elastic/elasticsearch/issues/20135
        script = {
            "lang": "painless",
            "source": "",
            "params": {}
        }
        for field, value in fields.items():
            script['source'] += "ctx._source.{} = params.{}; ".format(field, field)
            script['params'][field] = value

        result = self.client.elasticsearch.update_by_query(
            index=self.model_class.TEMPLATE,
            doc_type=self.model_class.DOC_TYPE,
            body={
                "query": {
                    "term": {
                        "_id": doc_id
                    }
                },
                "script": script
            },
            params={
                'refresh': 'true'
            }
        )

        if result['total'] == 0:
            raise DMSDocumentNotFoundError("Could not find %s with ID '%s'" % (self.model_class.__name__, doc_id))
        if result['updated'] != 1:
            raise DMSClientException('Unexpected error updating %s with ID %s: %s'
                                     % (self.model_class.__name__, doc_id, str(result)))

    def set_fields(self, doc_id, **fields):
        """
        Update unprotected fields for the document matching the given ID.

        :param doc_id: the document ID to be updated
        :type doc_id: string
        :param fields: extra kwargs with the fields and values to be updated
        :type fields: **kwargs
        :raises ValueError: if any of the fields is protected
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        for field in fields:
            if field in self.model_class.PROTECTED_ATTRIBUTES:
                raise ValueError("'%s' is a protected field of %s." % (field, self.model_class.__name__))
        self.__update__(doc_id, fields)

    @elasticsearch()
    def remove_field(self, doc_id, field_key):
        """
        Remove an unprotected field from the document matching the given ID
        and field key.

        :param doc_id: the document ID
        :type doc_id: string
        :param field_key: the field key to be removed
        :type field_key: string
        :raises ValueError: if any of the fields is protected
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        if field_key in self.model_class.PROTECTED_ATTRIBUTES:
            raise ValueError("'%s' is a protected field of %s." % (field_key, self.model_class.__name__))

        result = self.client.elasticsearch.update_by_query(
            index=self.model_class.TEMPLATE,
            doc_type=self.model_class.DOC_TYPE,
            body={
                "query": {
                    "term": {
                        "_id": doc_id
                    }
                },
                "script": {
                    "source": "ctx._source.remove(params.field)",
                    "params": {
                        "field": field_key
                    }
                }
            },
            params={
                'refresh': 'true'
            }
        )

        if result['total'] == 0:
            raise DMSDocumentNotFoundError("Could not find %s with ID '%s'" % (self.model_class.__name__, doc_id))
        if result['updated'] != 1:
            raise DMSClientException('Unexpected error updating %s with ID %s: %s'
                                     % (self.model_class.__name__, doc_id, str(result)))

    @elasticsearch()
    def add_tags(self, doc_id, tags):
        """
        Add tags to the document matching the given ID.

        :param doc_id: the document ID
        :type doc_id: string
        :param tags: the list of tags to be added
        :type tags: list
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        assert isinstance(tags, list)

        result = self.client.elasticsearch.update_by_query(
            index=self.model_class.TEMPLATE,
            doc_type=self.model_class.DOC_TYPE,
            body={
                "query": {
                    "term": {
                        "_id": doc_id
                    }
                },
                "script": {
                    "source": "ctx._source.tags.addAll(params.tags); ctx._source.updated_at = params.updated_at;",
                    "params": {
                        "tags": tags,
                        "updated_at": datetime.utcnow()
                    }
                }
            },
            params={
                'refresh': 'true'
            }
        )

        if result['total'] == 0:
            raise DMSDocumentNotFoundError("Could not find %s with ID '%s'" % (self.model_class.__name__, doc_id))
        if result['updated'] != 1:
            raise DMSClientException("Unexpected error updating %s with ID '%s': %s"
                                     % (self.model_class.__name__, doc_id, str(result)))

    @elasticsearch()
    def remove_tags(self, doc_id, tags):
        """
        Remove tags for the document matching the given ID.

        :param doc_id: the document ID
        :type doc_id: string
        :param tags: the list of tags to be removed
        :type tags: list
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        assert isinstance(tags, list)

        result = self.client.elasticsearch.update_by_query(
            index=self.model_class.INDEX,
            doc_type=self.model_class.DOC_TYPE,
            body={
                "query": {
                    "term": {
                        "_id": doc_id
                    }
                },
                "script": {
                    "source": "ctx._source.tags.removeAll(params.tags); ctx._source.updated_at = params.updated_at;",
                    "params": {
                        "tags": tags,
                        "updated_at": datetime.utcnow()
                    }
                }
            },
            params={
                'refresh': 'true'
            }
        )

        if result['total'] == 0:
            raise DMSDocumentNotFoundError('Could not find %s with ID %s' % (self.model_class.__name__, doc_id))
        if result['updated'] != 1:
            raise DMSClientException('Unexpected error updating %s with ID %s: %s'
                                     % (self.model_class.__name__, doc_id, str(result)))

    @elasticsearch()
    def get_tags(self, doc_id):
        """
        Obtain the tags of the document matching the given ID.

        :param doc_id: the document ID
        :type doc_id: string
        :return: the list of tags associated to the document
        :rtype: list
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        doc = self.get(doc_id)
        return doc.tags


class DMSControllerWithState(DMSController):
    """
    Controller with additional `set_state()` and `get_state()` methods.
    """

    @property
    @abc.abstractmethod
    def model_class(self):
        pass

    def set_state(self, doc_id, state, **kwargs):
        """
        Update the state for the document matching the given ID.

        :param doc_id: the document ID to be updated
        :type doc_id: string
        :param state: the desired state
        :type state: string
        :raises ValueError: if the state is not valid
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(doc_id, {'state': self.model_class.State(state)}, **kwargs)

    @elasticsearch()
    def get_state(self, doc_id):
        """
        Obtain the state of the document matching the given ID.

        :param doc_id: the document ID
        :type doc_id: string
        :returns: the state of the document
        :rtype: string
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if document with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        d = self.get(doc_id)
        return d.state
