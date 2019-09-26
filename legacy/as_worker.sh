#!/bin/bash
# Author: Rickard Math
# Reason for script: check README

MYHOST=$(uname -n|awk -F'.' '{print $1}')
MYFULLHOST=$(host $MYHOST | awk '{print $1}')

# list of hosts that should scp data
UPLOAD_SCP="asupload6"

# scp ?
CHECK_SCP=$(echo $UPLOAD_SCP | grep "$MYHOST")
SERVER1=
SERVER2=


# scp destination servers
if [[ -n $CHECK_SCP ]]; then
    # cs8 interactive node
    SERVER1=cs8-6.got.volvocars.net
    # last node in cs8 hostgroup
    SERVER2=cs8-172.got.volvocars.net
fi


# statistics file
statistics=/vcc/cads/cads4/Fieldtest/scripts/cadscopy2/statistics/disk_uploads.log

#Exclude list
exclude="lost\+found|recycle|system\ volume\ information|.Trash*"
umask 007
# user to copy with
user=bppcads4
group=cads
self=$0
#number of mounts
nr=10
ran=$(( $RANDOM % nr ))
until [ -d /d/"$ran"/Fieldtest ]
do
  ran=$(( $RANDOM % nr ))
done
station=$(uname -n)
device=${DEVNAME::-1}
if [[ $device == /dev/sd ]]; then
        device=$DEVNAME
fi
part=$(blkid $device[123]|tail -1|cut -d":" -f1)
if [[ -z $part ]]; then
        # probably disk formatted without partitions!
        part=$(blkid $device|tail -1|cut -d":" -f1)
fi

drive=$part
serial=$ID_SERIAL_SHORT
mountdir="/s/$serial"
sourcedir="$mountdir/"
dirdate=`date +%Y%m%d`
date=`date +%y%m%d-%H%M`
cadsroot=/d/"$ran"/Fieldtest/temp/dump
workdir=/vcc/cads/cads4/Fieldtest/scripts/cadscopy2/workdir/
[[ -z $temparea ]]&&temparea="$cadsroot/$dirdate/$RANDOM/"
destdir="$temparea"/"$station"_"$serial"
logfile="$temparea"/"$station"_"$serial"_"$date".log
usbportm=$(echo -n "$station"_;echo $DEVPATH|/usr/bin/awk -F"/" ' { print $5"_"$6 } ')
#port mapping
[[ $usbportm == asupload1_usb*_*-1 ]]&&usbport="pv16_port1"
[[ $usbportm == asupload1_usb*_*-2 ]]&&usbport="pv16_port2"
[[ $usbportm == asupload1_usb*_*-3 ]]&&usbport="pv16_port3"
[[ $usbportm == asupload1_usb*_*-4 ]]&&usbport="pv16_port4"
[[ $usbportm == asupload2_usb*_*-1 ]]&&usbport="pv16_port5"
[[ $usbportm == asupload2_usb*_*-2 ]]&&usbport="pv16_port6"
[[ $usbportm == asupload2_usb*_*-3 ]]&&usbport="pv16_port7"
[[ $usbportm == asupload2_usb*_*-4 ]]&&usbport="pv16_port8"
[[ $usbportm == asupload3_usb*_*-1 ]]&&usbport="pv16_port9"
[[ $usbportm == asupload3_usb*_*-2 ]]&&usbport="pv16_port10"
[[ $usbportm == asupload3_usb*_*-3 ]]&&usbport="pv16_port11"
[[ $usbportm == asupload3_usb*_*-4 ]]&&usbport="pv16_port12"
[[ $usbportm == asupload4_usb*_*-1 ]]&&usbport="pv16_port13"
[[ $usbportm == asupload4_usb*_*-2 ]]&&usbport="pv16_port14"
[[ $usbportm == asupload4_usb*_*-3 ]]&&usbport="pv16_port15"
[[ $usbportm == asupload4_usb*_*-4 ]]&&usbport="pv16_port16"
[[ $usbportm == asupload5_usb*_*-1 ]]&&usbport="pv16_port17"
[[ $usbportm == asupload5_usb*_*-2 ]]&&usbport="pv16_port18"
[[ $usbportm == asupload5_usb*_*-3 ]]&&usbport="pv16_port19"
[[ $usbportm == asupload5_usb*_*-4 ]]&&usbport="pv16_port20"
# port 12 moved to mol4 room
# have not checked what port is connected. therefore only *
[[ $usbportm == asupload6_usb*_*-1 ]]&&usbport="mol4_port21"
[[ $usbportm == asupload6_usb*_*-2 ]]&&usbport="mol4_port22"
[[ $usbportm == asupload6_usb*_*-3 ]]&&usbport="mol4_port23"
[[ $usbportm == asupload6_usb*_*-4 ]]&&usbport="mol4_port24"
[[ $usbportm == asupload6_usb*_*-5 ]]&&usbport="mol4_port25"
[[ $usbportm == asupload6_usb*_*-6 ]]&&usbport="mol4_port26"
[[ $usbportm == asupload6_usb*_*-7 ]]&&usbport="mol4_port27"
[[ $usbportm == asupload6_usb*_*-8 ]]&&usbport="mol4_port28"
# china upload stations below
# asl stands for "Active Safety Lab"
[[ $usbportm == asuplchn1_usb*_*-1 ]]&&usbport="asl_port29"
[[ $usbportm == asuplchn1_usb*_*-2 ]]&&usbport="asl_port30"
[[ $usbportm == asuplchn1_usb*_*-3 ]]&&usbport="asl_port31"
[[ $usbportm == asuplchn1_usb*_*-4 ]]&&usbport="asl_port32"

