#!/bin/bash
# Author: Rickard Math
# Reason for script: check README

con=/dev/tty1
/usr/bin/setterm --blank 0 --powerdown 0 --powersave off

while true
do
  clear > $con
  echo "Active Saftey disk dump monitoring console." 1> $con
  echo "" 1> $con
  [[ ! $(ls -1 /vcc/cads/cads4/Fieldtest/scripts/cadscopy2/workdir/) ]]&&echo "no drives in use" 1> $con
  cat /vcc/cads/cads4/Fieldtest/scripts/cadscopy2/workdir/* 1> $con 2>/dev/null
  sleep 10
done
