import os
import re
from datetime import datetime

from dmsclient.controllers import DMSControllerWithState
from dmsclient.decorators import elasticsearch
from dmsclient.exceptions import DMSClientException, DMSDocumentNotFoundError, DMSInvalidFormat
from dmsclient.models.segment import Segment
from dmsclient.models.sensor import Sensor
from dmsclient.models.sensorversion import SensorVersion


class SensorController(DMSControllerWithState):
    """
    Controller class for manipulating Sensor and SensorVersion documents
    """

    @property
    def model_class(self):
        return Sensor

    def create_from_segment(self, segment, sensor_type, **kwargs):
        """
        Utility method to create Sensor documents from a Segment object. The Sensor
        document will inherit fields from the given Segment.

        :param segment: the Segment object
        :type segment: string
        :param sensor_type: the sensor type (must be a valid type found in
        `dmsclient.models.sensor.Sensor.SENSOR_TYPES`)
        :type sensor_type: string
        :param kwargs: any extra fields that must be created with the Sensor document
        :return: the Sensor object
        :rtype: :class:`dmsclient.models.sensor.Sensor`
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        s = Sensor.from_segment(segment=segment,
                                sensor_type=sensor_type,
                                **kwargs)
        self.create(s)
        return s

    def create_from_filename(self, filename):
        """
        Utility method to create Sensor documents from a filename.

        :param filename: the name of the Sensor file
        (e.g. "Z1_BK031_CONT_20180316T102815-20180316T102915_FLC.dat")
        :type filename: string
        :return: the Sensor object
        :rtype: :class:`dmsclient.models.sensor.Sensor`
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        sensor_id = os.path.splitext(filename)[0]
        m = re.match(Sensor.INGEST_REGEX, sensor_id)
        if not m:
            raise DMSInvalidFormat("Could not parse sensor_id '%s'" % (sensor_id,))

        sensor_id_split = sensor_id.split('_')
        sensor_type = sensor_id_split[-1]
        segment_id = '_'.join(sensor_id_split[:-1])
        m = re.match(Segment.INGEST_REGEX, segment_id)
        if not m:
            raise DMSInvalidFormat("Could not parse segment_id '%s'" % (segment_id,))

        segment = self.client.segments.get(segment_id)
        return self.create_from_segment(segment, sensor_type)

    def find_by_segment_id(self, segment_id):
        """
        Utility method to find sensors by `segment_id`.

        :param segment_id: the Segment ID
        :type segment_id: string
        :return: a collection of sensors
        :rtype: iterator
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        return self.find_by_fields(segment_id=segment_id)

    @elasticsearch()
    def delete_by_segment_id(self, segment_id):
        """
        Utility method to delete sensors by `segment_id`.

        :param segment_id: the Segment ID
        :type segment_id: string
        :returns: the number of sensors successfully deleted
        :rtype: integer
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        result = self.client.elasticsearch.delete_by_query(
            index=Sensor.TEMPLATE,
            doc_type=Sensor.DOC_TYPE,
            body={
                'query': {
                    'term': {
                        'segment_id': segment_id
                    }
                }
            },
            params={
                'refresh': 'true'
            }
        )
        return result['deleted']

    def create_version_from_filename(self, filename, **kwargs):
        """
        Utility method to create SensorVersion documents from a filename.

        :param filename: the name of the SensorVersion file
        (e.g. "Z1_BK031_CONT_20180316T102815-20180316T102915_FLC_0048.dat")
        :type filename: string
        :return: the SensorVersion object
        :rtype: :class:`dmsclient.models.sensor.SensorVersion`
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        sensorversion_id = os.path.splitext(filename)[0]
        m = re.match(SensorVersion.INGEST_REGEX, sensorversion_id)
        if not m:
            raise DMSInvalidFormat("Could not parse sensorversion_id '%s'" % (sensorversion_id,))

        sensorid_split = sensorversion_id.split('_')[:-1]
        version = sensorversion_id.split('_')[-1]
        sensor_id = '_'.join(sensorid_split)
        m = re.match(Sensor.INGEST_REGEX, sensor_id)
        if not m:
            raise DMSInvalidFormat("Could not parse sensor_id '%s'" % (sensor_id,))
        sensor = self.get(sensor_id)

        return self.create_version(sensor, version, **kwargs)

    @elasticsearch()
    def create_version(self, sensor, version, **kwargs):
        """
        Create a SensorVersion document from a Sensor object and a version.

        :param sensor: the Sensor object
        :type sensor: string
        :param version: the four-digit version
        :type version: string
        :param kwargs: any extra fields that must be created with the SensorVersion document
        :return: the SensorVersion object
        :rtype: :class:`dmsclient.models.sensorversion.SensorVersion`
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        sv = SensorVersion.from_sensor(sensor, version, **kwargs)
        self.client.elasticsearch.create(
            index=SensorVersion.INDEX,
            doc_type=SensorVersion.DOC_TYPE,
            id=sv.sensorversion_id,
            body=sv.to_dict(),
            params={
                'refresh': 'true'
            }
        )
        return sv

    @elasticsearch()
    def get_versions(self, sensor_id):
        """
        Get all SensorVersion documents belonging to a particular Sensor.

        :param sensor_id: the Sensor ID
        :type sensor_id: string
        :return: a collection of SensorVersion objects
        :rtype: iterator
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        query = {
            'query': {
                'bool': {
                    'must': [
                        {'term': {'sensor_id': sensor_id}}
                    ]
                }
            }
        }

        result = self.client.elasticsearch.search(
            index=SensorVersion.TEMPLATE,
            doc_type=SensorVersion.DOC_TYPE,
            body=query
        )

        versions = []
        for entry in result['hits']['hits']:
            versions.append(SensorVersion.from_elasticsearch(entry))
        return versions

    @elasticsearch()
    def get_version(self, sensor_id, version):
        """
        Get a SensorVersion document by the Sensor ID and the version.

        :param sensor_id: the Sensor ID
        :type sensor_id: string
        :param version: the four-digit version
        :type version: string
        :return: the SensorVersion object
        :rtype: :class:`dmsclient.models.sensorversion.SensorVersion`
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if there's no match
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        query = {
            'query': {
                'bool': {
                    'must': [
                        {'term': {'sensor_id': sensor_id}},
                        {'term': {'version': version}}
                    ]
                }
            }
        }

        result = self.client.elasticsearch.search(
            index=SensorVersion.TEMPLATE,
            doc_type=SensorVersion.DOC_TYPE,
            body=query,
            size=1
        )

        if result['hits']['total'] == 0:
            raise DMSDocumentNotFoundError()
        return SensorVersion.from_elasticsearch(result['hits']['hits'][0])

    @elasticsearch()
    def delete_version(self, sensor_id, version):
        """
        Delete a SensorVersion document identified by the Sensor ID and the version.

        :param sensor_id: the Sensor ID
        :type sensor_id: string
        :param version: the four-digit version
        :type version: string
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if there's no match
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        result = self.client.elasticsearch.delete_by_query(
            index=SensorVersion.TEMPLATE,
            doc_type=SensorVersion.DOC_TYPE,
            body={
                'query': {
                    'bool': {
                        'must': [
                            {'term': {'sensor_id': sensor_id}},
                            {'term': {'version': version}}
                        ]
                    }
                }
            },
            params={
                'refresh': 'true'
            }
        )

        if result['total'] == 0:
            raise DMSDocumentNotFoundError()
        if result['deleted'] != 1:
            raise DMSClientException('Unexpected error deleting: %s' % str(result))

    @elasticsearch()
    def delete_all_versions(self, sensor_id):
        """
        Delete all SensorVersion documents identified by the Sensor ID.

        :param sensor_id: the Sensor ID
        :type sensor_id: string
        :returns: the number of SensorVersion documents successfully deleted
        :rtype: integer
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        result = self.client.elasticsearch.delete_by_query(
            index=SensorVersion.TEMPLATE,
            doc_type=SensorVersion.DOC_TYPE,
            body={
                'query': {
                    'term': {
                        'sensor_id': sensor_id
                    }
                }
            },
            params={
                'refresh': 'true'
            }
        )

        return result['deleted']

    @elasticsearch()
    def update_version(self, sensor_id, version, **fields):
        """
        Update the fields of a SensorVersion document identified by the Sensor ID
        and the version.

        :param sensor_id: the Sensor ID
        :type sensor_id: string
        :param version: the four-digit version
        :type version: string
        :param fields: fields to be updated (fields `sensorversion_id`, `sensor_id`,
        and `version` cannot be updated)
        :type fields: kwargs
        :raises dmsclient.exceptions.DMSDocumentNotFoundError: if there's no match
        :raises dmsclient.exceptions.DMSClientException: if any other error occur
        """
        fields.pop('_id', None)
        fields.pop('sensorversion_id', None)
        fields.pop('sensor_id', None)
        fields.pop('version', None)
        fields['updated_at'] = datetime.utcnow()

        # Partial update via "doc" is not available in "update_by_query" call
        # https://github.com/elastic/elasticsearch/issues/20135
        script = {
            "lang": "painless",
            "source": "",
            "params": {}
        }
        for field, value in fields.items():
            if field == 'state':
                # Will raise ValueError exception if 'value' is not a member of the enumerate
                SensorVersion.State(value)
            script['source'] += "ctx._source.{} = params.{}; ".format(field, field)
            script['params'][field] = value

        result = self.client.elasticsearch.update_by_query(
            index=SensorVersion.TEMPLATE,
            doc_type=SensorVersion.DOC_TYPE,
            body={
                'query': {
                    'bool': {
                        'must': [
                            {'term': {'sensor_id': sensor_id}},
                            {'term': {'version': version}}
                        ]
                    }
                },
                "script": script
            },
            params={
                'refresh': 'true'
            },
            conflicts='proceed'
        )

        if result['updated'] == 0:
            raise DMSDocumentNotFoundError()
