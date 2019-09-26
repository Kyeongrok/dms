import string
from datetime import datetime

import factory
from factory import fuzzy
from factory.compat import UTC
from factory.fuzzy import FuzzyDateTime

from dmsclient import utils
from dmsclient.models.asdmoutput import AsdmOutput
from dmsclient.models.cartridge import Cartridge
from dmsclient.models.cluster import Cluster
from dmsclient.models.drive import Drive
from dmsclient.models.reader import Reader
from dmsclient.models.scenario import Scenario
from dmsclient.models.scenariosegment import ScenarioSegment
from dmsclient.models.segment import Segment
from dmsclient.models.sensor import Sensor
from dmsclient.models.sensorversion import SensorVersion


class CartridgeFactory(factory.Factory):
    class Meta:
        model = Cartridge

    cartridge_id = factory.Sequence(lambda n: 'FECA0779140801261903-%s' % n)
    device = '/dev/md0'
    ingest_station = fuzzy.FuzzyText(length=4, prefix='ingest-', chars=string.ascii_lowercase + string.digits)
    usage = fuzzy.FuzzyDecimal(0.5, 5.0)
    workflow_type = factory.Iterator(Cartridge.WorkflowType)

    ingest_state = factory.Iterator(Reader.IngestState)
    slot = 'sas-phy0'
    updated_at = fuzzy.FuzzyNaiveDateTime(datetime(2017, 10, 20))


class ReaderFactory(factory.Factory):
    class Meta:
        model = Reader

    reader_id = factory.Sequence(lambda n: 'reader-%s' % n)
    hostname = fuzzy.FuzzyText(length=4, prefix='ingest-', chars=string.ascii_lowercase + string.digits)
    device = '/dev/md0'
    status = factory.Iterator(Reader.Status)
    ingest_state = factory.Iterator(Reader.IngestState)
    message = 'Foo bar'
    mount = '/mnt-1'
    port = 'sas-phy0'
    updated_at = fuzzy.FuzzyNaiveDateTime(datetime(2017, 10, 20))


class ClusterFactory(factory.Factory):
    class Meta:
        model = Cluster

    cluster_id = fuzzy.FuzzyText(length=4, prefix='cl-', chars=string.ascii_lowercase + string.digits)
    weight = fuzzy.FuzzyInteger(1, 4)
    available = True
    updated_at = factory.LazyFunction(datetime.utcnow)
    raw_export = '/raw/export'
    perm_export = '/perm/export'
    resim_export = '/resim/export'
    output_export = '/output/export'
    useroutput_export = '/useroutput/export'
    raw_mount = '/ifs/z1/amst-cl01/raw'
    perm_mount = '/ifs/z1/amst-cl01/perm'
    resim_mount = '/ifs/z1/amst-cl01/resim'
    output_mount = '/ifs/z1/amst-cl01/output'
    useroutput_mount = '/ifs/z1/amst-cl01/useroutput'
    raw_share = '/raw/share'
    perm_share = '/perm/share'
    resim_share = '/resim/share'
    output_share = '/output/share'
    useroutput_share = '/useroutput/share'
    nfs_host = 'cluster-1'
    smb_host = 'cluster-smb-1'


class DriveFactory(factory.Factory):
    class Meta:
        model = Drive

    drive_id = factory.LazyAttribute(lambda d: '%s_%s_CONT_%s' %
                                               (d.project_name,
                                                d.car_id,
                                                utils.datetime_to_str(d.logged_at)))
    car_id = fuzzy.FuzzyText(length=5, chars=string.ascii_uppercase + string.digits)
    project_name = fuzzy.FuzzyText(length=4, chars=string.ascii_uppercase + string.digits)
    cluster_id = fuzzy.FuzzyText(length=4, prefix='cl-', chars=string.ascii_lowercase + string.digits)
    ingest_station = fuzzy.FuzzyText(length=4, prefix='ingest-', chars=string.ascii_lowercase + string.digits)
    nfs_host = fuzzy.FuzzyText(length=4, prefix='nfs-host-', chars=string.ascii_lowercase + string.digits)
    smb_host = fuzzy.FuzzyText(length=4, prefix='smb-host-', chars=string.ascii_lowercase + string.digits)
    smb_share = factory.LazyAttribute(lambda d: '/raw/share/%s' % d.drive_id)
    logged_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    source_path = factory.LazyAttribute(lambda d: '/source/path/%s' % d.drive_id)
    target_path = factory.LazyAttribute(lambda d: '/target/path/%s' % d.drive_id)
    state = Drive.State.CREATED
    tags = ['raw', 'test', 'raining']
    size = fuzzy.FuzzyInteger(10000, 10000000)
    file_count = fuzzy.FuzzyInteger(100, 1000)


class SegmentFactory(factory.Factory):
    class Meta:
        model = Segment

    segment_id = factory.LazyAttribute(lambda d: '%s-%s' % (d.drive_id, utils.datetime_to_str(d.ended_at)))
    sequence = factory.Sequence(lambda n: '%04d' % (n + 1,))
    drive_id = factory.LazyAttribute(lambda s: '%s_%s_CONT_%s' %
                                               (s.project_name,
                                                s.car_id,
                                                utils.datetime_to_str(s.started_at)))
    project_name = fuzzy.FuzzyText(length=4, chars=string.ascii_uppercase + string.digits)
    car_id = fuzzy.FuzzyText(length=5, chars=string.ascii_uppercase + string.digits)
    cluster_id = fuzzy.FuzzyText(length=4, prefix='cl-', chars=string.ascii_lowercase + string.digits)
    started_at = FuzzyDateTime(datetime(2010, 1, 1, tzinfo=UTC))
    ended_at = FuzzyDateTime(datetime(2010, 1, 1, tzinfo=UTC))
    created_at = FuzzyDateTime(datetime(2010, 1, 1, tzinfo=UTC))
    updated_at = FuzzyDateTime(datetime(2010, 1, 1, tzinfo=UTC))
    state = Segment.State.CREATED
    tags = ['test', 'raining']
    perm_path = factory.LazyAttribute(lambda d: '/perm/path/%s/%s' % (d.drive_id, d.segment_id))
    output_path = factory.LazyAttribute(lambda d: '/output/path/%s/%s' % (d.drive_id, d.segment_id))
    resim_path = factory.LazyAttribute(lambda d: '/resim/path/%s/%s' % (d.drive_id, d.segment_id))


