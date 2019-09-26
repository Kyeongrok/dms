from dmsclient import factories
from dmsclient.exceptions import DMSClientException, DMSDocumentNotFoundError
from tests import BaseTestCase


class ClusterConfigTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(ClusterConfigTestCase, self).__init__(*args, **kwargs)
        self.cluster_1 = factories.ClusterFactory()
        self.cluster_2 = factories.ClusterFactory()

    def setUp(self):
        super(ClusterConfigTestCase, self).setUp()
        try:
            self.client.clusters.delete_all()
        except:
            pass

        for cluster in [self.cluster_1,
                        self.cluster_2]:
            self.client.clusters.create(cluster)
            pass

    def test_get_cluster(self):
        cluster = self.client.clusters.get(self.cluster_1.cluster_id)
        self.assertEqual(cluster, self.cluster_1)

    def test_get_nonexistent_cluster(self):
        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.clusters.get(99999)
        exception = error.exception
        self.assertEqual(str(exception), "Could not find Cluster with ID '99999'")

    def test_get_all_clusters(self):
        clusters = self.client.clusters.get_all()

        clusters = list(clusters)
        self.assertEqual(len(clusters), 2)
        self.assertIn(self.cluster_1, clusters)
        self.assertIn(self.cluster_2, clusters)

    def test_create_cluster(self):
        cluster = factories.ClusterFactory()
        self.client.clusters.create(cluster)

        returned_cluster = self.client.clusters.get(cluster.cluster_id)

        self.assertEqual(cluster, returned_cluster)

    def test_enable_disable_cluster(self):
        cluster = self.client.clusters.get(self.cluster_1.cluster_id)
        self.assertTrue(cluster.available)

        self.client.clusters.disable(self.cluster_1.cluster_id)
        cluster = self.client.clusters.get(self.cluster_1.cluster_id)
        self.assertFalse(cluster.available)

        self.client.clusters.enable(self.cluster_1.cluster_id)
        cluster = self.client.clusters.get(self.cluster_1.cluster_id)
        self.assertTrue(cluster.available)

    def test_set_cluster_weight(self):
        cluster = self.client.clusters.get(self.cluster_1.cluster_id)
        self.assertEqual(cluster.weight, self.cluster_1.weight)

        self.client.clusters.set_weight(self.cluster_1.cluster_id, 5)
        cluster = self.client.clusters.get(self.cluster_1.cluster_id)
        self.assertEqual(cluster.weight, 5)

    def test_set_cluster_weight_invalid(self):
        f = self.client.clusters.set_weight
        self.assertRaises(ValueError, f, self.cluster_1.cluster_id, 'invalid-weight')

    def test_delete_cluster(self):
        self.client.clusters.delete(self.cluster_1.cluster_id)

        with self.assertRaises(DMSClientException) as error:
            self.client.clusters.get(self.cluster_1.cluster_id)
        exception = error.exception

        self.assertEqual(404, exception.status_code)

    def test_delete_nonexistent_cluster(self):
        with self.assertRaises(DMSDocumentNotFoundError) as error:
            self.client.clusters.delete(99999)
        exception = error.exception
        self.assertEqual(str(exception), "Could not find Cluster with ID '99999'")

    def test_delete_all_clusters(self):
        clusters = self.client.clusters.get_all()
        self.assertGreater(len(list(clusters)), 0)

        self.client.clusters.delete_all()

        clusters = self.client.clusters.get_all()
        self.assertEqual(len(list(clusters)), 0)
