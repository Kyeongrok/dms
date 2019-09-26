DMS Installation On Ingest Stations
===================================

The Data Management System (DMS) ingestion components run on CentOS 7 or compatible Redhat versions.

Download DMS Software
----------------------

Download source code packages and documentations from https://github.com/EMCECS/volvo/releases.
Then extract them to a directory. In this document, it is assumed the code is extracted to ~/volvo-1.0.
Adjust accordingly if the version or working directory are different.

Assume user has root privilege.

Tools and Packages
------------------

The following software packages are required

-  mdadm
-  nfs-utils
-  rsync
-  atd

The following python packages must be installed

-  python3
-  pip3

Run the following command to install the tools and packages::

    $ cd ~/volvo-1.0/bootstrap/centos
    $ ./system-setup.sh

User and Group
--------------

Create "ingest" user and add to "resim" group. Enable passwordless sudo for ther user.

Run the following command to set up the user and group::

    $ cd ~/volvo-1.0/bootstrap/centos
    $ ./user-setup.sh

Mount Points
------------

The following mount points must be set up on the ingest stations to their respective NFS exports from Isilon clusters

-  /volvo/z1/islp00001/raw -> nfs.islp00001.ent.autodrivecluster.com:/ifs/z1/raw
-  /volvo/z1/islp00002/raw -> nfs.islp00002.ent.autodrivecluster.com:/ifs/z1/raw
-  /volvo/z1/islp00003/raw -> nfs.islp00003.ent.autodrivecluster.com:/ifs/z1/raw
-  /volvo/z1/islp00004/raw -> nfs.islp00004.ent.autodrivecluster.com:/ifs/z1/raw

Run the following command to set the mount points on ingest stations::
   
    $ cd ~/volvo-1.0/bootstrap/centos
    $ ./mount-setup.sh

If issues encountered, fix them, then re-run the above command. Verify that the mount points have been set up successfully by::

    $ mount | grep volvo

DMS Client
----------

Run the following command to install DMS client, ingest scripts and udev rules::

    $ cd ~/volvo-1.0/bootstrap/dmsclient
    $ ./dmsclient-ingest.sh

If issues are encoutered, re-run the script after the issues are fixed.

- Verify that dmsclient module has been successfully installed::

    $ python3 -c "import dmsclient"

- Verify that DMS executables are installed::

    $ ingest --help
    $ dms_utils --help

- Verify that the configuration file is at /opt/dms/conf/ingest.conf.

- Verify the udev rule has been installed at /etc/udev/rules.d/99z-ingest-trigger.rules.


