from dmsclient.controllers import DMSControllerWithState
from dmsclient.decorators import elasticsearch
from dmsclient.models.drive import Drive
from dmsclient.models.segment import Segment


class SegmentController(DMSControllerWithState):
    """
    Controller class for manipulating Segment documents
    """

    @property
    def model_class(self):
        return Segment

    def create_from_drive(self, segment_id, sequence, drive, **kwargs):
        """
        Utility method to create a Segment from a Drive.

        :param segment_id: the ID of the Segment to be created (e.g. Z1_21YD3_CONT_20170823T073455-20170823T073828)
        :type segment_id: string
        :param sequence: numeric index of this segment
        :type sequence: integer
        :param drive: Drive object
        :type drive: :class:`dmsclient.models.drive.Drive`
        :param kwargs: any additional Drive fields
        :type kwargs: keyword arguments
        :return: the Segment object
        :rtype: :class:`dmsclient.models.segment.Segment`
        """
        assert isinstance(drive, Drive)
        cluster = self.client.get_cluster(drive.drive_id)
        s = Segment.from_drive(segment_id=segment_id,
                               sequence=sequence,
                               drive=drive,
                               cluster=cluster,
                               **kwargs)
        self.create(s)
        return s

    def find_by_drive_id(self, drive_id):
        """
        Utility method to find segments by `drive_id`.

        :param drive_id: the Drive ID
        :type drive_id: string
        :return: a collection of segments
        :rtype: iterator
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        return self.find_by_fields(drive_id=drive_id)

    @elasticsearch()
    def delete_by_drive_id(self, drive_id):
        """
        Utility method to delete segments by `drive_id`.

        :param drive_id: the Drive ID
        :type drive_id: string
        :returns: the number of segments successfully deleted
        :rtype: integer
        :raises dmsclient.exceptions.DMSClientException: if an error occurs
        """
        result = self.client.elasticsearch.delete_by_query(
            index=Segment.TEMPLATE,
            doc_type=Segment.DOC_TYPE,
            body={
                'query': {
                    'term': {
                        'drive_id': drive_id
                    }
                }
            },
            params={
                'refresh': 'true'
            }
        )
        return result['deleted']
