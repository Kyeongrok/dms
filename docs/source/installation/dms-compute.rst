DMS Client Installation On Compute Nodes
========================================

Installation of DMS client on HPC compute nodes.

Download DMS Software
-----------------------------

Download source code packages and documentations from https://github.com/EMCECS/volvo/releases.
Then extract them to a directory. In this document, it is assumed the code is extracted to ~/volvo-1.0. 
Adjust accordingly if the version or working directory are different.

Assume user has root privilege.

Tools and Packages
------------------

The following software packages are required. Note that depending on the OS of the compute node, the packages may have different names.

-  nfs-utils

The following python packages must be installed

-  python3
-  pip3

User, Group, and Mount Points
-----------------------------

This section contains the suggested setup for user, group, mode, and permissions. Adjust if necessary to
achieve best protection of the files and convenience for the users.

- Create "ingest" user and "resim" group. Add the user to the "resim" group.
- Create an user, e.g., "resim", to own the result directories from the simulation jobs.
- The HPC jobs to produce permanent data should be executed as "ingest" user. 
- Any other users who expect to run HPC simulation jobs should be added to the "resim" group so that they will be able to read the permanent data.

Mount points and their expected mode, owner, and group are listed in the table below. The <resim_user>, e.g., "resim", is the user that should own the mount points for resim, output, and useroutput. 

+--------------------------------+--------+---------------+--------+
| Mount Point                    | Mode   | Owner         | Group  |
+================================+========+===============+========+
| /volvo/z1/islp0000[1-4]/raw    | 640    | ingest        | resim  |
+--------------------------------+--------+---------------+--------+
| /volvo/z1/islp0000[1-4]/perm   | 640    | ingest        | resim  |
+--------------------------------+--------+---------------+--------+
| /volvo/z1/islp0000[1-4]/resim  | 660    | <resim_user>  | resim  |
+--------------------------------+--------+---------------+--------+
| /volvo/z1/islp0000[1-4]/output | 660    | <resim_user>  | resim  |
+--------------------------------+--------+---------------+--------+
| /volvo/z1/islp00001/useroutput | 660    | <resim_user>  | resim  |
+--------------------------------+--------+---------------+--------+

NFS Mounts
----------

The following NFS mounts must be set up on HPC nodes to their respective NFS exports from Isilon clusters

Raw data. Mount permission: read only

-  /volvo/z1/islp00001/raw -> nfs.islp00001.ent.autodrivecluster.com:/ifs/z1/raw
-  /volvo/z1/islp00002/raw -> nfs.islp00002.ent.autodrivecluster.com:/ifs/z1/raw
-  /volvo/z1/islp00003/raw -> nfs.islp00003.ent.autodrivecluster.com:/ifs/z1/raw
-  /volvo/z1/islp00004/raw -> nfs.islp00004.ent.autodrivecluster.com:/ifs/z1/raw

Permanent data after merge/split/annotate. Mount permission: read and write

-  /volvo/z1/islp00001/perm -> nfs.islp00001.ent.autodrivecluster.com:/ifs/z1/perm
-  /volvo/z1/islp00002/perm -> nfs.islp00002.ent.autodrivecluster.com:/ifs/z1/perm
-  /volvo/z1/islp00003/perm -> nfs.islp00003.ent.autodrivecluster.com:/ifs/z1/perm
-  /volvo/z1/islp00004/perm -> nfs.islp00004.ent.autodrivecluster.com:/ifs/z1/perm

Output from sensor resim. Mount permission: read and write

-  /volvo/z1/islp00001/resim -> nfs.islp00001.ent.autodrivecluster.com:/ifs/z1/resim
-  /volvo/z1/islp00002/resim -> nfs.islp00002.ent.autodrivecluster.com:/ifs/z1/resim
-  /volvo/z1/islp00003/resim -> nfs.islp00003.ent.autodrivecluster.com:/ifs/z1/resim
-  /volvo/z1/islp00004/resim -> nfs.islp00004.ent.autodrivecluster.com:/ifs/z1/resim

Output from ASDM resim. Mount permission: read and write

-  /volvo/z1/islp00001/output -> nfs.islp00001.ent.autodrivecluster.com:/ifs/z1/output
-  /volvo/z1/islp00002/output -> nfs.islp00002.ent.autodrivecluster.com:/ifs/z1/output
-  /volvo/z1/islp00003/output -> nfs.islp00003.ent.autodrivecluster.com:/ifs/z1/output
-  /volvo/z1/islp00004/output -> nfs.islp00004.ent.autodrivecluster.com:/ifs/z1/output

Output from user scenario. Mount permission: read and write

-  /volvo/z1/islp00001/useroutput -> nfs.islp00001.ent.autodrivecluster.com:/ifs/z1/useroutput

DMS Client
----------

Run the following command to install DMS client::

    $ cd ~/volvo-1.0/bootstrap/dmsclient
    $ ./dmsclient-compute.sh

If issues are encoutered, re-run the script after the issues are fixed.

Verify that dmsclient module has been successfully installed::

    $ python3 -c "import dmsclient"

