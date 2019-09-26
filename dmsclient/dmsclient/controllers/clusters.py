from elasticsearch.helpers import scan

from dmsclient.controllers import DMSController
from dmsclient.decorators import elasticsearch
from dmsclient.models.cluster import Cluster


class ClusterController(DMSController):
    """
    Controller class for manipulating Cluster documents
    """

    @property
    def model_class(self):
        return Cluster

    def create(self, cluster):
        """
        Create a cluster object. It overrides the cluster if a cluster
        with the same ID already exists.

        :param cluster: the cluster object to be created
        :type cluster: :class:`dmsclient.models.cluster.Cluster`
        """
        self.index(cluster, sync=False)

    def enable(self, cluster_id):
        """
        Enable the cluster matching the given ID.

        :param cluster_id: the cluster ID
        :type cluster_id: string
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a cluster with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(cluster_id, {'available': 1})

    def disable(self, cluster_id):
        """
        Disable the cluster matching the given ID.

        :param cluster_id: the cluster ID
        :type cluster_id: string
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a cluster with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        self.__update__(cluster_id, {'available': 0})

    def set_weight(self, cluster_id, weight):
        """
        Update the reader ingest state for the document matching the given ID.

        :param cluster_id: the cluster ID to be updated
        :type cluster_id: string
        :param weight: the cluster weight
        :type weight: int
        :raises ValueError: if weight is not an integer
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if a cluster with the given ID does not exist
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        if not isinstance(weight, int):
            raise ValueError('Cluster weight must be an integer')
        self.__update__(cluster_id, {'weight': weight})

    def get_all(self):
        """
        Get all Cluster documents.

        :return: a collection of Cluster objects
        :rtype: iterator
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        result = scan(self.client.elasticsearch,
                      index=Cluster.INDEX,
                      doc_type=Cluster.DOC_TYPE,
                      size=1000)

        for item in result:
            yield Cluster.from_elasticsearch(item)

    @elasticsearch()
    def delete_all(self):
        """
        Delete all Cluster documents.

        :raises dmsclient.exceptions.DMSClientException: if an error occur
        """
        self.client.elasticsearch.delete_by_query(
            index=Cluster.INDEX,
            doc_type=Cluster.DOC_TYPE,
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
