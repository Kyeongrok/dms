# udev Rule and Action Script
The udev rules monitor udev add/remove events on block devices starting with "md" followed by any number of digits, and invoke the script to ingest the raw data. 
* Make sure ingest.py and dms_utils.py are in system PATH or in /opt/dms/bin
* Copy 99z-ingest-trigger.rules to /etc/udev/rule.d. By default the rule take config from /opt/dms/conf/ingest.conf.
* Adjust parameters in ingest.conf if necessary.
* To enable the udev rule
```
$ udevadm control --reload
```

## Test Locally
To test udev script locally, set the following env variables that will be passed from udev rules.
```
export DEVNAME=/dev/md0
```
* Test add action

Run this command to test add action. The log file is at /opt/dms/logs/ 
```
ACTION=add ./ingest-device.sh dispatch
```
* Test remove action

Run this command to test remove action
```
ACTION=remove ./ingest-device.sh dispatch
```

## Test Action Triggered by udev Rule
Use VM on vCenter to create raid0 device. The steps were tested on CentOS VM on vSphere
* Add a couple of disks to your VM.
* Follow the steps here to create raid0 md device. https://www.thegeekdiary.com/redhat-centos-managing-software-raid-with-mdadm/
* Check status of device, e.g., /dev/md123, with mdadm
```
$ mdadm --detail /dev/md123
```
* Simulate the removal and insertion of disks using the following commands, replace sdb, sdc with your disk name.
```
# To simulate disk removal
$ echo 1 >  /sys/block/sdb/device/delete
$ echo 1 >  /sys/block/sdc/device/delete
```

```
# To simulate disk insertion. Replace host0 with host1, host2, etc., depending on the VM OS
echo "- - -" > /sys/class/scsi_host/host0/scan
```