#logfile=/tmp/cadscopy.log

update_progress() {
        src_path=$1
        dest_path=$2
        # usb port file
        u_pid=$3

        while :; do

                sleep 10

                cp_pid=$(ps aux|grep $u_pid|grep -v grep)
                cp_process=$(ps aux | grep "$dest_path" | grep -v grep | head -1)
                if [[ -z $cp_process ]]; then
                        # copy process is gone
                        break
                elif [[ -n $cp_pid && -n $u_pid ]]; then
                        src_size=$(du -sm ${src_path}|awk '{print $1}')
                        dest_size=$(du -sm ${dest_path}|awk '{print $1}')
                else
                        break
                fi

                # update numbers
                echo "[${dest_size} MB out of ${src_size} MB copied] - Copy in progress $usbport" > $workdir/$usbport

        done
}

cadscopy(){
        destdir=$1
        logfile=$2
        echo "usbport $usbportm" >> $logfile
        echo "destdir $destdir" >> $logfile
        echo "sourcedir $sourcedir" >> $logfile
        echo "$workdir/$usbport" >> $logfile
        echo "Copy in progress $usbport" > $workdir/$usbport
        df -h >> $logfile
        date >> $logfile
        pushd $sourcedir 2>&1 >/dev/null
                rc_push=$?

                # if pushd is a success
                if [[ $rc_push -eq 0 ]]; then
                        #/bin/cp -vR --preserve=timestamp "$sourcedir"/. "$destdir"/ 1>> $logfile 2>> "$logfile".error
                        #exitcode=$?

                        #exclude="lost\+found|recycle|system\ volume\ information|.Trash*"
                        #tar --exclude='.Trash*' --exclude='lost+found' --exclude='*RECYCLE.BIN' \
                        #       -c '.' 2>> "$logfile".error | tar -C "$destdir"/ -xv 1>> $logfile 2>> "$logfile".error &

                        # destdir /d/9/Fieldtest/temp/dump/20170904/28459//asupload6_V2JC254FE699EQRO49

                        # if Gothenburg
                        if [[ -n $CHECK_SCP ]]; then
                                new_destdir=${destdir:4}
                                ping_test=$(ping -w 1 -c 1 ${SERVER1}| grep bytes\ from)
                                if [[ -n $ping_test ]]; then
                                        scp -o CheckHostIP=No -o StrictHostKeyChecking=No -vrp \
                                                "$sourcedir"/. bppcads4@${SERVER1}:/vcc/cads/cads4/$new_destdir 1>> $logfile 2>> "$logfile".error &
                                        copy_pid=$!
                                else
                                        scp -o CheckHostIP=No -o StrictHostKeyChecking=No -vrp \
                                                "$sourcedir"/. bppcads4@${SERVER2}:/vcc/cads/cads4/$new_destdir 1>> $logfile 2>> "$logfile".error &
                                        copy_pid=$!
                                fi
                        else
                                /bin/cp -vR --preserve=timestamp "$sourcedir"/. "$destdir"/ 1>> $logfile 2>> "$logfile".error &
                                copy_pid=$!
                        fi
                        update_progress "${sourcedir}" "$destdir" "$copy_pid"
                        if [[ ! -s "$logfile".error ]]; then
                                # if empty then exit code is ok
                                exitcode=0
                        else
                                exitcode=1
                        fi
                else
                        # pushd (cd) did not work ... have to bail
                        echo ERROR: could not cd to $sourcedir !!! >> $logfile
                        echo ERROR: therefore no copy was made !!! >> $logfile
                        exitcode=1
                fi
        popd 2>&1 >/dev/null
        echo "" >> $logfile
        echo "Exited with exit code $exitcode" >> $logfile
}

