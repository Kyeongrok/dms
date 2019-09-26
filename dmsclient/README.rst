===================================
Data Management System (DMS) client
===================================

This library allows developers to interact with the Data Management System (DMS) in the scope of the Volvo and Zenuity
ADAC project.

Quick Start
-----------

You can easily install this library.

.. code-block:: sh

    $ python3 setup.py install

This will install the library and its dependencies.

Creating an instance of the DMSClient class allows the following
arguments:


+--------------------------------+------------+-------------------+----------------------------------------------------------------+
| Name                           | Required   | Default Value     | Description                                                    |
+================================+============+===================+================================================================+
| ``es_endpoint``                | Yes        | None              | Elasticsearch endpoint.                                        |
+--------------------------------+------------+-------------------+----------------------------------------------------------------+
| ``es_user``                    | Yes        | None              | Elasticsearch username                                         |
+--------------------------------+------------+-------------------+----------------------------------------------------------------+
| ``es_password``                | Yes        | None              | Elasticsearch password                                         |
+--------------------------------+------------+-------------------+----------------------------------------------------------------+
| ``initial_sync``               | No         | True              | By default, the client will try to obtain the cluster          |
|                                |            |                   | configuration from Elasticsearch. If we want to defer this     |
|                                |            |                   | initial sync until there is a request, we can set it to False. |
+--------------------------------+------------+-------------------+----------------------------------------------------------------+
| ``create_templates``           | No         | False             | Whether or not the client should create the index templates on |
|                                |            |                   | Elasticsearch when it's instantiated. If the templates already |
|                                |            |                   | exist, it will just do nothing.                                |
+--------------------------------+------------+-------------------+----------------------------------------------------------------+
| ``verify_templates``           | No         | True              | Whether or not the client should verify that the templates     |
|                                |            |                   | exist on Elasticsearch. If True, the client will fail          |
|                                |            |                   | if some template is missing on Elasticsearch.                  |
+--------------------------------+------------+-------------------+----------------------------------------------------------------+

This is how you can instantiate the ``DMSClient`` class and use the library.

.. code-block:: python

    import datetime
    from dmsclient.client import DMSClient
    from dmsclient.models.cluster import Cluster

    # We need to include the `skip_initial_sync` if there's no cluster configuration in Elasticsearch yet.
    client = DMSClient(es_endpoint='https://10.23.34.56:9200',
                       es_user='elastic',
                       es_password='changeme',
                       initial_sync=False)

    # Let's create a fake cluster configuration object
    cluster = Cluster(cluster_id='amst-cl01',
                      weight=1,
                      available=True,
                      updated_at=datetime.datetime.now(),
                      raw_export='/raw/export',
                      perm_export='/perm/export',
                      resim_export='/resim/export',
                      output_export='/output/export',
                      raw_mount='/ifs/z1/amst-cl01/raw',
                      perm_mount='/ifs/z1/amst-cl01/perm',
                      resim_mount='/ifs/z1/amst-cl01/resim',
                      output_mount='/ifs/z1/amst-cl01/output',
                      raw_share='/raw/share',
                      perm_share='/perm/share',
                      resim_share='/resim/share',
                      output_share='/output/share',
                      nfs_host='cluster-1',
                      smb_host='cluster-smb-1')

    # and push it to Elasticsearch
    self.client.clusters.create(cluster)

    # Now that we have the cluster configured, let's sync the client
    self.client.sync_cluster_config()

    # This will create a Drive in Elasticsearch from the directory and source path
    drive = client.drives.create_from_ingest(dir_name='Z1_MLB090_CONT_20170823T073000',
                                             source_path='/source/path')

    # Then, we would split the Drive lifespan into segments and upload them like this
    segment = client.segments.create_from_drive(drive.drive_id + '-0001',
                                                drive=drive,
                                                started_at=datetime.datetime(2017, 8, 23, 7, 32, 18),
                                                ended_at=datetime.datetime(2017, 8, 23, 7, 43, 57),
                                                tags=['raw', 'test'])


Development
-----------

Getting Started
~~~~~~~~~~~~~~~
Assuming that you have Python 3.x and ``virtualenv`` installed, set up your
environment and install the required dependencies like this instead of
the ``python3 setup.py install`` defined above:

.. code-block:: sh

    $ git clone https://github.com/EMCECS/volvo.git
    $ cd volvo
    $ virtualenv venv
    ...
    $ . venv/bin/activate
    $ cd dmsclient
    $ pip install -r requirements.txt


Elasticsearch
~~~~~~~~~~~~~

You can easily deploy an Elasticsearch node for development and testing purposes with
Docker:

.. code-block:: sh

    $ docker run -p 9200:9200 -e "http.host=0.0.0.0" -e "transport.host=127.0.0.1" docker.elastic.co/elasticsearch/elasticsearch:5.6.4

And connect to it at ``http://127.0.0.1:9200`` with username ``elastic`` and password ``changeme``.


Running Tests
~~~~~~~~~~~~~

The tests require a configuration file with the connection details to
an Elasticsearch cluster. Create a ``test.conf`` file with the following
content.

.. code-block::

    [func_test]
    endpoint = http://127.0.0.1:9200
    user = elastic
    password = changeme

And export the ``TEST_CONFIG_FILE`` environment variable with the path to
this file.

.. code-block:: sh

    $ export TEST_CONFIG_FILE=/path/to/test.conf

You can run tests in all supported Python versions using ``tox``. Note that
this requires that you have all supported versions of Python installed,
otherwise you must pass ``-e`` or run the ``nosetests`` command directly.


.. code-block:: sh

    $ tox
    $ tox -e py34,py35

You can also run individual tests with your default Python version:

.. code-block:: sh

    $ nosetests
