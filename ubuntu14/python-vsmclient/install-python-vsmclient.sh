#!/bin/bash
#
# Small script to install python-vsmclient to local filesystem

VSMCLIENT_ROOT_PATH=debian/python-vsmclient

python setup.py install -O1 --skip-build --root $VSMCLIENT_ROOT_PATH

#---------------------------
# usr/share/doc
#---------------------------
install -g root -o root -v -m 640 -d $VSMCLIENT_ROOT_PATH/usr/share/doc/python-vsmclient-2015.03
install -g root -o root -v -m 640 -t $VSMCLIENT_ROOT_PATH/usr/share/doc/python-vsmclient-2015.03 LICENSE
