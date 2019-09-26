import time
from datetime import datetime

from dmsclient import factories
from dmsclient.exceptions import DMSClientException, DMSDocumentNotFoundError
from tests import BaseTestCase


class AsdmOutputControllerTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(AsdmOutputControllerTestCase, self).__init__(*args, **kwargs)
        self.asdmoutput_1 = factories.AsdmOutputFactory(asdm_version='v3',
                                                        cluster_id='cluster-2',
                                                        extra_field_1='extra-field-1-value',
                                                        extra_field_2='extra-field-2-value',
                                                        extra_field_3='extra-field-3-value')
        self.asdmoutput_2 = factories.AsdmOutputFactory(asdmoutput_id='asdmoutput-test-1',
                                                        segment_id='segment-test-1',
                                                        sensor_versions=[{'sensor': 'CAM', 'version': 'v1.2'}],
                                                        asdm_version='v2',
                                                        cluster_id='cluster-1',
                                                        created_at=datetime(2017, 12, 10, 20, 34, 56),
                                                        updated_at=datetime(2017, 12, 11, 12, 20, 49),
                                                        nfs_host='cluster-nfs-1',
                                                        smb_host='cluster-smb-1',
                                                        dat_file='/file.dat',
                                                        mat_file='/file.mat',
                                                        smb_share=r'\\smbshare\abc',
                                                        path='/path/to/asdm',
                                                        extra_field_1='extra-field-1-value',
                                                        extra_field_2='extra-field-2-value',
                                                        extra_field_3='extra-field-3-value')

    def setUp(self):
        super(AsdmOutputControllerTestCase, self).setUp()
        self.client.asdmoutput.create(self.asdmoutput_1)

    def tearDown(self):
        super(AsdmOutputControllerTestCase, self).tearDown()
        for d in [self.asdmoutput_1,
                  self.asdmoutput_2]:
            try:
                self.client.asdmoutput.delete(d.asdmoutput_id)
                pass
            except DMSClientException:
                pass

    def test_create_asdmoutput(self):
        self.client.asdmoutput.create(self.asdmoutput_2)

        d = self.client.asdmoutput.get('asdmoutput-test-1')

        self.assertEqual(d.asdmoutput_id, 'asdmoutput-test-1')
        self.assertEqual(d.segment_id, 'segment-test-1')
        self.assertEqual(d.sensor_versions, [{'sensor': 'CAM', 'version': 'v1.2'}])
        self.assertEqual(d.asdm_version, 'v2')
        self.assertEqual(d.cluster_id, 'cluster-1')
        self.assertEqual(d.created_at, datetime(2017, 12, 10, 20, 34, 56))
        self.assertEqual(d.updated_at, datetime(2017, 12, 11, 12, 20, 49))
        self.assertEqual(d.nfs_host, 'cluster-nfs-1')
        self.assertEqual(d.smb_host, 'cluster-smb-1')
        self.assertEqual(d.dat_file, '/file.dat')
        self.assertEqual(d.mat_file, '/file.mat')
        self.assertEqual(d.smb_share, r'\\smbshare\abc')
        self.assertEqual(d.path, '/path/to/asdm')
        self.assertEqual(d.extra_fields['extra_field_1'], 'extra-field-1-value')
        self.assertEqual(d.extra_fields['extra_field_2'], 'extra-field-2-value')
        self.assertEqual(d.extra_fields['extra_field_3'], 'extra-field-3-value')

    def test_get_asdmoutput(self):
        d = self.client.asdmoutput.get(self.asdmoutput_1.asdmoutput_id)
        self.assertEqual(self.asdmoutput_1, d)

    def test_delete_asdmoutput(self):
        self.client.asdmoutput.get(self.asdmoutput_1.asdmoutput_id)
        self.client.asdmoutput.delete(self.asdmoutput_1.asdmoutput_id)

        f = self.client.asdmoutput.get
        self.assertRaises(DMSDocumentNotFoundError, f, self.asdmoutput_1.asdmoutput_id)

    def test_find_by_fields(self):
        docs = self.client.asdmoutput.find_by_fields(cluster_id='cluster-2',
                                                     asdm_version='v3')
        docs = list(docs)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0], self.asdmoutput_1)

    def test_find_by_query(self):
        query = {
            'query': {
                'term': {'cluster_id': 'cluster-2'}
            }
        }
        docs = self.client.asdmoutput.find_by_query(query=query)
        docs = list(docs)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0], self.asdmoutput_1)

    def test_set_extra_fields(self):
        extra_fields = {
            "field_%s_1" % int(time.time()): 'field-value-1',
            "field_%s_2" % int(time.time()): 'field-value-2',
            "field_%s_3" % int(time.time()): 'field-value-3'
        }
        self.client.asdmoutput.set_fields(self.asdmoutput_1.asdmoutput_id, **extra_fields)

        segment = self.client.asdmoutput.get(self.asdmoutput_1.asdmoutput_id)

        for field in extra_fields:
            self.assertIn(field, segment.extra_fields)

    def test_set_fields_protected(self):
        fields = {
            "asdm_version": 'field-value-1'
        }
        with self.assertRaises(ValueError) as error:
            self.client.asdmoutput.set_fields(self.asdmoutput_1.asdmoutput_id, **fields)
        exception = error.exception
        self.assertIn("'asdm_version' is a protected field of AsdmOutput.", str(exception))

    def test_remove_extra_field(self):
        field_to_remove = 'extra_field_1'
        segment = self.client.asdmoutput.get(self.asdmoutput_1.asdmoutput_id)
        self.assertIn(field_to_remove, segment.extra_fields)

        self.client.asdmoutput.remove_field(self.asdmoutput_1.asdmoutput_id, field_to_remove)

        segment = self.client.asdmoutput.get(self.asdmoutput_1.asdmoutput_id)
        self.assertNotIn(field_to_remove, segment.extra_fields)

    def test_remove_extra_field_nonexistent_segment(self):
        f = self.client.asdmoutput.remove_field
        self.assertRaises(DMSDocumentNotFoundError, f, 'FAKE_ID_123', 'field_x')

    def test_remove_field_protected(self):
        field = 'asdm_version'
        with self.assertRaises(ValueError) as error:
            self.client.asdmoutput.remove_field(self.asdmoutput_1.asdmoutput_id, field)
        exception = error.exception
        self.assertIn("'asdm_version' is a protected field of AsdmOutput.", str(exception))
