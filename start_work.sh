#!/usr/bin/env bash

echo "*** Source py3env/bin/activate ... "

source ../py3env/bin/activate

here=`pwd`

ulimit -n 4096

export LANG=zh_CN.UTF-8
#nohup   python app.py --host 0.0.0.0 --port 8081  &
         python app.py --host 0.0.0.0 --port 8081  # port 8080 will not work correctly for some proxy reason.

echo "*** Start finished ... "
