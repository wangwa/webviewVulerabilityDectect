#!/bin/bash

echo "start wangwa services."

filepath=`dirname $0`
cd ${filepath}
echo "current path ${filepath}"
sh ./bi/service_ctl.sh start

echo "end wangwa services."

#mod by peter
