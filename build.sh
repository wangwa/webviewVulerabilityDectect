#!/bin/bash

FOCUS_VERSION=$1
if [ x${FOCUS_VERSION} = x ]
then
    echo "Pls input focus version!!!"
    exit 1
fi

echo "version input is ${FOCUS_VERSION}"

filepath=`dirname $0`

cd ${filepath}

chmod +x services_ctl.sh

docker build -t openscanner/wangwa:${FOCUS_VERSION} .

cd -

#mod by peter
