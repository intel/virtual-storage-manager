#!/bin/bash

cat /etc/vsmdeploy/deployrc |grep -e "^ADMIN_PASSWORD" |awk -F "=" '{print $2}' 
