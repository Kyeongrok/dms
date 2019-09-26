# Utilities for Data Management System
## Cluster Configuration
### Create cluster configuration in ES
* Edit and source dms-env file
* To create
```
$ ./dms_utils.py --help
$ ./dms_utils.py cluster_create --help
$ ./dms_utils.py cluster_create --cluster-id=islp00001
```

## Ingest Reader Configuration
### Create reader configuration in ES
* Edit and source dms-env file
* To create an ingest reader in ES
```
$ ./dms_utils.py reader_update --help
$ ./dms_utils.py reader_create --reader-id=reader1 --host=host1
```

### Update reader in ES

```
$ ./dms_utils.py reader_update --help
$ ./dms_utils.py reader_update --reader-id=reader1 --host=host1 "active" "/dev/md123" "copying" 
```

