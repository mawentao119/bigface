#!/usr/bin/env bash

echo "*** Source py3env/bin/activate ... "

source ../py3env/bin/activate

here=`pwd`

ulimit -n 4096

#nohup   python davinci.py runserver -h 0.0.0.0 -p 8080  &
         python davinci.py runserver -h 0.0.0.0 -p 8080

echo "*** Start finished ... "
