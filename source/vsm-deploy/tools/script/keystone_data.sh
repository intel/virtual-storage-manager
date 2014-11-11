#!/bin/bash

# Copyright 2014 Intel Corporation, All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the"License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

set -e
set -o xtrace

export OS_USERNAME=""
export OS_AUTH_KEY=""
export OS_AUTH_TENANT=""
export OS_STRATEGY=""
export OS_AUTH_STRATEGY=""
export OS_AUTH_URL=""
export SERVICE_ENDPOINT=""

export SERVICE_TOKEN=%SERVICE_TOKEN%
export ADMIN_PASSWORD=%ADMIN_PASSWORD%
export SERVICE_TENANT_NAME=%SERVICE_TENANT_NAME%
export KEYSTONE_HOST=%KEYSTONE_HOST%
export SERVICE_ENDPOINT=%SERVICE_ENDPOINT%
export KEYSTONE_CATALOG_BACKEND=%KEYSTONE_CATALOG_BACKEND%
export AGENT_PASSWORD=%AGENT_PASSWORD%

keyrc=~/keyrc

function get_id () {
    echo `"$@" | awk '/ id / { print $4 }'`
}

# Tenants
# -------

ADMIN_TENANT=$(get_id keystone tenant-create --name=admin)
echo "export ADMIN_TENANT=$ADMIN_TENANT" >> $keyrc

SERVICE_TENANT=$(get_id keystone tenant-create --name=$SERVICE_TENANT_NAME)
echo "export SERVICE_TENANT=$SERVICE_TENANT" >> $keyrc

DEMO_TENANT=$(get_id keystone tenant-create --name=demo)
echo "export DEMO_TENANT=$DEMO_TENANT" >> $keyrc

AGENT_TENANT=$(get_id keystone tenant-create --name=agent)
echo "export AGENT_TENANT=$AGENT_TENANT" >> $keyrc

INVIS_TENANT=$(get_id keystone tenant-create --name=invisible_to_admin)

# Users
# -----

ADMIN_USER=$(get_id keystone user-create --name=admin \
                                         --pass="$ADMIN_PASSWORD" \
                                         --email=admin@intel.com)
DEMO_USER=$(get_id keystone user-create --name=demo \
                                        --pass="$ADMIN_PASSWORD" \
                                        --email=demo@intel.com)

AGENT_USER=$(get_id keystone user-create --name=agent \
                                        --pass="$AGENT_PASSWORD" \
                                        --email=agent@intel.com)

# Roles
# -----

ADMIN_ROLE=$(get_id keystone role-create --name=admin)
echo "export ADMIN_ROLE=$ADMIN_ROLE" >> $keyrc

AGENT_ROLE=$(get_id keystone role-create --name=agent)
echo "export AGENT_ROLE=$AGENT_ROLE" >> $keyrc

KEYSTONEADMIN_ROLE=$(get_id keystone role-create --name=KeystoneAdmin)
echo "export KEYSTONEADMIN_ROLE=$KEYSTONEADMIN_ROLE" >> $keyrc

KEYSTONESERVICE_ROLE=$(get_id keystone role-create --name=KeystoneServiceAdmin)
# ANOTHER_ROLE demonstrates that an arbitrary role may be created and used
# TODO(sleepsonthefloor): show how this can be used for rbac in the future!
ANOTHER_ROLE=$(get_id keystone role-create --name=anotherrole)

# Add Roles to Users in Tenants
keystone user-role-add --user_id $ADMIN_USER --role_id $ADMIN_ROLE --tenant_id $ADMIN_TENANT
keystone user-role-add --user_id $ADMIN_USER --role_id $ADMIN_ROLE --tenant_id $DEMO_TENANT
keystone user-role-add --user_id $DEMO_USER --role_id $ANOTHER_ROLE --tenant_id $DEMO_TENANT
keystone user-role-add --user_id $AGENT_USER --role_id $AGENT_ROLE --tenant_id $AGENT_TENANT

# TODO(termie): these two might be dubious
keystone user-role-add --user_id $ADMIN_USER --role_id $KEYSTONEADMIN_ROLE --tenant_id $ADMIN_TENANT
keystone user-role-add --user_id $ADMIN_USER --role_id $KEYSTONESERVICE_ROLE --tenant_id $ADMIN_TENANT

# The Member role is used by Horizon and Swift so we need to keep it:
MEMBER_ROLE=$(get_id keystone role-create --name=Member)
keystone user-role-add --user_id $DEMO_USER --role_id $MEMBER_ROLE --tenant_id $DEMO_TENANT
keystone user-role-add --user_id $DEMO_USER --role_id $MEMBER_ROLE --tenant_id $INVIS_TENANT

# Services
# --------

KEYSTONE_SERVICE=$(get_id keystone service-create \
	--name=keystone \
	--type=identity \
	--description="Keystone Identity Service")
keystone endpoint-create \
    --region RegionOne \
	--service_id $KEYSTONE_SERVICE \
	--publicurl "http://$KEYSTONE_HOST:\$(public_port)s/v2.0" \
	--adminurl "http://$KEYSTONE_HOST:\$(admin_port)s/v2.0" \
	--internalurl "http://$KEYSTONE_HOST:\$(admin_port)s/v2.0"

set +o xtrace
