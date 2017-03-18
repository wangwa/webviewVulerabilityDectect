#!/bin/bash

echo "start focus services."

filepath=`dirname $0`
cd ${filepath}
echo "current path ${filepath}"
sh ./bi/service_ctl.sh start

echo "end focus services."