class SensorFactory(factory.Factory):
    class Meta:
        model = Sensor

    sensor_id = factory.LazyAttribute(lambda s: '%s_%s' % (s.segment_id, s.sensor_type))
    segment_id = factory.LazyAttribute(lambda s: 'Z1_64TG3_CONT_%s-%s' %
                                                 (utils.datetime_to_str(s.started_at),
                                                  utils.datetime_to_str(s.ended_at)))
    sensor_type = factory.Iterator(Sensor.SENSOR_TYPES)
    project_name = fuzzy.FuzzyText(length=4, chars=string.ascii_uppercase + string.digits)
    car_id = fuzzy.FuzzyText(length=5, chars=string.ascii_uppercase + string.digits)
    cluster_id = fuzzy.FuzzyText(length=4, prefix='cl-', chars=string.ascii_lowercase + string.digits)
    started_at = FuzzyDateTime(datetime(2010, 1, 1, tzinfo=UTC))
    ended_at = FuzzyDateTime(datetime(2010, 1, 1, tzinfo=UTC))
    created_at = FuzzyDateTime(datetime(2010, 1, 1, tzinfo=UTC))
    updated_at = FuzzyDateTime(datetime(2010, 1, 1, tzinfo=UTC))
    state = Sensor.State.CREATED
    tags = ['test', 'raining']
    perm_path = factory.LazyAttribute(lambda d: '/perm/path/%s' % d.segment_id)
    output_path = factory.LazyAttribute(lambda d: '/output/path/%s' % d.segment_id)
    resim_path = factory.LazyAttribute(lambda d: '/resim/path/%s' % d.segment_id)


class SensorVersionFactory(SensorFactory):
    class Meta:
        model = SensorVersion

    sensorversion_id = factory.LazyAttribute(lambda s: '%s_%04d' % (s.sensor_id, s.sequence))
    sequence = factory.Sequence(lambda n: n + 1)
    version = factory.Sequence(lambda n: 'v2.%d' % (n,))


class ScenarioSegmentFactory(factory.Factory):
    class Meta:
        model = ScenarioSegment

    scenario_id = fuzzy.FuzzyText(length=8, chars=string.ascii_lowercase + string.digits)
    segment_id = factory.Sequence(lambda n: 'Z1_64TG3_CONT_%s-%s' %
                                            (utils.datetime_to_str(datetime.utcnow()),
                                             utils.datetime_to_str(datetime.utcnow())))
    state = ScenarioSegment.State.CREATED


class ScenarioFactory(factory.Factory):
    class Meta:
        model = Scenario

    name = fuzzy.FuzzyText(length=8, chars=string.ascii_lowercase + string.digits)
    user = fuzzy.FuzzyText(length=3, chars=string.digits)
    query = ''
    sensor_versions = [{'sensor': 'CAM', 'version': 'v1.1'}, {'sensor': 'LDR', 'version': 'v2.44'}]
    scenario_segments = factory.List([
        factory.SubFactory(ScenarioSegmentFactory),
        factory.SubFactory(ScenarioSegmentFactory),
        factory.SubFactory(ScenarioSegmentFactory),
        factory.SubFactory(ScenarioSegmentFactory),
        factory.SubFactory(ScenarioSegmentFactory),
    ])
    created_at = fuzzy.FuzzyNaiveDateTime(datetime(2015, 1, 1))
    updated_at = fuzzy.FuzzyNaiveDateTime(datetime(2015, 1, 1))
    started_at = fuzzy.FuzzyNaiveDateTime(datetime(2015, 1, 1))
    ended_at = fuzzy.FuzzyNaiveDateTime(datetime(2015, 1, 1))
    state = Scenario.State.CREATED
    cpu_time = fuzzy.FuzzyInteger(100, 1000)
    output_path = factory.LazyAttribute(lambda s: '/output/path/%s-%s' % (s.name, s.user))


class AsdmOutputFactory(factory.Factory):
    class Meta:
        model = AsdmOutput

    asdmoutput_id = factory.Sequence(lambda n: 'asdmoutput-%04d' % (n + 1,))
    segment_id = factory.Sequence(lambda n: 'segment-%04d' % (n + 1,))
    sensor_versions = [{'sensor': 'CAM', 'version': 'v1.1'}, {'sensor': 'LDR', 'version': 'v2.44'}]
    asdm_version = 'v2'
    cluster_id = 'cluster-1'
    created_at = fuzzy.FuzzyNaiveDateTime(datetime(2015, 1, 1))
    updated_at = fuzzy.FuzzyNaiveDateTime(datetime(2015, 1, 1))
    nfs_host = 'cluster-nfs-1'
    smb_host = 'cluster-smb-1'
    dat_file = '/file.dat'
    mat_file = '/file.mat'
    smb_share = factory.LazyAttribute(lambda s: r'\\%s%s' % (s.smb_host, s.path))
    path = factory.LazyAttribute(lambda d: '/path/%s' % d.asdmoutput_id)
