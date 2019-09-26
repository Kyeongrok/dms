from datetime import datetime


class Indices(object):
    INDEX_CONFIG = 'volvo-configuration-v1'
    INDEX_RAW = 'volvo-z1-raw-v1'
    INDEX_RESIM_PREFIX = 'volvo-z1-resim-v1'
    INDEX_JOURNAL_PREFIX = 'volvo-z1-log-v1'

    @staticmethod
    def timebased(prefix):
        utc_time = datetime.utcnow()
        return '-'.join([prefix, str(utc_time.year), str(utc_time.month).zfill(2)])