clean(){
        echo ""
        echo "cleaning up" >> $logfile
        echo "cleanup on $usbport in progress" > $workdir""$usbport
        exitcode=$(awk ' /Exited/ { print $5 } ' $logfile )
        date >> $logfile
        echo "Cleaning $sourcedir exitcode=$exitcode" >> $logfile
        ##[[ x"$exitcode" = "x0" ]]&&/bin/rm -rfv $sourcedir/* >> $logfile
        #[[ $(cat $sourcedir/*error|grep -Evi "$exclude"|wc -l) = "0" ]]&&clean="and cleanup is ok"&&/bin/rm -rfv $sourcedir/* >> $logfile||clean="and no cleanup"

# remember china upload station
# make sure it is working before enabling this
#       if [[ $exitcode -eq 0 ]]; then
#                       pushd $sourcedir >/dev/null 2>&1
#               push_rc=$?
#               if [[ $cd_rc -eq 0 ]]; then
#                       /bin/rm -rfv $sourcedir/* >> $logfile 2>&1
#                       # do not forget hidden folders....
#                       /bin/rm -rfv $sourcedir/.* >> $logfile 2>&1
#               fi
#               popd >/dev/null 2>&1
#               rm_exit=$?
#               if [[ $rm_exit -eq 0 ]]; then
#                       clean="and cleanup is ok"
#               else
#                       clean="and something wrong with cleanup"
#               fi
#       else
#               clean="and no cleanup"
#       fi
        clean="and no cleanup"
        echo "done $clean" >> $logfile
        echo "Copy is done $clean on $usbport ready to remove" > $workdir""$usbport
        mv $temparea/stage1_in_progress $temparea/done
}

case "$1" in
        add)
          # am I already copying? Bail if so ...

          [[ $(/sbin/blkid $drive|grep ntfs) ]]&&scan='/bin/ntfsfix'||scan='/sbin/fsck -aV'
          su $user -c "[[ ! -d $destdir ]]&&mkdir -p $destdir"
          su $user -c "echo \"Device and serialnumber\" >> $temparea/stage1_in_progress"
          echo "$drive $serial" >> $temparea/stage1_in_progress
          echo "" >> $temparea/stage1_in_progress
          /usr/sbin/smartctl -H $drive|grep SMART >> $temparea/stage1_in_progress
          echo "" >> $temparea/stage1_in_progress
          $scan $drive >> $temparea/stage1_in_progress

          # am I already mounted ?
          am_mounted=$(mount|grep $mountdir|wc -l)
          if [[ $am_mounted -eq 0 ]]; then
                # not mounted

                if [[ ! -d $mountdir ]]; then
                        mkdir $mountdir
                        /bin/chown -vR $user:$group $mountdir >> $logfile
                fi
                mount $drive $mountdir
                /bin/chown -R $user:$group $sourcedir >> $logfile

                copy_start_time=$(date +%Y%m%d-%H%M)
                [[ x"$?" == x0 ]]&&su $user -c "$self copy $destdir $logfile"
                copy_stop_time=$(date +%Y%m%d-%H%M)
                clean
                # log statistics
                data_size=$(du -sm $destdir | awk '{print $1}')
                if [[ -f $statistics ]]; then
                        echo "${copy_start_time}:${copy_stop_time}:${station}:${usbport}:${serial}:${data_size}" >> $statistics
                fi
                # umount disk
                umount $sourcedir
          else
                # am mounted
                echo "ERROR: disk $mountdir is already mounted on ${usbport}" >> $logfile
                echo "DATE: $(date)" >> $logfile
                echo "MOUNT: $(mount)" >> $logfile
                echo "ERROR: disk $mountdir is already mounted on ${usbport}, (contact support)" > $workdir""$usbport
          fi
        ;;

        copy)
          cadscopy $2 $3
        ;;

        remove)
          /bin/rm "$workdir""$usbport"
          umount $mountdir
        ;;

        dispatch)
          echo $self $ACTION $drive $ID_SERIAL_SHORT|/usr/bin/at now
        ;;
esac