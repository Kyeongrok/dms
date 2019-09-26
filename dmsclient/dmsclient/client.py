import logging
from datetime import timedelta, datetime

from elasticsearch import Elasticsearch
from uhashring import HashRing

from dmsclient.controllers.asdmoutput import AsdmOutputController
from dmsclient.controllers.cartridges import CartridgeController
from dmsclient.controllers.clusters import ClusterController
from dmsclient.controllers.journals import JournalController
from dmsclient.controllers.drives import DriveController
from dmsclient.controllers.readers import ReaderController
from dmsclient.controllers.usbreaders import USBReaderController
from dmsclient.controllers.scenarios import ScenarioController
from dmsclient.controllers.segments import SegmentController
from dmsclient.controllers.sensors import SensorController
from dmsclient.exceptions import DMSClientException
from dmsclient.mappings import MAPPINGS

logger = logging.getLogger('dmsclient')


class DMSClient(object):
    """
    Client for the DMS and wrapper for the Elasticsearch client.

    :param string es_endpoint: Elasticsearch endpoint.
    :param string es_user: Elasticsearch user.
    :param string es_password: Elasticsearch password.
    :param bool create_templates: Create the Elasticsearch templates when instantiated (optional).
    :param bool verify_templates: Verify the configured Elasticsearch templates when instantiated.
                                  If True, the client will fail if any template is not created (optional).
    :param bool initial_sync: Obtain the cluster configuration when instanted. If False, the client
                              will defer the sync until there is a request (optional).
    :raises dmsclient.exceptions.DMSClientException: if there is any error related to the DMS
    """

    SYNC_INTERVAL = timedelta(minutes=10)

    def __init__(self, es_endpoint, es_user, es_password,
                 create_templates=False, verify_templates=True, initial_sync=True):
        logger.info('Connecting to Elasticsearch backend')

        self.elasticsearch = Elasticsearch(
            [es_endpoint],
            http_auth=(es_user, es_password),
            verify_certs=False
        )

        self.readers = ReaderController(self)
        self.usbreaders = USBReaderController(self)
        self.cartridges = CartridgeController(self)
        self.clusters = ClusterController(self)
        self.journals = JournalController(self)
        self.drives = DriveController(self)
        self.segments = SegmentController(self)
        self.sensors = SensorController(self)
        self.scenarios = ScenarioController(self)
        self.asdmoutput = AsdmOutputController(self)

        self.last_sync = datetime.min

        if create_templates:
            self.create_templates()
        else:
            logger.info('Skipping template creation')

        if verify_templates:
            self.verify_templates()
        else:
            logger.info('Skipping template verification')

        if initial_sync:
            self.sync_cluster_config()
        else:
            logger.info('Skipping initial sync')

    def create_templates(self):
        """
        Create the templates configured in `dmsclient.mappings.MAPPINGS`.
        """
        for template, mappings in MAPPINGS.items():
            logger.info("Creating template '%s'..." % (template,))
            self.elasticsearch.indices.put_template(template, body=mappings)

    def verify_templates(self):
        """
        Verify that the template names are available in Elasticsearch.

        :raises dmsclient.exceptions.DMSClientException: if a template does not exist in Elasticsearch
        """
        for template in MAPPINGS.keys():
            logger.info("Verifying template '%s'..." % (template,))
            if not self.elasticsearch.indices.exists_template(template):
                raise DMSClientException("Template '%s' does not exist in Elasticsearch" % (template, ))

    def sync_cluster_config(self, force=False):
        """
        Obtain the latest cluster configuration from Elasticsearch and update the hash ring.
         This method is called every time there is an operation that requires communication
         with Elasticsearch. However, it will only synchronize the cluster configuration if
         the time elapsed since the last sync is greater than `SYNC_INTERVAL` or the `force`
         parameter is set to `True`.

        :param bool force: Force synchronization regardless of the time elapsed since last sync
        :raises dmsclient.exceptions.DMSClientException: if there is no cluster configured in Elasticsearch
        """
        if not force and ((datetime.now() - self.last_sync) < self.SYNC_INTERVAL):
            return

        logger.debug('Syncing cluster configuration')
        nodes_ring = {}

        try:
            clusters = self.clusters.get_all()
            for cluster in clusters:
                if not cluster.available:
                    continue
                nodes_ring[cluster.cluster_id] = {
                    'instance': cluster,
                    'weight': cluster.weight
                }
        except Exception as e:
            raise DMSClientException("Could not obtain cluster configuration. %s" % (str(e),))

        logger.debug('Obtained %d clusters from Elasticsearch' % (len(nodes_ring),))

        if len(nodes_ring) == 0:
            raise DMSClientException('There are no available cluster configured in Elasticsearch')

        self.hashring = HashRing(nodes=nodes_ring)
        self.last_sync = datetime.now()

    def get_cluster(self, key):
        """
        Return the cluster object for the provided key

        :param key: the key to look for, normally, the drive ID.
        :return: a cluster object
        :rtype: :py:class:`dmsclient.models.cluster.Cluster`
        """
        return self.hashring.get_node_instance(key)

    def get_index(self, index_pattern, doc_type, **fields):
        """
        Return the index of the object that matches with the provided filters.

        :param string index_pattern: Index pattern to perform the search
        :param string doc_type: Document type to look for
        :param fields: Arguments that are used in the query as filters
        :return: The index name that matches the given filters
        :raises dmsclient.exceptions.DMSClientException: if there is no match
        """
        query = {
            'query': {
                'bool': {
                    'must': []
                }
            }
        }
        for k, v in fields.items():
            query['query']['bool']['must'].append({'match': {k: v}})

        result = self.elasticsearch.search(index=index_pattern,
                                           doc_type=doc_type,
                                           body=query)
        docs = result['hits']['hits']
        if len(docs) == 1:
            index = docs[0]['_index']
            return index
        else:
            message = '"found":false'
            raise DMSClientException(message, 404)
