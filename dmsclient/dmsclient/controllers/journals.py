from dmsclient.controllers import DMSController
from dmsclient.decorators import elasticsearch
from dmsclient.models.journal import Journal


class JournalController(DMSController):
    """
    Controller class for manipulating Journal documents
    """

    @property
    def model_class(self):
        return Journal

    def create(self, document):
        """
        Create a Journal document. For journals, this is the same as
        using the `index` method on the Journal controller.

        :param document: the Journal object to be created/indexed
        """
        self.index(document)

    @elasticsearch()
    def delete_all(self):
        """
        Delete all Journal documents.

        :raises dmsclient.exceptions.DMSClientException: if an error occur
        """
        self.client.elasticsearch.delete_by_query(
            index=self.model_class.TEMPLATE,
            doc_type=self.model_class.DOC_TYPE,
            body={
                'query': {
                    'match_all': {}
                }
            },
            params={
                'conflicts': 'proceed',
                'refresh': 'true'
            }
        )
