from dmsclient.controllers import DMSControllerWithState
from dmsclient.models.drive import Drive


class DriveController(DMSControllerWithState):
    """
    Controller class for manipulating Drive documents
    """

    @property
    def model_class(self):
        return Drive

    def create_from_ingest(self, dir_name, source_path, ingest_station, **kwargs):
        """
        Utility method to create drives during the drive ingestion process.

        :param dir_name: the drive directory name found on the disk during ingestion
        :type dir_name: string
        :param source_path: the absolute path to the drive directory
        :type source_path: string
        :param ingest_station: the hostname of the ingest station (e.g. amst01-mus-02)
        :type ingest_station: string
        :param kwargs: any extra fields that must be created with the Drive document
        :return: the drive object
        :rtype: :class:`dmsclient.models.drive.Drive`
        """
        cluster = self.client.get_cluster(dir_name)
        drive = Drive.from_ingest(cluster=cluster,
                                  dir_name=dir_name,
                                  source_path=source_path,
                                  ingest_station=ingest_station,
                                  **kwargs)

        super(DriveController, self).create(drive)
        return drive
