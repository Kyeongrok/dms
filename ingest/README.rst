=====================
Ingest Python package
=====================

The Ingest Python package is meant to be installed on the upload stations and triggered by Udev rules when a cartridge is inserted to the station. At a glance, this package is responsible for:

1. Scanning the cartridge to obtain new Drive data
2. Uploading the data found on the cartridges to the Isilon cluster
3. Create and update metadata records on the Data Management System (DMS)


Quick Start
-----------

This package depends on the ``dmsclient`` Python package. Check out the `dmsclient README file
<../dmsclient>`_ for installation instructions.

Make sure you have successfully installed the ``dmsclient`` package by checking the output of the following command.

.. code-block:: sh

    $ pip3 show dmsclient


Install the Ingest package.

.. code-block:: sh

    $ python3 setup.py install

If the package has been successfully installed you should now have the ``ingest`` and ``dms_utils`` commands.

.. code-block:: sh

    $ ingest --help
    Usage: ingest [OPTIONS]

    Options:
      -c, --config-file PATH  Path to the configuration file containing
                              Elasticsearch connection details  [required]
      -m, --mount-path PATH   Path to the directory where the cartridge is mounted
                              [required]
      --version               Show the version and exit.
      --help                  Show this message and exit.


.. code-block:: sh

    $ dms_utils --help                                                                                              documentation ⚑ 1  (e) .venv 
    Usage: dms_utils [OPTIONS] COMMAND [ARGS]...

      Utility to manage configurations of Data Management System

    Options:
      -c, --config-file PATH  Path to the configuration file containing ingest
                              configuration
      --help                  Show this message and exit.

    Commands:
      cluster_create      Create a cluster configuration
      cluster_delete      Delete a cluster configuration
      cluster_delete_all  Delete all cluster configurations
      cluster_list        List all cluster configurations
      cluster_update      Update a cluster configuration
      datadir_ingest      Ingest drive data stored on local directory...
      device_format       Format the data cartridge for better writing...
      device_ingest       Simulate udev add/remove actions to trigger...
      drive_list          List drives in specified state
      ingest_stop         Stop running ingestions...
      ingest_verify       Verify data on Isilon clusters with data on...
      journal_create      Create a journal entry for ingestion log...
      reader_create       Create a cartridge reader
      reader_delete       Delete a cartridge reader
      reader_list         List all cartridge readers
      reader_update       Update a cartridge reader: status,...
      segment_create      Create segments for specified drive
      segment_list        List segments for specified drive

You can see an example of the expected configuration file `here <config.example.ini>`_.


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
    $ . venv/bin/activate
    $ cd dmsclient
    $ python3 setup.py develop
    $ cd ..
    $ pip3 install -r ingest/requirements.txt

Elasticsearch
~~~~~~~~~~~~~

You can easily deploy an Elasticsearch node for development and testing purposes with
Docker:

.. code-block:: sh

    $ docker run -p 9200:9200 -e "http.host=0.0.0.0" -e "transport.host=127.0.0.1" docker.elastic.co/elasticsearch/elasticsearch:5.6.4

And connect to it at ``http://127.0.0.1:9200`` with username ``elastic`` and password ``changeme``.


Configuration
~~~~~~~~~~~~~

Copy the example file to ``config.ini`` and edit the ``[elasticsearch]`` section to use your Elasticsearch instance.

.. code-block::

    ...
    [elasticsearch]
    endpoint = http://127.0.0.1:9200
    user = elastic
    password = changeme
    ...

Create a local directory that will simulate the input mount point of the cartridge that will contain the data to be ingested and another one that will simulate the Isilon output mount point.

.. code-block:: sh

    $ mkdir -p ~/mount/{input,output}

Fill the input directory with some test data.

.. code-block:: sh

    $ ./samples/gen-drive-data.sh ~/mount/input

Considering you have your Elasticsearch instance up and running. Create a local cluster configuration with the ``dms_utils`` command.

.. code-block:: sh

    $ python3 ingest/utils/dms_utils -c config.ini cluster_create --cluster-id=test-cluster-1 --mount-prefix $HOME/mount/output

Ingestion
~~~~~~~~~

You can now start your ingest process and debug it if need it.

.. code-block:: sh

    $ python3 ingest/bin/ingest -c ingest/config.ini -m $HOME/mount/input

At the end of the process the output will show the result of the ingestion:

.. code-block::

  ...
  2017-12-22T13:45:03.847Z INFO ingest.worker filename:worker.py line(79) Drive 'Z1_BT2DI_CONT_20171222T121747' ingested successfully
  2017-12-22T13:45:03.875Z INFO ingest.manager filename:manager.py line(76) Processed 2 directories. Found 0 errors
  2017-12-22T13:45:03.876Z INFO ingest.main filename:ingest line(59) Exiting

And the output directory should contain the ingested drives.

.. code-block::

  $ tree $HOME/mount/output                                                                                   documentation ✚ 2 ⚑ 1  (e) .venv 
  /home/user/mount/output
  └── test-cluster-1
      └── raw
          ├── BT2DI
          │   └── 201712
          │       └── 22T121747
          │           └── Z1_BT2DI_CONT_20171222T121747
          │               ├── Z1_BT2DI_CONT_20171222T121748-20171222T121848.vpcap
          │               └── Z1_BT2DI_CONT_20171222T121758-20171222T121858.vpcap
          └── SAZFM
              └── 201712
                  └── 22T121728
                      └── Z1_SAZFM_CONT_20171222T121728
                          ├── Z1_SAZFM_CONT_20171222T121729-20171222T121829.vpcap
                          └── Z1_SAZFM_CONT_20171222T121739-20171222T121839.vpcap

    10 directories, 4 files
