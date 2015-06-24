# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Implementation of SQLAlchemy backend."""

import json
import datetime
import uuid
import warnings
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, joinedload_all
from sqlalchemy.sql.expression import literal_column
from sqlalchemy.sql.expression import desc
from sqlalchemy.sql import func

from vsm.common import sqlalchemyutils
from vsm import db
from vsm.db.sqlalchemy import models
from vsm.db.sqlalchemy.session import get_session
from vsm import exception
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.openstack.common import timeutils
from vsm.openstack.common import uuidutils
from vsm.openstack.common.db import exception as db_exc

FLAGS = flags.FLAGS

LOG = logging.getLogger(__name__)

def is_admin_context(context):
    """Indicates if the request context is an administrator."""
    if not context:
        warnings.warn(_('Use of empty request context is deprecated'),
                      DeprecationWarning)
        raise Exception('die')
    return context.is_admin

def is_user_context(context):
    """Indicates if the request context is a normal user."""
    if not context:
        return False
    if context.is_admin:
        return False
    if not context.user_id or not context.project_id:
        return False
    return True

def authorize_project_context(context, project_id):
    """Ensures a request has permission to access the given project."""
    if is_user_context(context):
        if not context.project_id:
            raise exception.NotAuthorized()
        elif context.project_id != project_id:
            raise exception.NotAuthorized()

def authorize_user_context(context, user_id):
    """Ensures a request has permission to access the given user."""
    if is_user_context(context):
        if not context.user_id:
            raise exception.NotAuthorized()
        elif context.user_id != user_id:
            raise exception.NotAuthorized()

def authorize_quota_class_context(context, class_name):
    """Ensures a request has permission to access the given quota class."""
    if is_user_context(context):
        if not context.quota_class:
            raise exception.NotAuthorized()
        elif context.quota_class != class_name:
            raise exception.NotAuthorized()

def require_admin_context(f):
    """Decorator to require admin request context.

    The first argument to the wrapped function must be the context.

    """

    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]):
            raise exception.AdminRequired()
        return f(*args, **kwargs)
    return wrapper

def require_context(f):
    """Decorator to require *any* user or admin context.

    This does no authorization for user or project access matching, see
    :py:func:`authorize_project_context` and
    :py:func:`authorize_user_context`.

    The first argument to the wrapped function must be the context.

    """

    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]) and not is_user_context(args[0]):
            raise exception.NotAuthorized()
        return f(*args, **kwargs)
    return wrapper

def require_storage_exists(f):
    """Decorator to require the specified storage to exist.

    Requires the wrapped function to use context and storage_id as
    their first two arguments.
    """

    def wrapper(context, storage_id, *args, **kwargs):
        db.storage_get(context, storage_id)
        return f(context, storage_id, *args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def require_snapshot_exists(f):
    """Decorator to require the specified snapshot to exist.

    Requires the wrapped function to use context and snapshot_id as
    their first two arguments.
    """

    def wrapper(context, snapshot_id, *args, **kwargs):
        db.api.snapshot_get(context, snapshot_id)
        return f(context, snapshot_id, *args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def model_query(context, *args, **kwargs):
    """Query helper that accounts for context's `read_deleted` field.

    :param context: context to query under
    :param session: if present, the session to use
    :param read_deleted: if present, overrides context's read_deleted field.
    :param project_only: if present and context is user-type, then restrict
            query to match the context's project_id.
    """
    session = kwargs.get('session') or get_session()
    read_deleted = kwargs.get('read_deleted') or context.read_deleted
    project_only = kwargs.get('project_only')

    query = session.query(*args)

    if read_deleted == 'no':
        query = query.filter_by(deleted=False)
    elif read_deleted == 'yes':
        pass  # omit the filter to include deleted and active
    elif read_deleted == 'only':
        query = query.filter_by(deleted=True)
    else:
        raise Exception(
            _("Unrecognized read_deleted value '%s'") % read_deleted)

    if project_only and is_user_context(context):
        query = query.filter_by(project_id=context.project_id)

    return query

def exact_filter(query, model, filters, legal_keys):
    """Applies exact match filtering to a query.

    Returns the updated query.  Modifies filters argument to remove
    filters consumed.

    :param query: query to apply filters to
    :param model: model object the query applies to, for IN-style
                  filtering
    :param filters: dictionary of filters; values that are lists,
                    tuples, sets, or frozensets cause an 'IN' test to
                    be performed, while exact matching ('==' operator)
                    is used for other values
    :param legal_keys: list of keys to apply exact filtering to
    """

    filter_dict = {}

    # Walk through all the keys
    for key in legal_keys:
        # Skip ones we're not filtering on
        if key not in filters:
            continue

        # OK, filtering on this key; what value do we search for?
        value = filters.pop(key)

        if isinstance(value, (list, tuple, set, frozenset)):
            # Looking for values in a list; apply to query directly
            column_attr = getattr(model, key)
            query = query.filter(column_attr.in_(value))
        else:
            # OK, simple exact match; save for later
            filter_dict[key] = value

    # Apply simple exact matches
    if filter_dict:
        query = query.filter_by(**filter_dict)

    return query

@require_admin_context
def service_destroy(context, service_id):
    session = get_session()
    with session.begin():
        service_ref = service_get(context, service_id, session=session)
        service_ref.delete(session=session)

@require_admin_context
def service_get(context, service_id, session=None):
    result = model_query(
        context,
        models.Service,
        session=session).\
        filter_by(id=service_id).\
        first()
    if not result:
        raise exception.ServiceNotFound(service_id=service_id)

    return result

@require_admin_context
def service_get_all(context, disabled=None):
    query = model_query(context, models.Service)
    if disabled is not None:
        query = query.filter_by(disabled=disabled)

    return query.all()

@require_admin_context
def service_get_all_by_topic(context, topic):
    return model_query(
        context, models.Service, read_deleted="no").\
        filter_by(disabled=False).\
        filter_by(topic=topic).\
        all()

@require_admin_context
def service_get_by_host_and_topic(context, host, topic):
    result = model_query(
        context, models.Service, read_deleted="no").\
        filter_by(disabled=False).\
        filter_by(host=host).\
        filter_by(topic=topic).\
        first()
    if not result:
        raise exception.ServiceNotFound(service_id=None)
    return result

@require_admin_context
def service_get_all_by_host(context, host):
    return model_query(
        context, models.Service, read_deleted="no").\
        filter_by(host=host).\
        all()

@require_admin_context
def service_get_all_bmc_by_host(context, host):
    result = model_query(context, models.Service, read_deleted="no").\
                options(joinedload('compute_node')).\
                filter_by(host=host).\
                filter_by(topic="vsm-bmc").\
                all()

    if not result:
        raise exception.VsmHostNotFound(host=host)

    return result
@require_admin_context
def service_get_by_device(context, host):
    result = model_query(context, models.Service, read_deleted="no").\
                options(joinedload('compute_node')).\
                filter_by(host=host).\
                filter_by(topic="vsm-bmc").\
                all()

    if not result:
        raise exception.VsmHostNotFound(host=host)

    return result

@require_admin_context
def _service_get_all_topic_subquery(context, session, topic, subq, label):
    sort_value = getattr(subq.c, label)
    return model_query(context, models.Service,
                       func.coalesce(sort_value, 0),
                       session=session, read_deleted="no").\
        filter_by(topic=topic).\
        filter_by(disabled=False).\
        outerjoin((subq, models.Service.host == subq.c.host)).\
        order_by(sort_value).\
        all()

@require_admin_context
def service_get_all_storage_sorted(context):
    session = get_session()
    with session.begin():
        topic = FLAGS.storage_topic
        label = 'storage_gigabytes'
        subq = model_query(context, models.Hardware.host,
                           func.sum(models.Hardware.size).label(label),
                           session=session, read_deleted="no").\
            group_by(models.Hardware.host).\
            subquery()
        return _service_get_all_topic_subquery(context,
                                               session,
                                               topic,
                                               subq,
                                               label)

@require_admin_context
def service_get_by_args(context, host, binary):
    result = model_query(context, models.Service).\
        filter_by(host=host).\
        filter_by(binary=binary).\
        first()

    if not result:
        raise exception.HostBinaryNotFound(host=host, binary=binary)

    return result

@require_admin_context
def service_create(context, values):
    service_ref = models.Service()
    service_ref.update(values)
    if not FLAGS.enable_new_services:
        service_ref.disabled = True
    service_ref.save()
    return service_ref

@require_admin_context
def service_update(context, service_id, values):
    session = get_session()
    with session.begin():
        service_ref = service_get(context, service_id, session=session)
        service_ref.update(values)
        service_ref.save(session=session)

###################
def convert_datetimes(values, *datetime_keys):
    for key in values:
        if key in datetime_keys and isinstance(values[key], basestring):
            values[key] = timeutils.parse_strtime(values[key])
    return values

@require_admin_context
def compute_node_get(context, compute_id, session=None):
    result = model_query(context, models.ComputeNode, session=session).\
                     filter_by(id=compute_id).\
                     first()

    if not result:
        raise exception.VsmHostNotFound(host=compute_id)

    return result

#@require_admin_context
def compute_node_get_all(context, session=None):
    return model_query(context, models.ComputeNode, session=session).\
                    options(joinedload('service')).\
                    all()

def _get_host_utilization(context, host, ram_mb, disk_gb):
    """Compute the current utilization of a given host."""
    instances = instance_get_all_by_host(context, host)
    vms = len(instances)
    free_ram_mb = ram_mb - FLAGS.reserved_host_memory_mb
    free_disk_gb = disk_gb - (FLAGS.reserved_host_disk_mb * 1024)

    work = 0
    for instance in instances:
        free_ram_mb -= instance.memory_mb
        free_disk_gb -= instance.root_gb
        free_disk_gb -= instance.ephemeral_gb
        if instance.vm_state in [vm_states.BUILDING, vm_states.REBUILDING,
                                 vm_states.MIGRATING, vm_states.RESIZING]:
            work += 1
    return dict(free_ram_mb=free_ram_mb,
                free_disk_gb=free_disk_gb,
                current_workload=work,
                running_vms=vms)

def _adjust_compute_node_values_for_utilization(context, values, session):
    service_ref = service_get(context, values['service_id'], session=session)
    host = service_ref['host']
    ram_mb = values['memory_mb']
    disk_gb = values['local_gb']
    #values.update(_get_host_utilization(context, host, ram_mb, disk_gb))

@require_admin_context
def compute_node_create(context, values, session=None):
    """Creates a new ComputeNode and populates the capacity fields
    with the most recent data."""
    if not session:
        session = get_session()

    _adjust_compute_node_values_for_utilization(context, values, session)
    with session.begin(subtransactions=True):
        compute_node_ref = models.ComputeNode()
        session.add(compute_node_ref)
        compute_node_ref.update(values)
    return compute_node_ref

@require_admin_context
def compute_node_update(context, compute_id, values, auto_adjust):
    """Creates a new ComputeNode and populates the capacity fields
    with the most recent data."""
    session = get_session()
    if auto_adjust:
        _adjust_compute_node_values_for_utilization(context, values, session)
    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        compute_ref = compute_node_get(context, compute_id, session=session)
        for (key, value) in values.iteritems():
            compute_ref[key] = value
        compute_ref.save(session=session)

def compute_node_get_by_host(context, host):
    """Get all capacity entries for the given host."""
    session = get_session()
    with session.begin():
        service = session.query(models.Service).\
                            filter_by(host=host, binary="vsm-bmc").first()
        node = session.query(models.ComputeNode).\
                             options(joinedload('service')).\
                             filter_by(deleted=False,service_id=service.id)
        return node.first()

def compute_node_utilization_update(context, host, free_ram_mb_delta=0,
                          free_disk_gb_delta=0, work_delta=0, vm_delta=0):
    """Update a specific ComputeNode entry by a series of deltas.
    Do this as a single atomic action and lock the row for the
    duration of the operation. Requires that ComputeNode record exist."""
    session = get_session()
    compute_node = None
    with session.begin(subtransactions=True):
        compute_node = session.query(models.ComputeNode).\
                              options(joinedload('service')).\
                              filter(models.Service.host == host).\
                              filter_by(deleted=False).\
                              with_lockmode('update').\
                              first()
        if compute_node is None:
            raise exception.NotFound(_("No ComputeNode for %(host)s") %
                                     locals())

        # This table thingy is how we get atomic UPDATE x = x + 1
        # semantics.
        table = models.ComputeNode.__table__
        if free_ram_mb_delta != 0:
            compute_node.free_ram_mb = table.c.free_ram_mb + free_ram_mb_delta
        if free_disk_gb_delta != 0:
            compute_node.free_disk_gb = (table.c.free_disk_gb +
                                         free_disk_gb_delta)
        if work_delta != 0:
            compute_node.current_workload = (table.c.current_workload +
                                             work_delta)
        if vm_delta != 0:
            compute_node.running_vms = table.c.running_vms + vm_delta
    return compute_node

def compute_node_utilization_set(context, host, free_ram_mb=None,
                                 free_disk_gb=None, work=None, vms=None):
    """Like compute_node_utilization_update() modify a specific host
    entry. But this function will set the metrics absolutely
    (vs. a delta update).
    """
    session = get_session()
    compute_node = None
    with session.begin(subtransactions=True):
        compute_node = session.query(models.ComputeNode).\
                              options(joinedload('service')).\
                              filter(models.Service.host == host).\
                              filter_by(deleted=False).\
                              with_lockmode('update').\
                              first()
        if compute_node is None:
            raise exception.NotFound(_("No ComputeNode for %(host)s") %
                                     locals())

        if free_ram_mb != None:
            compute_node.free_ram_mb = free_ram_mb
        if free_disk_gb != None:
            compute_node.free_disk_gb = free_disk_gb
        if work != None:
            compute_node.current_workload = work
        if vms != None:
            compute_node.running_vms = vms

    return compute_node

###################
# Standby Table
@require_admin_context
def standby_service_create(context, values, session=None):
    """Creates a new standby service  ."""
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        standbyServiceRef = models.StandbyService()
        session.add(standbyServiceRef)
        standbyServiceRef.update(values)
        standbyServiceRef.save(session=session)

    return standbyServiceRef

@require_admin_context
def standby_service_get_by_hostname(context, host_name, session=None):
    """get a standby service  ."""
    if not session:
        session = get_session()

    with session.begin():
        result = session.query(models.StandbyService).\
                             filter(models.StandbyService.host_name == host_name).\
                             filter_by(deleted=False)
        return result.first()

@require_admin_context
def standby_service_get_all(context, session=None):
    result = model_query(context, models.StandbyService, session=session).all()
    if not result:
        raise exception.ServiceNotFound("")
    return result

@require_admin_context
def standby_service_update(context, host_name, values, session=None):
    """update a standby service ."""
    session = get_session()
    values['updated_at'] = timeutils.utcnow()
    convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')

    with session.begin():
        result = session.query(models.StandbyService).\
                             filter(models.StandbyService.host_name == host_name).\
                             filter_by(deleted=False)
        standbyServiceRef = result.first()
        standbyServiceRef.update(values)
        standbyServiceRef.save(session=session)

@require_admin_context
def standby_setting_get_by_id(context, id, session=None):
    """get standby setting by id"""
    result = model_query(context, models.StandbySetting, session=session).\
            filter_by(id=id).first()
    if not result:
        raise exception.NotFound("setting")

    return result

@require_admin_context
def standby_setting_update_by_id(context, id, data, session=None):
    """get standby setting by id"""
    session = get_session()
    with session.begin():
        result = model_query(context, models.StandbySetting, session=session).\
                filter_by(id=id).first()
        if not result:
            raise exception.NotFound("setting")
        result.update(data)
        result.save(session=session)

    return result
###################

def _metadata_refs(metadata_dict, meta_class):
    metadata_refs = []
    if metadata_dict:
        for k, v in metadata_dict.iteritems():
            metadata_ref = meta_class()
            metadata_ref['key'] = k
            metadata_ref['value'] = v
            metadata_refs.append(metadata_ref)
    return metadata_refs

def _dict_with_extra_specs(inst_type_query):
    """Takes an instance, storage, or instance type query returned
    by sqlalchemy and returns it as a dictionary, converting the
    extra_specs entry from a list of dicts:

    'extra_specs' : [{'key': 'k1', 'value': 'v1', ...}, ...]

    to a single dict:

    'extra_specs' : {'k1': 'v1'}

    """
    inst_type_dict = dict(inst_type_query)
    extra_specs = dict([(x['key'], x['value'])
                        for x in inst_type_query['extra_specs']])
    inst_type_dict['extra_specs'] = extra_specs
    return inst_type_dict

###################

@require_admin_context
def iscsi_target_count_by_host(context, host):
    return model_query(context, models.IscsiTarget).\
        filter_by(host=host).\
        count()

@require_admin_context
def iscsi_target_create_safe(context, values):
    iscsi_target_ref = models.IscsiTarget()

    for (key, value) in values.iteritems():
        iscsi_target_ref[key] = value
    try:
        iscsi_target_ref.save()
        return iscsi_target_ref
    except IntegrityError:
        return None

###################

@require_context
def quota_get(context, project_id, resource, session=None):
    result = model_query(context, models.Quota, session=session,
                         read_deleted="no").\
        filter_by(project_id=project_id).\
        filter_by(resource=resource).\
        first()

    if not result:
        raise exception.ProjectQuotaNotFound(project_id=project_id)

    return result

@require_context
def quota_get_all_by_project(context, project_id):
    authorize_project_context(context, project_id)

    rows = model_query(context, models.Quota, read_deleted="no").\
        filter_by(project_id=project_id).\
        all()

    result = {'project_id': project_id}
    for row in rows:
        result[row.resource] = row.hard_limit

    return result

@require_admin_context
def quota_create(context, project_id, resource, limit):
    quota_ref = models.Quota()
    quota_ref.project_id = project_id
    quota_ref.resource = resource
    quota_ref.hard_limit = limit
    quota_ref.save()
    return quota_ref

@require_admin_context
def quota_update(context, project_id, resource, limit):
    session = get_session()
    with session.begin():
        quota_ref = quota_get(context, project_id, resource, session=session)
        quota_ref.hard_limit = limit
        quota_ref.save(session=session)

@require_admin_context
def quota_destroy(context, project_id, resource):
    session = get_session()
    with session.begin():
        quota_ref = quota_get(context, project_id, resource, session=session)
        quota_ref.delete(session=session)

###################

@require_context
def quota_class_get(context, class_name, resource, session=None):
    result = model_query(context, models.QuotaClass, session=session,
                         read_deleted="no").\
        filter_by(class_name=class_name).\
        filter_by(resource=resource).\
        first()

    if not result:
        raise exception.QuotaClassNotFound(class_name=class_name)

    return result

@require_context
def quota_class_get_all_by_name(context, class_name):
    authorize_quota_class_context(context, class_name)

    rows = model_query(context, models.QuotaClass, read_deleted="no").\
        filter_by(class_name=class_name).\
        all()

    result = {'class_name': class_name}
    for row in rows:
        result[row.resource] = row.hard_limit

    return result

@require_admin_context
def quota_class_create(context, class_name, resource, limit):
    quota_class_ref = models.QuotaClass()
    quota_class_ref.class_name = class_name
    quota_class_ref.resource = resource
    quota_class_ref.hard_limit = limit
    quota_class_ref.save()
    return quota_class_ref

@require_admin_context
def quota_class_update(context, class_name, resource, limit):
    session = get_session()
    with session.begin():
        quota_class_ref = quota_class_get(context, class_name, resource,
                                          session=session)
        quota_class_ref.hard_limit = limit
        quota_class_ref.save(session=session)

@require_admin_context
def quota_class_destroy(context, class_name, resource):
    session = get_session()
    with session.begin():
        quota_class_ref = quota_class_get(context, class_name, resource,
                                          session=session)
        quota_class_ref.delete(session=session)

@require_admin_context
def quota_class_destroy_all_by_name(context, class_name):
    session = get_session()
    with session.begin():
        quota_classes = model_query(context, models.QuotaClass,
                                    session=session, read_deleted="no").\
            filter_by(class_name=class_name).\
            all()

        for quota_class_ref in quota_classes:
            quota_class_ref.delete(session=session)

###################

@require_context
def quota_usage_get(context, project_id, resource, session=None):
    result = model_query(context, models.QuotaUsage, session=session,
                         read_deleted="no").\
        filter_by(project_id=project_id).\
        filter_by(resource=resource).\
        first()

    if not result:
        raise exception.QuotaUsageNotFound(project_id=project_id)

    return result

@require_context
def quota_usage_get_all_by_project(context, project_id):
    authorize_project_context(context, project_id)

    rows = model_query(context, models.QuotaUsage, read_deleted="no").\
        filter_by(project_id=project_id).\
        all()

    result = {'project_id': project_id}
    for row in rows:
        result[row.resource] = dict(in_use=row.in_use, reserved=row.reserved)

    return result

@require_admin_context
def quota_usage_create(context, project_id, resource, in_use, reserved,
                       until_refresh, session=None):
    quota_usage_ref = models.QuotaUsage()
    quota_usage_ref.project_id = project_id
    quota_usage_ref.resource = resource
    quota_usage_ref.in_use = in_use
    quota_usage_ref.reserved = reserved
    quota_usage_ref.until_refresh = until_refresh
    quota_usage_ref.save(session=session)

    return quota_usage_ref

###################

@require_context
def reservation_get(context, uuid, session=None):
    result = model_query(context, models.Reservation, session=session,
                         read_deleted="no").\
        filter_by(uuid=uuid).first()

    if not result:
        raise exception.ReservationNotFound(uuid=uuid)

    return result

@require_context
def reservation_get_all_by_project(context, project_id):
    authorize_project_context(context, project_id)

    rows = model_query(context, models.Reservation, read_deleted="no").\
        filter_by(project_id=project_id).all()

    result = {'project_id': project_id}
    for row in rows:
        result.setdefault(row.resource, {})
        result[row.resource][row.uuid] = row.delta

    return result

@require_admin_context
def reservation_create(context, uuid, usage, project_id, resource, delta,
                       expire, session=None):
    reservation_ref = models.Reservation()
    reservation_ref.uuid = uuid
    reservation_ref.usage_id = usage['id']
    reservation_ref.project_id = project_id
    reservation_ref.resource = resource
    reservation_ref.delta = delta
    reservation_ref.expire = expire
    reservation_ref.save(session=session)
    return reservation_ref

@require_admin_context
def reservation_destroy(context, uuid):
    session = get_session()
    with session.begin():
        reservation_ref = reservation_get(context, uuid, session=session)
        reservation_ref.delete(session=session)

###################

# NOTE(johannes): The quota code uses SQL locking to ensure races don't
# cause under or over counting of resources. To avoid deadlocks, this
# code always acquires the lock on quota_usages before acquiring the lock
# on reservations.

def _get_quota_usages(context, session, project_id):
    # Broken out for testability
    rows = model_query(context, models.QuotaUsage,
                       read_deleted="no",
                       session=session).\
        filter_by(project_id=project_id).\
        with_lockmode('update').\
        all()
    return dict((row.resource, row) for row in rows)

@require_context
def quota_reserve(context, resources, quotas, deltas, expire,
                  until_refresh, max_age, project_id=None):
    elevated = context.elevated()
    session = get_session()
    with session.begin():
        if project_id is None:
            project_id = context.project_id

        # Get the current usages
        usages = _get_quota_usages(context, session, project_id)

        # Handle usage refresh
        work = set(deltas.keys())
        while work:
            resource = work.pop()

            # Do we need to refresh the usage?
            refresh = False
            if resource not in usages:
                usages[resource] = quota_usage_create(elevated,
                                                      project_id,
                                                      resource,
                                                      0, 0,
                                                      until_refresh or None,
                                                      session=session)
                refresh = True
            elif usages[resource].in_use < 0:
                # Negative in_use count indicates a desync, so try to
                # heal from that...
                refresh = True
            elif usages[resource].until_refresh is not None:
                usages[resource].until_refresh -= 1
                if usages[resource].until_refresh <= 0:
                    refresh = True
            elif max_age and (usages[resource].updated_at -
                              timeutils.utcnow()).seconds >= max_age:
                refresh = True

            # OK, refresh the usage
            if refresh:
                # Grab the sync routine
                sync = resources[resource].sync

                updates = sync(elevated, project_id, session)
                for res, in_use in updates.items():
                    # Make sure we have a destination for the usage!
                    if res not in usages:
                        usages[res] = quota_usage_create(elevated,
                                                         project_id,
                                                         res,
                                                         0, 0,
                                                         until_refresh or None,
                                                         session=session)

                    # Update the usage
                    usages[res].in_use = in_use
                    usages[res].until_refresh = until_refresh or None

                    # Because more than one resource may be refreshed
                    # by the call to the sync routine, and we don't
                    # want to double-sync, we make sure all refreshed
                    # resources are dropped from the work set.
                    work.discard(res)

                    # NOTE(Vek): We make the assumption that the sync
                    #            routine actually refreshes the
                    #            resources that it is the sync routine
                    #            for.  We don't check, because this is
                    #            a best-effort mechanism.

        # Check for deltas that would go negative
        unders = [resource for resource, delta in deltas.items()
                  if delta < 0 and
                  delta + usages[resource].in_use < 0]

        # Now, let's check the quotas
        # NOTE(Vek): We're only concerned about positive increments.
        #            If a project has gone over quota, we want them to
        #            be able to reduce their usage without any
        #            problems.
        overs = [resource for resource, delta in deltas.items()
                 if quotas[resource] >= 0 and delta >= 0 and
                 quotas[resource] < delta + usages[resource].total]

        # NOTE(Vek): The quota check needs to be in the transaction,
        #            but the transaction doesn't fail just because
        #            we're over quota, so the OverQuota raise is
        #            outside the transaction.  If we did the raise
        #            here, our usage updates would be discarded, but
        #            they're not invalidated by being over-quota.

        # Create the reservations
        if not overs:
            reservations = []
            for resource, delta in deltas.items():
                reservation = reservation_create(elevated,
                                                 str(uuid.uuid4()),
                                                 usages[resource],
                                                 project_id,
                                                 resource, delta, expire,
                                                 session=session)
                reservations.append(reservation.uuid)

                # Also update the reserved quantity
                # NOTE(Vek): Again, we are only concerned here about
                #            positive increments.  Here, though, we're
                #            worried about the following scenario:
                #
                #            1) User initiates resize down.
                #            2) User allocates a new instance.
                #            3) Resize down fails or is reverted.
                #            4) User is now over quota.
                #
                #            To prevent this, we only update the
                #            reserved value if the delta is positive.
                if delta > 0:
                    usages[resource].reserved += delta

        # Apply updates to the usages table
        for usage_ref in usages.values():
            usage_ref.save(session=session)

    if unders:
        LOG.warning(_("Change will make usage less than 0 for the following "
                      "resources: %(unders)s") % locals())
    if overs:
        usages = dict((k, dict(in_use=v['in_use'], reserved=v['reserved']))
                      for k, v in usages.items())
        raise exception.OverQuota(overs=sorted(overs), quotas=quotas,
                                  usages=usages)

    return reservations

def _quota_reservations(session, context, reservations):
    """Return the relevant reservations."""

    # Get the listed reservations
    return model_query(context, models.Reservation,
                       read_deleted="no",
                       session=session).\
        filter(models.Reservation.uuid.in_(reservations)).\
        with_lockmode('update').\
        all()

@require_context
def reservation_commit(context, reservations, project_id=None):
    session = get_session()
    with session.begin():
        usages = _get_quota_usages(context, session, project_id)

        for reservation in _quota_reservations(session, context, reservations):
            usage = usages[reservation.resource]
            if reservation.delta >= 0:
                usage.reserved -= reservation.delta
            usage.in_use += reservation.delta

            reservation.delete(session=session)

        for usage in usages.values():
            usage.save(session=session)

@require_context
def reservation_rollback(context, reservations, project_id=None):
    session = get_session()
    with session.begin():
        usages = _get_quota_usages(context, session, project_id)

        for reservation in _quota_reservations(session, context, reservations):
            usage = usages[reservation.resource]
            if reservation.delta >= 0:
                usage.reserved -= reservation.delta

            reservation.delete(session=session)

        for usage in usages.values():
            usage.save(session=session)

@require_admin_context
def quota_destroy_all_by_project(context, project_id):
    session = get_session()
    with session.begin():
        quotas = model_query(context, models.Quota, session=session,
                             read_deleted="no").\
            filter_by(project_id=project_id).\
            all()

        for quota_ref in quotas:
            quota_ref.delete(session=session)

        quota_usages = model_query(context, models.QuotaUsage,
                                   session=session, read_deleted="no").\
            filter_by(project_id=project_id).\
            all()

        for quota_usage_ref in quota_usages:
            quota_usage_ref.delete(session=session)

        reservations = model_query(context, models.Reservation,
                                   session=session, read_deleted="no").\
            filter_by(project_id=project_id).\
            all()

        for reservation_ref in reservations:
            reservation_ref.delete(session=session)

@require_admin_context
def reservation_expire(context):
    session = get_session()
    with session.begin():
        current_time = timeutils.utcnow()
        results = model_query(context, models.Reservation, session=session,
                              read_deleted="no").\
            filter(models.Reservation.expire < current_time).\
            all()

        if results:
            for reservation in results:
                if reservation.delta >= 0:
                    reservation.usage.reserved -= reservation.delta
                    reservation.usage.save(session=session)

                reservation.delete(session=session)

###################

@require_admin_context
def storage_allocate_iscsi_target(context, storage_id, host):
    session = get_session()
    with session.begin():
        iscsi_target_ref = model_query(context, models.IscsiTarget,
                                       session=session, read_deleted="no").\
            filter_by(storage=None).\
            filter_by(host=host).\
            with_lockmode('update').\
            first()

        # NOTE(vish): if with_lockmode isn't supported, as in sqlite,
        #             then this has concurrency issues
        if not iscsi_target_ref:
            raise db.NoMoreTargets()

        iscsi_target_ref.storage_id = storage_id
        session.add(iscsi_target_ref)

    return iscsi_target_ref.target_num

@require_admin_context
def storage_attached(context, storage_id, instance_uuid, mountpoint):
    if not uuidutils.is_uuid_like(instance_uuid):
        raise exception.InvalidUUID(uuid=instance_uuid)

    session = get_session()
    with session.begin():
        storage_ref = storage_get(context, storage_id, session=session)
        storage_ref['status'] = 'in-use'
        storage_ref['mountpoint'] = mountpoint
        storage_ref['attach_status'] = 'attached'
        storage_ref['instance_uuid'] = instance_uuid
        storage_ref.save(session=session)

@require_context
def storage_create(context, values):
    values['storage_metadata'] = _metadata_refs(values.get('metadata'),
                                               models.HardwareMetadata)
    storage_ref = models.Hardware()
    if not values.get('id'):
        values['id'] = str(uuid.uuid4())
    storage_ref.update(values)

    session = get_session()
    with session.begin():
        storage_ref.save(session=session)

    return storage_get(context, values['id'], session=session)

@require_admin_context
def storage_data_get_for_host(context, host, session=None):
    result = model_query(context,
                         func.count(models.Hardware.id),
                         func.sum(models.Hardware.size),
                         read_deleted="no",
                         session=session).\
        filter_by(host=host).\
        first()

    # NOTE(vish): convert None to 0
    return (result[0] or 0, result[1] or 0)

@require_admin_context
def storage_data_get_for_project(context, project_id, session=None):
    result = model_query(context,
                         func.count(models.Hardware.id),
                         func.sum(models.Hardware.size),
                         read_deleted="no",
                         session=session).\
        filter_by(project_id=project_id).\
        first()

    # NOTE(vish): convert None to 0
    return (result[0] or 0, result[1] or 0)

@require_admin_context
def storage_destroy(context, storage_id):
    session = get_session()
    with session.begin():
        session.query(models.Hardware).\
            filter_by(id=storage_id).\
            update({'status': 'deleted',
                    'deleted': True,
                    'deleted_at': timeutils.utcnow(),
                    'updated_at': literal_column('updated_at')})
        session.query(models.IscsiTarget).\
            filter_by(storage_id=storage_id).\
            update({'storage_id': None})
        session.query(models.HardwareMetadata).\
            filter_by(storage_id=storage_id).\
            update({'deleted': True,
                    'deleted_at': timeutils.utcnow(),
                    'updated_at': literal_column('updated_at')})

@require_admin_context
def storage_detached(context, storage_id):
    session = get_session()
    with session.begin():
        storage_ref = storage_get(context, storage_id, session=session)
        storage_ref['status'] = 'available'
        storage_ref['mountpoint'] = None
        storage_ref['attach_status'] = 'detached'
        storage_ref['instance_uuid'] = None
        storage_ref.save(session=session)

@require_context
def _storage_get_query(context, session=None, project_only=False):
    return model_query(context, models.Hardware, session=session,
                       project_only=project_only).\
        options(joinedload('storage_metadata')).\
        options(joinedload('storage_type'))

@require_context
def storage_get(context, storage_id, session=None):
    result = _storage_get_query(context, session=session, project_only=True).\
        filter_by(id=storage_id).\
        first()

    if not result:
        raise exception.HardwareNotFound(storage_id=storage_id)

    return result

@require_admin_context
def storage_get_all(context, marker, limit, sort_key, sort_dir):
    query = _storage_get_query(context)

    marker_storage = None
    if marker is not None:
        marker_storage = storage_get(context, marker)

    query = sqlalchemyutils.paginate_query(query, models.Hardware, limit,
                                           [sort_key, 'created_at', 'id'],
                                           marker=marker_storage,
                                           sort_dir=sort_dir)

    return query.all()

@require_admin_context
def storage_get_all_by_host(context, host):
    return _storage_get_query(context).filter_by(host=host).all()

@require_admin_context
def storage_get_all_by_instance_uuid(context, instance_uuid):
    result = model_query(context, models.Hardware, read_deleted="no").\
        options(joinedload('storage_metadata')).\
        options(joinedload('storage_type')).\
        filter_by(instance_uuid=instance_uuid).\
        all()

    if not result:
        return []

    return result

@require_context
def storage_get_all_by_project(context, project_id, marker, limit, sort_key,
                              sort_dir):
    authorize_project_context(context, project_id)
    query = _storage_get_query(context).filter_by(project_id=project_id)

    marker_storage = None
    if marker is not None:
        marker_storage = storage_get(context, marker)

    query = sqlalchemyutils.paginate_query(query, models.Hardware, limit,
                                           [sort_key, 'created_at', 'id'],
                                           marker=marker_storage,
                                           sort_dir=sort_dir)

    return query.all()

@require_admin_context
def storage_get_iscsi_target_num(context, storage_id):
    result = model_query(context, models.IscsiTarget, read_deleted="yes").\
        filter_by(storage_id=storage_id).\
        first()

    if not result:
        raise exception.ISCSITargetNotFoundForHardware(storage_id=storage_id)

    return result.target_num

@require_context
def storage_update(context, storage_id, values):
    session = get_session()
    metadata = values.get('metadata')
    if metadata is not None:
        storage_metadata_update(context,
                               storage_id,
                               values.pop('metadata'),
                               delete=True)
    with session.begin():
        storage_ref = storage_get(context, storage_id, session=session)
        storage_ref.update(values)
        storage_ref.save(session=session)
        return storage_ref

####################

def _storage_metadata_get_query(context, storage_id, session=None):
    return model_query(context, models.HardwareMetadata,
                       session=session, read_deleted="no").\
        filter_by(storage_id=storage_id)

@require_context
@require_storage_exists
def storage_metadata_get(context, storage_id):
    rows = _storage_metadata_get_query(context, storage_id).all()
    result = {}
    for row in rows:
        result[row['key']] = row['value']

    return result

@require_context
@require_storage_exists
def storage_metadata_delete(context, storage_id, key):
    _storage_metadata_get_query(context, storage_id).\
        filter_by(key=key).\
        update({'deleted': True,
                'deleted_at': timeutils.utcnow(),
                'updated_at': literal_column('updated_at')})

@require_context
@require_storage_exists
def storage_metadata_get_item(context, storage_id, key, session=None):
    result = _storage_metadata_get_query(context, storage_id, session=session).\
        filter_by(key=key).\
        first()

    if not result:
        raise exception.HardwareMetadataNotFound(metadata_key=key,
                                               storage_id=storage_id)
    return result

@require_context
@require_storage_exists
def storage_metadata_update(context, storage_id, metadata, delete):
    session = get_session()

    # Set existing metadata to deleted if delete argument is True
    if delete:
        original_metadata = storage_metadata_get(context, storage_id)
        for meta_key, meta_value in original_metadata.iteritems():
            if meta_key not in metadata:
                meta_ref = storage_metadata_get_item(context, storage_id,
                                                    meta_key, session)
                meta_ref.update({'deleted': True})
                meta_ref.save(session=session)

    meta_ref = None

    # Now update all existing items with new values, or create new meta objects
    for meta_key, meta_value in metadata.items():

        # update the value whether it exists or not
        item = {"value": meta_value}

        try:
            meta_ref = storage_metadata_get_item(context, storage_id,
                                                meta_key, session)
        except exception.HardwareMetadataNotFound as e:
            meta_ref = models.HardwareMetadata()
            item.update({"key": meta_key, "storage_id": storage_id})

        meta_ref.update(item)
        meta_ref.save(session=session)

    return metadata

###################

@require_context
def snapshot_create(context, values):
    values['snapshot_metadata'] = _metadata_refs(values.get('metadata'),
                                                 models.SnapshotMetadata)
    snapshot_ref = models.Snapshot()
    if not values.get('id'):
        values['id'] = str(uuid.uuid4())
    snapshot_ref.update(values)

    session = get_session()
    with session.begin():
        snapshot_ref.save(session=session)

    return snapshot_get(context, values['id'], session=session)

@require_admin_context
def snapshot_destroy(context, snapshot_id):
    session = get_session()
    with session.begin():
        session.query(models.Snapshot).\
            filter_by(id=snapshot_id).\
            update({'status': 'deleted',
                    'deleted': True,
                    'deleted_at': timeutils.utcnow(),
                    'updated_at': literal_column('updated_at')})

@require_context
def snapshot_get(context, snapshot_id, session=None):
    result = model_query(context, models.Snapshot, session=session,
                         project_only=True).\
        filter_by(id=snapshot_id).\
        first()

    if not result:
        raise exception.SnapshotNotFound(snapshot_id=snapshot_id)

    return result

@require_admin_context
def snapshot_get_all(context):
    return model_query(context, models.Snapshot).all()

@require_context
def snapshot_get_all_for_storage(context, storage_id):
    return model_query(context, models.Snapshot, read_deleted='no',
                       project_only=True).\
        filter_by(storage_id=storage_id).all()

@require_context
def snapshot_get_all_by_project(context, project_id):
    authorize_project_context(context, project_id)
    return model_query(context, models.Snapshot).\
        filter_by(project_id=project_id).\
        all()

@require_context
def snapshot_data_get_for_project(context, project_id, session=None):
    authorize_project_context(context, project_id)
    result = model_query(context,
                         func.count(models.Snapshot.id),
                         func.sum(models.Snapshot.storage_size),
                         read_deleted="no",
                         session=session).\
        filter_by(project_id=project_id).\
        first()

    # NOTE(vish): convert None to 0
    return (result[0] or 0, result[1] or 0)

@require_context
def snapshot_update(context, snapshot_id, values):
    session = get_session()
    with session.begin():
        snapshot_ref = snapshot_get(context, snapshot_id, session=session)
        snapshot_ref.update(values)
        snapshot_ref.save(session=session)

####################

def _snapshot_metadata_get_query(context, snapshot_id, session=None):
    return model_query(context, models.SnapshotMetadata,
                       session=session, read_deleted="no").\
        filter_by(snapshot_id=snapshot_id)

@require_context
@require_snapshot_exists
def snapshot_metadata_get(context, snapshot_id):
    rows = _snapshot_metadata_get_query(context, snapshot_id).all()
    result = {}
    for row in rows:
        result[row['key']] = row['value']

    return result

@require_context
@require_snapshot_exists
def snapshot_metadata_delete(context, snapshot_id, key):
    _snapshot_metadata_get_query(context, snapshot_id).\
        filter_by(key=key).\
        update({'deleted': True,
                'deleted_at': timeutils.utcnow(),
                'updated_at': literal_column('updated_at')})

@require_context
@require_snapshot_exists
def snapshot_metadata_get_item(context, snapshot_id, key, session=None):
    result = _snapshot_metadata_get_query(context,
                                          snapshot_id,
                                          session=session).\
        filter_by(key=key).\
        first()

    if not result:
        raise exception.SnapshotMetadataNotFound(metadata_key=key,
                                                 snapshot_id=snapshot_id)
    return result

@require_context
@require_snapshot_exists
def snapshot_metadata_update(context, snapshot_id, metadata, delete):
    session = get_session()

    # Set existing metadata to deleted if delete argument is True
    if delete:
        original_metadata = snapshot_metadata_get(context, snapshot_id)
        for meta_key, meta_value in original_metadata.iteritems():
            if meta_key not in metadata:
                meta_ref = snapshot_metadata_get_item(context, snapshot_id,
                                                      meta_key, session)
                meta_ref.update({'deleted': True})
                meta_ref.save(session=session)

    meta_ref = None

    # Now update all existing items with new values, or create new meta objects
    for meta_key, meta_value in metadata.items():

        # update the value whether it exists or not
        item = {"value": meta_value}

        try:
            meta_ref = snapshot_metadata_get_item(context, snapshot_id,
                                                  meta_key, session)
        except exception.SnapshotMetadataNotFound as e:
            meta_ref = models.SnapshotMetadata()
            item.update({"key": meta_key, "snapshot_id": snapshot_id})

        meta_ref.update(item)
        meta_ref.save(session=session)

    return metadata

###################

@require_admin_context
def migration_create(context, values):
    migration = models.Migration()
    migration.update(values)
    migration.save()
    return migration

@require_admin_context
def migration_update(context, id, values):
    session = get_session()
    with session.begin():
        migration = migration_get(context, id, session=session)
        migration.update(values)
        migration.save(session=session)
        return migration

@require_admin_context
def migration_get(context, id, session=None):
    result = model_query(context, models.Migration, session=session,
                         read_deleted="yes").\
        filter_by(id=id).\
        first()

    if not result:
        raise exception.MigrationNotFound(migration_id=id)

    return result

@require_admin_context
def migration_get_by_instance_and_status(context, instance_uuid, status):
    result = model_query(context, models.Migration, read_deleted="yes").\
        filter_by(instance_uuid=instance_uuid).\
        filter_by(status=status).\
        first()

    if not result:
        raise exception.MigrationNotFoundByStatus(instance_id=instance_uuid,
                                                  status=status)

    return result

@require_admin_context
def migration_get_all_unconfirmed(context, confirm_window, session=None):
    confirm_window = timeutils.utcnow() - datetime.timedelta(
        seconds=confirm_window)

    return model_query(context, models.Migration, session=session,
                       read_deleted="yes").\
        filter(models.Migration.updated_at <= confirm_window).\
        filter_by(status="finished").\
        all()

##################

@require_admin_context
def storage_type_create(context, values):
    """Create a new instance type. In order to pass in extra specs,
    the values dict should contain a 'extra_specs' key/value pair:

    {'extra_specs' : {'k1': 'v1', 'k2': 'v2', ...}}

    """
    if not values.get('id'):
        values['id'] = str(uuid.uuid4())

    session = get_session()
    with session.begin():
        try:
            storage_type_get_by_name(context, values['name'], session)
            raise exception.HardwareTypeExists(id=values['name'])
        except exception.HardwareTypeNotFoundByName:
            pass
        try:
            storage_type_get(context, values['id'], session)
            raise exception.HardwareTypeExists(id=values['id'])
        except exception.HardwareTypeNotFound:
            pass
        try:
            values['extra_specs'] = _metadata_refs(values.get('extra_specs'),
                                                   models.HardwareTypeExtraSpecs)
            storage_type_ref = models.HardwareTypes()
            storage_type_ref.update(values)
            storage_type_ref.save()
        except Exception, e:
            raise exception.DBError(e)
        return storage_type_ref

@require_context
def storage_type_get_all(context, inactive=False, filters=None):
    """
    Returns a dict describing all storage_types with name as key.
    """
    filters = filters or {}

    read_deleted = "yes" if inactive else "no"
    rows = model_query(context, models.HardwareTypes,
                       read_deleted=read_deleted).\
        options(joinedload('extra_specs')).\
        order_by("name").\
        all()

    # TODO(sirp): this patern of converting rows to a result with extra_specs
    # is repeated quite a bit, might be worth creating a method for it
    result = {}
    for row in rows:
        result[row['name']] = _dict_with_extra_specs(row)

    return result

@require_context
def storage_type_get(context, id, session=None):
    """Returns a dict describing specific storage_type"""
    result = model_query(context, models.HardwareTypes, session=session).\
        options(joinedload('extra_specs')).\
        filter_by(id=id).\
        first()

    if not result:
        raise exception.HardwareTypeNotFound(storage_type_id=id)

    return _dict_with_extra_specs(result)

@require_context
def storage_type_get_by_name(context, name, session=None):
    """Returns a dict describing specific storage_type"""
    result = model_query(context, models.HardwareTypes, session=session).\
        options(joinedload('extra_specs')).\
        filter_by(name=name).\
        first()

    if not result:
        raise exception.HardwareTypeNotFoundByName(storage_type_name=name)
    else:
        return _dict_with_extra_specs(result)

@require_admin_context
def storage_type_destroy(context, id):
    storage_type_get(context, id)

    session = get_session()
    with session.begin():
        session.query(models.HardwareTypes).\
            filter_by(id=id).\
            update({'deleted': True,
                    'deleted_at': timeutils.utcnow(),
                    'updated_at': literal_column('updated_at')})
        session.query(models.HardwareTypeExtraSpecs).\
            filter_by(storage_type_id=id).\
            update({'deleted': True,
                    'deleted_at': timeutils.utcnow(),
                    'updated_at': literal_column('updated_at')})

@require_context
def storage_get_active_by_window(context,
                                begin,
                                end=None,
                                project_id=None):
    """Return storages that were active during window."""
    session = get_session()
    query = session.query(models.Hardware)

    query = query.filter(or_(models.Hardware.deleted_at == None,
                             models.Hardware.deleted_at > begin))
    if end:
        query = query.filter(models.Hardware.created_at < end)
    if project_id:
        query = query.filter_by(project_id=project_id)

    return query.all()

####################

def _storage_type_extra_specs_query(context, storage_type_id, session=None):
    return model_query(context, models.HardwareTypeExtraSpecs, session=session,
                       read_deleted="no").\
        filter_by(storage_type_id=storage_type_id)

@require_context
def storage_type_extra_specs_get(context, storage_type_id):
    rows = _storage_type_extra_specs_query(context, storage_type_id).\
        all()

    result = {}
    for row in rows:
        result[row['key']] = row['value']

    return result

@require_context
def storage_type_extra_specs_delete(context, storage_type_id, key):
    _storage_type_extra_specs_query(context, storage_type_id).\
        filter_by(key=key).\
        update({'deleted': True,
                'deleted_at': timeutils.utcnow(),
                'updated_at': literal_column('updated_at')})

@require_context
def storage_type_extra_specs_get_item(context, storage_type_id, key,
                                     session=None):
    result = _storage_type_extra_specs_query(
        context, storage_type_id, session=session).\
        filter_by(key=key).\
        first()

    if not result:
        raise exception.HardwareTypeExtraSpecsNotFound(
            extra_specs_key=key,
            storage_type_id=storage_type_id)

    return result

@require_context
def storage_type_extra_specs_update_or_create(context, storage_type_id,
                                             specs):
    session = get_session()
    spec_ref = None
    for key, value in specs.iteritems():
        try:
            spec_ref = storage_type_extra_specs_get_item(
                context, storage_type_id, key, session)
        except exception.HardwareTypeExtraSpecsNotFound, e:
            spec_ref = models.HardwareTypeExtraSpecs()
        spec_ref.update({"key": key, "value": value,
                         "storage_type_id": storage_type_id,
                         "deleted": False})
        spec_ref.save(session=session)
    return specs

####################

@require_context
@require_storage_exists
def storage_glance_metadata_get(context, storage_id, session=None):
    """Return the Glance metadata for the specified storage."""
    if not session:
        session = get_session()

    return session.query(models.HardwareGlanceMetadata).\
        filter_by(storage_id=storage_id).\
        filter_by(deleted=False).all()

@require_context
@require_snapshot_exists
def storage_snapshot_glance_metadata_get(context, snapshot_id, session=None):
    """Return the Glance metadata for the specified snapshot."""
    if not session:
        session = get_session()

    return session.query(models.HardwareGlanceMetadata).\
        filter_by(snapshot_id=snapshot_id).\
        filter_by(deleted=False).all()

@require_context
@require_storage_exists
def storage_glance_metadata_create(context, storage_id, key, value,
                                  session=None):
    """
    Update the Glance metadata for a storage by adding a new key:value pair.
    This API does not support changing the value of a key once it has been
    created.
    """
    if not session:
        session = get_session()

    with session.begin():
        rows = session.query(models.HardwareGlanceMetadata).\
            filter_by(storage_id=storage_id).\
            filter_by(key=key).\
            filter_by(deleted=False).all()

        if len(rows) > 0:
            raise exception.GlanceMetadataExists(key=key,
                                                 storage_id=storage_id)

        vol_glance_metadata = models.HardwareGlanceMetadata()
        vol_glance_metadata.storage_id = storage_id
        vol_glance_metadata.key = key
        vol_glance_metadata.value = value

        vol_glance_metadata.save(session=session)

    return

@require_context
@require_snapshot_exists
def storage_glance_metadata_copy_to_snapshot(context, snapshot_id, storage_id,
                                            session=None):
    """
    Update the Glance metadata for a snapshot by copying all of the key:value
    pairs from the originating storage. This is so that a storage created from
    the snapshot will retain the original metadata.
    """
    if session is None:
        session = get_session()

    metadata = storage_glance_metadata_get(context, storage_id, session=session)
    with session.begin():
        for meta in metadata:
            vol_glance_metadata = models.HardwareGlanceMetadata()
            vol_glance_metadata.snapshot_id = snapshot_id
            vol_glance_metadata.key = meta['key']
            vol_glance_metadata.value = meta['value']

            vol_glance_metadata.save(session=session)

@require_context
@require_storage_exists
def storage_glance_metadata_copy_from_storage_to_storage(context,
                                                      src_storage_id,
                                                      storage_id,
                                                      session=None):
    """
    Update the Glance metadata for a storage by copying all of the key:value
    pairs from the originating storage. This is so that a storage created from
    the storage (clone) will retain the original metadata.
    """
    if session is None:
        session = get_session()

    metadata = storage_glance_metadata_get(context,
                                          src_storage_id,
                                          session=session)
    with session.begin():
        for meta in metadata:
            vol_glance_metadata = models.HardwareGlanceMetadata()
            vol_glance_metadata.storage_id = storage_id
            vol_glance_metadata.key = meta['key']
            vol_glance_metadata.value = meta['value']

            vol_glance_metadata.save(session=session)

@require_context
@require_storage_exists
def storage_glance_metadata_copy_to_storage(context, storage_id, snapshot_id,
                                          session=None):
    """
    Update the Glance metadata from a storage (created from a snapshot) by
    copying all of the key:value pairs from the originating snapshot. This is
    so that the Glance metadata from the original storage is retained.
    """
    if session is None:
        session = get_session()

    metadata = storage_snapshot_glance_metadata_get(context, snapshot_id,
                                                   session=session)
    with session.begin():
        for meta in metadata:
            vol_glance_metadata = models.HardwareGlanceMetadata()
            vol_glance_metadata.storage_id = storage_id
            vol_glance_metadata.key = meta['key']
            vol_glance_metadata.value = meta['value']

            vol_glance_metadata.save(session=session)

@require_context
def storage_glance_metadata_delete_by_storage(context, storage_id):
    session = get_session()
    session.query(models.HardwareGlanceMetadata).\
        filter_by(storage_id=storage_id).\
        filter_by(deleted=False).\
        update({'deleted': True,
                'deleted_at': timeutils.utcnow(),
                'updated_at': literal_column('updated_at')})

@require_context
def storage_glance_metadata_delete_by_snapshot(context, snapshot_id):
    session = get_session()
    session.query(models.HardwareGlanceMetadata).\
        filter_by(snapshot_id=snapshot_id).\
        filter_by(deleted=False).\
        update({'deleted': True,
                'deleted_at': timeutils.utcnow(),
                'updated_at': literal_column('updated_at')})

####################

@require_admin_context
def sm_backend_conf_create(context, values):
    backend_conf = models.SMBackendConf()
    backend_conf.update(values)
    backend_conf.save()
    return backend_conf

@require_admin_context
def sm_backend_conf_update(context, sm_backend_id, values):
    session = get_session()
    with session.begin():
        backend_conf = model_query(context, models.SMBackendConf,
                                   session=session,
                                   read_deleted="yes").\
            filter_by(id=sm_backend_id).\
            first()

        if not backend_conf:
            raise exception.NotFound(
                _("No backend config with id %(sm_backend_id)s") % locals())

        backend_conf.update(values)
        backend_conf.save(session=session)
    return backend_conf

@require_admin_context
def sm_backend_conf_delete(context, sm_backend_id):
    # FIXME(sirp): for consistency, shouldn't this just mark as deleted with
    # `purge` actually deleting the record?
    session = get_session()
    with session.begin():
        model_query(context, models.SMBackendConf, session=session,
                    read_deleted="yes").\
            filter_by(id=sm_backend_id).\
            delete()

@require_admin_context
def sm_backend_conf_get(context, sm_backend_id):
    result = model_query(context, models.SMBackendConf, read_deleted="yes").\
        filter_by(id=sm_backend_id).\
        first()

    if not result:
        raise exception.NotFound(_("No backend config with id "
                                   "%(sm_backend_id)s") % locals())

    return result

@require_admin_context
def sm_backend_conf_get_by_sr(context, sr_uuid):
    return model_query(context, models.SMBackendConf, read_deleted="yes").\
        filter_by(sr_uuid=sr_uuid).\
        first()

@require_admin_context
def sm_backend_conf_get_all(context):
    return model_query(context, models.SMBackendConf, read_deleted="yes").\
        all()

####################

def _sm_flavor_get_query(context, sm_flavor_label, session=None):
    return model_query(context, models.SMFlavors, session=session,
                       read_deleted="yes").\
        filter_by(label=sm_flavor_label)

@require_admin_context
def sm_flavor_create(context, values):
    sm_flavor = models.SMFlavors()
    sm_flavor.update(values)
    sm_flavor.save()
    return sm_flavor

@require_admin_context
def sm_flavor_update(context, sm_flavor_label, values):
    sm_flavor = sm_flavor_get(context, sm_flavor_label)
    sm_flavor.update(values)
    sm_flavor.save()
    return sm_flavor

@require_admin_context
def sm_flavor_delete(context, sm_flavor_label):
    session = get_session()
    with session.begin():
        _sm_flavor_get_query(context, sm_flavor_label).delete()

@require_admin_context
def sm_flavor_get(context, sm_flavor_label):
    result = _sm_flavor_get_query(context, sm_flavor_label).first()

    if not result:
        raise exception.NotFound(
            _("No sm_flavor called %(sm_flavor)s") % locals())

    return result

@require_admin_context
def sm_flavor_get_all(context):
    return model_query(context, models.SMFlavors, read_deleted="yes").all()

###############################

def _sm_storage_get_query(context, storage_id, session=None):
    return model_query(context, models.SMHardware, session=session,
                       read_deleted="yes").\
        filter_by(id=storage_id)

def sm_storage_create(context, values):
    sm_storage = models.SMHardware()
    sm_storage.update(values)
    sm_storage.save()
    return sm_storage

def sm_storage_update(context, storage_id, values):
    sm_storage = sm_storage_get(context, storage_id)
    sm_storage.update(values)
    sm_storage.save()
    return sm_storage

def sm_storage_delete(context, storage_id):
    session = get_session()
    with session.begin():
        _sm_storage_get_query(context, storage_id, session=session).delete()

def sm_storage_get(context, storage_id):
    result = _sm_storage_get_query(context, storage_id).first()

    if not result:
        raise exception.NotFound(
            _("No sm_storage with id %(storage_id)s") % locals())

    return result

def sm_storage_get_all(context):
    return model_query(context, models.SMHardware, read_deleted="yes").all()

###############################

@require_context
def backup_get(context, backup_id, session=None):
    result = model_query(context, models.Backup,
                         session=session, project_only=True).\
        filter_by(id=backup_id).\
        first()

    if not result:
        raise exception.BackupNotFound(backup_id=backup_id)

    return result

@require_admin_context
def backup_get_all(context):
    return model_query(context, models.Backup).all()

@require_admin_context
def backup_get_all_by_host(context, host):
    return model_query(context, models.Backup).filter_by(host=host).all()

@require_context
def backup_get_all_by_project(context, project_id):
    authorize_project_context(context, project_id)

    return model_query(context, models.Backup).\
        filter_by(project_id=project_id).all()

@require_context
def backup_create(context, values):
    backup = models.Backup()
    if not values.get('id'):
        values['id'] = str(uuid.uuid4())
    backup.update(values)
    backup.save()
    return backup

@require_context
def backup_update(context, backup_id, values):
    session = get_session()
    with session.begin():
        backup = model_query(context, models.Backup,
                             session=session, read_deleted="yes").\
            filter_by(id=backup_id).first()

        if not backup:
            raise exception.BackupNotFound(
                _("No backup with id %(backup_id)s") % locals())

        backup.update(values)
        backup.save(session=session)
    return backup

@require_admin_context
def backup_destroy(context, backup_id):
    session = get_session()
    with session.begin():
        session.query(models.Backup).\
            filter_by(id=backup_id).\
            update({'status': 'deleted',
                    'deleted': True,
                    'deleted_at': timeutils.utcnow(),
                    'updated_at': literal_column('updated_at')})

####################
# power_cpu_logs table

@require_admin_context
def power_cpu_log_create(context, values, session=None):
    """
    """
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        power_cpu_log_ref = models.PowerCpuLog()
        session.add(power_cpu_log_ref)
        power_cpu_log_ref.update(values)
    return power_cpu_log_ref

@require_admin_context
def get_power_cpu_logs(context, compute_node_id):
    """
    """
    session = get_session()
#    result = model_query(context, models.PowerCpuLog, session=session).\
#                    filter_by(compute_node_id=compute_node_id).all()
    result = model_query(context, models.PowerCpuLog, session=session).\
                    filter_by(compute_node_id=compute_node_id).order_by(desc(models.PowerCpuLog.id)).limit(10000)
    return result
    

@require_admin_context
def powercpurelation_update(context, compute_id, values):
    """update the powercpurelation and populates the capacity fields
    with the most recent data."""
    session = get_session()
    #if auto_adjust:
        #_adjust_compute_node_values_for_utilization(context, values, session)
    with session.begin(subtransactions=True):
        powercpurelation_ref = powercpurelation_get(context, compute_id, session=session)
        powercpurelation_ref.update(values)
        powercpurelation_ref.save(session=session)

@require_admin_context
def powercpurelation_get(context, compute_id, session=None):
    result = model_query(context, models.powercpurelation, session=session).\
                     filter_by(compute_node_id=compute_id).\
                     first()

    if not result:
        raise exception.ComputeHostNotFound(host=compute_id)

    return result

#below is function about osd operating
#@DEBUG

@require_admin_context
def osd_get(context, osd_id, session=None):
    result = model_query(context, models.OsdState, session=session).\
        filter_by(id=osd_id).\
        options(joinedload('device')).\
        options(joinedload('storage_group')).\
        first()

    if not result:
        raise exception.VsmOsdNotFound(osd=osd_id)

    return result

@require_admin_context
def osd_get_all(context, session=None):
    return model_query(context, models.OsdState, session=session).all()

@require_admin_context
def osd_get_all_down(context, session=None):
    return model_query(
        context, models.OsdState, read_deleted="no").\
        filter_by(state="down").\
        all()

@require_admin_context
def osd_get_all_up(context, session=None):
    return model_query(
        context, models.OsdState, read_deleted="no").\
        filter_by(state="up").\
        all()

@require_admin_context
def osd_get_by_service_id(context, serviceid, session=None):
    return model_query(
        context, models.OsdState, read_deleted="no").\
        filter_by(service_id=serviceid).\
        all()

@require_admin_context
def osd_get_by_cluster_id(context, clusterid, session=None):
    return model_query(
        context, models.OsdState, read_deleted="no").\
        filter_by(cluster_id=clusterid).\
        all()

@require_admin_context
def osd_destroy(context, osd_id):
    session = get_session()
    with session.begin():
        osd_ref = osd_get(context, osd_id, session=session)
        osd_ref.delete(session=session)

@require_admin_context
def osd_create(context, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        osd_ref = models.OsdState()
        session.add(osd_ref)
        osd_ref.update(values)
    return osd_ref

@require_admin_context
def osd_update(context, osd_id, values):
    """update the information of osd with specified osd id"""
    session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        osd_ref = osd_get(context, osd_id, session=session)
        for (key, value) in values.iteritems():
            osd_ref[key] = value
        osd_ref.save(session=session)

@require_admin_context
def osd_delete(context, osd_id):
    session = get_session()

    with session.begin(subtransactions=True):
        values = {}
        values['deleted_at'] = timeutils.utcnow()
        values['updated_at'] = values['deleted_at']
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        osd_ref = osd_get(context, osd_id, session=session)
        for (key, value) in values.iteritems():
            osd_ref[key] = value
        osd_ref['deleted'] = True
        osd_ref.save(session=session)

@require_admin_context
def osd_remove(context, osd_id):
#TOCHANGE osd->osd_state and need to fix conflict
    session = get_session()

    with session.begin(subtransactions=True):
        values = {}
        values['deleted_at'] = timeutils.utcnow()
        values['updated_at'] = values['deleted_at']
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        osd_ref = osd_get(context, osd_id, session=session)
        for (key, value) in values.iteritems():
            osd_ref[key] = value
        osd_ref['operation_status'] = FLAGS.vsm_status_removed
        osd_ref.save(session=session)

#bellow is crushmap operating
#@DEBUG

@require_admin_context
def crushmap_get(context, crushmap_id, session=None):
    result = model_query(context, models.CrushMap, session=session).\
                        filter_by(id=crushmap_id).first()

    if not result:
        raise exception.VsmCrushMapNotFound(crushmap=crushmap_id)

    return result

@require_admin_context
def crushmap_get_all(context, session=None):
    return model_query(context, models.CrushMap, session=session).\
                       all()

@require_admin_context
def crushmap_create(context, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        crushmap_ref = models.CrushMap()
        session.add(crushmap_ref)
        crushmap_ref.update(values)
    return crushmap_ref

@require_admin_context
def crushmap_update(context, crushmap_id, values):
    """update the information of crushmap with specified crushmap id"""
    session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        crushmap_ref = crushmap_get(context, crushmap_id, session=session)
        for (key, value) in values.iteritems():
            crushmap_ref[key] = value
        crushmap_ref.save(session=session)

@require_admin_context
def crushmap_delete(context, crushmap_id):
    session = get_session()

    with session.begin(subtransactions=True):
        values = {}
        values['deleted_at'] = timeutils.utcnow()
        values['updated_at'] = values['deleted_at']
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        crushmap_ref = crushmap_get(context, crushmap_id, session=session)
        for (key, value) in values.iteritems():
            crushmap_ref[key] = value
        crushmap_ref['deleted'] = True
        crushmap_ref.save(session=session)

# operation on device

@require_admin_context
def device_get(context, device_id, session=None):
    result = model_query(context, models.Device, session=session).\
                     filter_by(id=device_id).\
                     first()

    if not result:
        raise exception.VsmDeviceNotFound(device=device_id)

    return result
@require_admin_context
def device_get_by_name(context, device_name, session=None):
    result = model_query(context, models.Device, session=session).\
                     filter_by(name = device_name).\
                     first()

    if not result:
        raise exception.VsmDeviceNotFound(device=device_name)

    return result

@require_admin_context
def device_get_all(context, session=None):
    return model_query(context, models.Device, session=session).\
                    options(joinedload('service')).\
                    all()

def device_get_count(context):
    query = model_query(context, models.Device, read_deleted="no").\
            count()
    return query

@require_admin_context
def device_get_all_by_interface_type(context, interface, session=None):
    return model_query(
        context, models.Device, read_deleted="no").\
        filter_by(interface_type=interface).\
        all()

@require_admin_context
def device_get_all_by_device_type(context, devicetype, session=None):
    return model_query(
        context, models.Device, read_deleted="no").\
        filter_by(device_type=devicetype).\
        all()

@require_admin_context
def device_get_all_by_service_id(context, serviceid, session=None):
    return model_query(
        context, models.Device, read_deleted="no").\
        filter_by(service_id=serviceid).\
        order_by(models.Device.service_id).\
        all()

@require_admin_context
def device_get_all_by_state(context, st, session=None):
    return model_query(
        context, models.Device, read_deleted="no").\
        filter_by(state=st).\
        all()

@require_admin_context
def device_create(context, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        device_ref = models.Device()
        session.add(device_ref)
        device_ref.update(values)

    return device_ref

@require_admin_context
def device_update(context, device_id, values):    
    session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        device_ref = device_get(context, device_id, session=session)

        for (key, value) in values.iteritems():
            device_ref[key] = value
        device_ref.save(session=session)
    return device_ref

@require_admin_context
def device_delete(context, device_id):    
    session = get_session()

    with session.begin(subtransactions=True):
        device_ref = device_get(context, device_id, session=session)
        device_ref['deleted_at'] = timeutils.utcnow()
        device_ref['updated_at'] = device_ref['deleted_at']
        device_ref['deleted'] = True
        convert_datetimes(device_ref, 'created_at', 'deleted_at', 'updated_at')

        device_ref.save(session=session)

# operation on recipes

@require_admin_context
def recipe_get(context, recipe_id, session=None):
    result = model_query(context, models.Recipe, session=session).\
                     filter_by(id=recipe_id).\
                     first()

    if not result:
        raise exception.VsmRecipeNotFound(recipe=recipe_id)
    
    return result

@require_admin_context
def recipe_get_all(context, session=None):
    return model_query(context, models.Recipe, session=session).\
                    all()

@require_admin_context
def recipe_create(context, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        recipe_ref = models.Recipe()
        session.add(recipe_ref)
        recipe_ref.update(values)

    return recipe_ref

@require_admin_context
def recipe_update(context, recipe_id, values):    
    session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        recipe_ref = recipe_get(context, recipe_id, session=session)

        for (key, value) in values.iteritems():
            recipe_ref[key] = value
        recipe_ref.save(session=session)

@require_admin_context
def recipe_delete(context, recipe_id):    
    session = get_session()

    with session.begin(subtransactions=True):
        recipe_ref = recipe_get(context, recipe_id, session=session)
        recipe_ref['deleted_at'] = timeutils.utcnow()
        recipe_ref['updated_at'] = recipe_ref['deleted_at']
        recipe_ref['deleted'] = True
        convert_datetimes(recipe_ref, 'created_at', 'deleted_at', 'updated_at')
        
        recipe_ref.save(session=session)

# opreration on VSM user capacity management
@require_admin_context
def vsm_capacity_manage_get(context, vsm_capacity_manage_id, session=None):
    result = model_query(context, models.VsmCapacityManage, session=session).\
                     filter_by(id=vsm_capacity_manage_id).\
                     first()

    if not result:
        raise exception.VsmCapacityManageNotFound(vsm_capacity_manage=
                                                  vsm_capacity_manage_id)

    return result

@require_admin_context
def vsm_capacity_manage_get_all(context, session=None):
    return model_query(context, models.VsmCapacityManage, session=session).\
                    all()

@require_admin_context
def vsm_capacity_manage_create(context, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        vsm_capacity_manage_ref = models.VsmCapacityManage()
        session.add(vsm_capacity_manage_ref)
        vsm_capacity_manage_ref.update(values)

    return vsm_capacity_manage_ref

@require_admin_context
def vsm_capacity_manage_update(context, vsm_capacity_manage_id, values):    
    session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        vsm_capacity_manage_ref = vsm_capacity_manage_get(
                                   context, vsm_capacity_manage_id,
                                   session=session)

        for (key, value) in values.iteritems():
            vsm_capacity_manage_ref[key] = value
        vsm_capacity_manage_ref.save(session=session)

@require_admin_context
def vsm_capacity_manage_delete(context, vsm_capacity_manage_id):    
    session = get_session()

    with session.begin(subtransactions=True):
        vsm_capacity_manage_ref = vsm_capacity_manage_get(context, vsm_capacity_manage_id, session=session)
        vsm_capacity_manage_ref['deleted_at'] = timeutils.utcnow()
        vsm_capacity_manage_ref['updated_at'] = vsm_capacity_manage_ref['deleted_at']
        vsm_capacity_manage_ref['deleted'] = True
        convert_datetimes(vsm_capacity_manage_ref, 'created_at', 'deleted_at', 'updated_at')
        
        vsm_capacity_manage_ref.save(session=session)

#bellow is operation on storage pool
@require_admin_context
def pool_get_all(context, session=None):
    return model_query(context, models.StoragePool, session=session).\
        options(joinedload('storage_group')).\
        all()

@require_admin_context
def pool_get(context, pool_id, session=None):
    result = model_query(context, models.StoragePool, session=session).\
        filter_by(pool_id=pool_id).\
        first()
    return result

@require_admin_context
def pool_get_by_pool_id(context, pool_id, session=None):
    result = model_query(context, models.StoragePool, session=session).\
        filter_by(pool_id=pool_id).\
        first()
    return result

@require_admin_context
def pool_get_by_db_id(context, pool_id, session=None):
    result = model_query(context, models.StoragePool, session=session).\
        options(joinedload('storage_group')).\
        filter_by(id=pool_id).\
        first()
    return result

@require_admin_context
def pool_get_by_name(context, pool_name, cluster_id, session=None):
    return model_query(context, models.StoragePool, session=session).\
        filter_by(name=pool_name).\
        filter_by(cluster_id=cluster_id).\
        first()

def pool_get_by_ruleset(context, ruleset, session=None):
    if not session:
        session = get_session()
    with session.begin(subtransactions=True):
        return model_query(context, models.StoragePool, session=session).\
            filter_by(crush_ruleset=ruleset).\
            all()

def pool_destroy(context, pool_name, session=None):
    if not session:
        session = get_session()
    with session.begin():
        pool_ref = pool_get_by_name(context, pool_name, cluster_id=1, session=session)
        if pool_ref:
            pool_ref.delete(session=session)

@require_admin_context
def pool_create(context, values, session=None):
    if not session:
        session = get_session()

    pool_ref = pool_get_by_name(context,
                        values['name'],
                        values['cluster_id'],
                        session)
    if pool_ref:
        return pool_ref

    with session.begin(subtransactions=True):
        pool_ref = models.StoragePool()
        session.add(pool_ref)
        pool_ref.update(values)

    return pool_ref

@require_admin_context
def pool_update_by_name(context, pool_name, cluster_id, values):
    session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        pool_ref = pool_get_by_name(context, pool_name, cluster_id, session=session)

        for (key, value) in values.iteritems():
            pool_ref[key] = value
        pool_ref.save(session=session)
        return pool_ref

#this pool_id is not the db id
@require_admin_context
def pool_update_by_pool_id(context, pool_id, values):
    session = get_session()
    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        pool_ref = pool_get_by_pool_id(context, pool_id, session=session)
        pool_ref.update(values)
        return pool_ref 
        
@require_admin_context
def pool_update(context, pool_id, values):
    session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        pool_ref = pool_get(context, pool_id, session=session)

        for (key, value) in values.iteritems():
            pool_ref[key] = value
        pool_ref.save(session=session)
        return pool_ref

#bellow is operation on cluster 
@require_admin_context
def cluster_get_all(context, session=None):
    return model_query(context, models.Cluster, session=session).all()

def cluster_update_ceph_conf(context, cluster_id, ceph_conf, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        values = {'ceph_conf': ceph_conf}
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        cluster_ref = cluster_get(context, cluster_id, session=session)

        for (key, value) in values.iteritems():
            cluster_ref[key] = value

        cluster_ref.save(session=session)

def cluster_increase_deleted_times(context, cluster_id, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        values = {'deleted_times': 0}
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        cluster_ref = cluster_get(context, cluster_id, session=session)
        values['deleted_times'] = cluster_ref['deleted_times'] + 1

        for (key, value) in values.iteritems():
            cluster_ref[key] = value

        cluster_ref.save(session=session)

def cluster_get_deleted_times(context, cluster_id, session=None):
    if not session:
        session = get_session()

    cluster_ref = cluster_get(context, cluster_id, session)
    return cluster_ref['deleted_times']

def cluster_get_ceph_conf(context, cluster_id, session=None):
    if not session:
        session = get_session()

    cluster_ref = cluster_get(context, cluster_id, session)
    return cluster_ref['ceph_conf']

@require_admin_context
def cluster_info_dict_get_by_id(context, cluster_id, session=None):
    if not session:
        session = get_session()

    cluster_ref = cluster_get(context, cluster_id, session)
    if cluster_ref and cluster_ref.get('info_dict', None):
        info = json.loads(cluster_ref['info_dict'])
        return info

    return None

@require_admin_context
def cluster_get(context, cluster_id, session=None):
    if not session:
        session = get_session()

    result = model_query(context, models.Cluster, session=session).\
                     filter_by(id=cluster_id).\
                     first()
    return result

@require_admin_context
def cluster_create(context, values, session=None):

    if not values.get('ceph_conf', None):
        values['ceph_conf'] = ""

    if not session:
        session = get_session()
    with session.begin(subtransactions=True):
        cluster_ref = models.Cluster()
        session.add(cluster_ref)

        # This info_dict will be transfer into json.
        # Keep values can be used outside this function.
        # We use vc to transfer into DB.
        vc = values
        info = vc.get('info_dict', None)
        if info:
            vc['info_dict'] = json.dumps(info)

        cluster_ref.update(vc)

    return cluster_ref

@require_admin_context
def cluster_update(context, cluster_id, values, session=None):

    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        cluster_ref = cluster_get(context, cluster_id, session=session)

        for (key, value) in values.iteritems():
            cluster_ref[key] = value

        # DB.cluster table ['info_dict'] contains
        # json format string.
        info = values.get('info_dict', None)
        if info:
            cluster_ref['info_dict'] = json.dumps(info)

        # TODO change it to cluster_ref.save() ?
        #cluster_ref.update(values)
        cluster_ref.save(session=session)

#bellow is operation on storage_group
@require_admin_context
def storage_group_get_all(context, session=None):
    return model_query(context, models.StorageGroup, session=session).all()

@require_admin_context
def storage_group_get_by_rule_id(context, rule_id, session=None):
    if not session:
        session = get_session()

    result = model_query(context, models.StorageGroup, session=session).\
                     filter_by(rule_id=rule_id).\
                     first()
    return result

@require_admin_context
def storage_group_get_by_name(context, name, session=None):
    if not session:
        session = get_session()
    result = model_query(context, models.StorageGroup, session=session).\
            filter_by(name=name).first()
    return result

@require_admin_context
def storage_group_get_by_storage_class(context, storage_class, session=None):
    if not session:
        session = get_session()

    result = model_query(context, models.StorageGroup, session=session).\
             filter_by(storage_class=storage_class).\
             first()
    return result

@require_admin_context
def storage_group_get(context, group_id, session=None):
    result = model_query(context, models.StorageGroup, session=session).\
                     filter_by(id=group_id).\
                     first()
    if not result:
        raise exception.VsmStorageGroupNotFound(group=group_id)

    return result

@require_admin_context
def storage_group_create(context, values, session=None):
    if not session:
        session = get_session()
    with session.begin(subtransactions=True):
        group_ref = models.StorageGroup()
        session.add(group_ref)
        group_ref.update(values)

    return group_ref

@require_admin_context
def storage_group_update(context, group_id, values):
    session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        group_ref = storage_group_get(context, group_id, session=session)

        for (key, value) in values.iteritems():
            group_ref[key] = value
        group_ref.save(session=session)
                                 
@require_admin_context
def storage_group_update_by_name(context, name, values, session=None):
    if not session:
        session = get_session()
    with session.begin(subtransactions=True):
        group_ref = storage_group_get_by_name(context, name, session=session)
        if group_ref:
            values['updated_at'] = timeutils.utcnow()
            convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
            group_ref.update(values)
    
#bellow is operation on zone
@require_admin_context
def zone_get_all(context, session=None):
    return model_query(context, models.Zone, session=session).all()

@require_admin_context
def zone_get(context, zone_id, session=None):
    result = model_query(context, models.Zone, session=session).\
                     filter_by(id=zone_id).\
                     first()
    return result

@require_admin_context
def zone_create(context, values, session=None):
    if not session:
        session = get_session()
    with session.begin(subtransactions=True):
        map_ref = models.Zone()
        session.add(map_ref)
        map_ref.update(values)

    return map_ref

@require_admin_context
def zone_update(context, zone_id, values):
    session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        map_ref = zone_get(context, zone_id, session=session)

        for (key, value) in values.iteritems():
            map_ref[key] = value
        map_ref.save(session=session)

def server_get_all(context):
    query = model_query(context, models.ComputeNode)

    return query.all()

def cluster_get_by_name(context, name, session=None):
    result = model_query(
        context,
        models.Cluster, \
        session=session,\
        read_deleted="no").\
        filter_by(name=name).\
        first()
    return result

def init_node_create(context, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        if values['primary_public_ip']:
            init_node_ref = init_node_get_by_primary_public_ip(context,
                        values['primary_public_ip'],
                        session=session)
        elif values['secondary_public_ip']:
            init_node_ref = init_node_get_by_secondary_public_ip(context,
                        values['secondary_public_ip'],
                        session=session)
        elif values['cluster_ip']:
            init_node_ref = init_node_get_by_cluster_ip(context,
                        values['cluster_ip'],
                        session=session)
        else:
            init_node_ref = None
        if not init_node_ref:
            init_node_ref = models.InitNode()
            session.add(init_node_ref)
        init_node_ref.update(values)

    return init_node_ref

def init_node_get_all(context):
    query = model_query(context, models.InitNode)
    return query.all()

def init_node_get_by_host(context, host, session=None):
    """Get init node ref by host name."""
    if not session:
        session = get_session()

    init_node_ref = model_query(context,
                                models.InitNode,
                                read_deleted="no",
                                session=session).\
        options(joinedload('zone')).\
        filter_by(host=host).\
        first()

    #if not init_node_ref:
    #    LOG.warn('Can not find init_node_ref by %s' % host)

    return init_node_ref

def init_node_get_by_cluster_id(context, cluster_id, session=None):
    """Get init node ref by cluster id."""
    if not session:
        session = get_session()

    init_node_ref = model_query(context,
                            models.InitNode,
                            session=session).\
                            filter_by(cluster_id=cluster_id).\
                            filter_by(deleted=False).all()

    if not init_node_ref:
        LOG.warn('Can not find init_node_ref by %s' % cluster_id)

    return init_node_ref

def init_node_get_cluster_nodes(context, init_node_id, session=None):
    """Get all active nodes in the same cluster."""
    if not session:
        session = get_session()

    init_node_ref = init_node_get(context, init_node_id, session)
    if not init_node_ref:
        LOG.warn('Can not find %s' % init_node_id)
        raise exception.NotFound()

    cluster_ip = init_node_ref['cluster_ip']
    cluster_id = init_node_ref['cluster_id']

    if cluster_id:
        node_list = model_query(context,
                             models.InitNode,
                             session=session).\
                             filter_by(cluster_id=cluster_id).\
                             filter_by(deleted=False).all()
    elif cluster_ip:
        node_list = model_query(context,
                             models.InitNode,
                             session=session).\
                             filter_by(cluster_ip=cluster_ip).\
                             filter_by(deleted=False).all()
    else:
        LOG.warn('Can not find the cluster ip, cluster_id for %s' \
                  % init_node_ref['host'])
        raise exception.NotFound()

    return node_list

def init_node_get_by_primary_public_ip(context, primary_public_ip, \
                                       session=None):
    result = model_query(
        context,
        models.InitNode,\
        session=session,\
        read_deleted="no").\
        filter_by(primary_public_ip=primary_public_ip).\
        first()
    return result

def init_node_get_by_secondary_public_ip(context, secondary_public_ip,\
                                         session=None):
    result = model_query(
        context,
        models.InitNode,\
        session=session,\
        read_deleted="no").\
        filter_by(secondary_public_ip=secondary_public_ip).\
        first()
    return result

def init_node_get_by_cluster_ip(context, cluster_ip, session=None):
    result = model_query(
        context,
        models.InitNode,\
        session=session,\
        read_deleted="no").\
        filter_by(cluster_ip=cluster_ip).\
        first()
    return result

def init_node_get(context, id, session=None):
    if not session:
        session = get_session()

    result = model_query(
        context,
        models.InitNode,
        session=session,
        read_deleted='no').\
        options(joinedload('zone')).\
        filter_by(id=id).\
        first()
    return result

def init_node_update(context, init_node_id, values, session=None):
    if not session:
        session = get_session()
    with session.begin(subtransactions=True):
        if init_node_id:
            map_ref = init_node_get(context, init_node_id, session=session)
            values['updated_at'] = timeutils.utcnow()
            convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
            for (key, value) in values.iteritems():
                map_ref[key] = value
            map_ref.save(session=session)
        else:
            init_node_create(context, values, session=session)

def init_node_update_status_by_id(context, init_node_id, status, session=None):
    if not session:
        session = get_session()
    with session.begin(subtransactions=True):
        if init_node_id:
            map_ref = init_node_get(context, init_node_id, session=session)
            pre_status = map_ref.get('status', None)
            if pre_status.lower().find('unavailable') != -1 \
                or pre_status == 'unavailable' \
                or pre_status.find('ERROR') != -1:
                pre_status = map_ref['pre_status']

            values = {'status': status,
                      'pre_status': pre_status,
                      'updated': timeutils.utcnow()}
            convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
            for (key, value) in values.iteritems():
                map_ref[key] = value
            map_ref.save(session=session)
        else:
            values = {'status': status,
                      'updated': timeutils.utcnow()}
            init_node_create(context, values, session=session)

def init_node_get_by_hostname(context, hostname, session=None):
    return model_query(
        context,
        models.InitNode,
        session=session).\
        filter_by(host=hostname).\
        first()

def init_node_get_by_service_id(context, service_id, session=None):
    return model_query(context, \
                       models.InitNode, \
                       session=session).\
                       filter_by(service_id=service_id).\
                       options(joinedload('zone')).\
                       first()
def init_node_get_by_device_id(context, device_id, session=None):
    return model_query(context, \
                   models.InitNode,\
                   session=session).join(models.Service).join(models.Device).\
                   filter(models.Device.id==device_id).\
                   first()
def zone_get_by_name(context, name, session=None):
    return model_query(
        context, 
        models.Zone, read_deleted="no").\
        filter_by(name=name).\
        first()

def init_node_get_by_id_and_type(context, id, type, session=None):
    field = models.InitNode.type
    return model_query(
        context, 
        models.InitNode,
        read_deleted="no").\
        filter_by(id=id).\
        filter(field.like('%%%s%%' % type)).\
        first()

def init_node_get_by_id(context, id, session=None):
    return model_query(
        context,
        models.InitNode,
        session=session,
        read_deleted="no").\
        options(joinedload('cluster')).\
        filter_by(id=id).\
        first()

def init_node_count_by_status(context, status):
    return model_query(context, models.InitNode,
                       read_deleted="no").\
                       filter_by(status=status).\
                       count()

def osd_state_get(context, id, session=None):
    result = model_query(context, models.OsdState, session=session).\
        filter_by(id=id).\
        first()

    return result

def osd_state_create(context, values, session=None):
    if not session:
        session = get_session()

    ref = osd_state_get_by_name(context, values.get('osd_name'))
    if ref:
        ref = osd_state_update(context, ref['id'], values)
        return ref

    with session.begin(subtransactions=True):
        osd_state_ref = models.OsdState()
        session.add(osd_state_ref)
        osd_state_ref.update(values)

    return osd_state_ref

def osd_state_update(context, id, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        osd_state_ref = osd_state_get(context, id, session=session)
        osd_state_ref.update(values)
    return osd_state_ref

def osd_state_update_or_create(context, values):
    session = get_session()
    with session.begin():
        result = None
        if values['id']:
            result = model_query(context,
                                models.OsdState,
                                session=session).\
                        filter_by(id=values['id']).\
                        first()
        if result:
            result.update(values)
        else:
            result = models.OsdState()
            result.update(values)
        result.save(session=session)
        return result

def osd_state_count_by_init_node_id(context, init_node_id):
    init_node_ref = init_node_get_by_id(context, init_node_id)
    result = model_query(context,
                        func.count(models.OsdState.id),
                        base_model=models.OsdState,
                        read_deleted="no").\
                        filter_by(service_id=init_node_ref['service_id']).\
                        first()
    return (result[0] or 0)

def zone_get_by_id(context, id):
    result = model_query(
        context, models.Zone, read_deleted="no").\
        filter_by(id=id).\
        first()
    if not result:
        raise exception.ServiceNotFound(id=id)
    return result

def device_get_distinct_storage_class_by_service_id(context, service_id):
    storage_classes = []
    for result in model_query(
        context, models.Device.device_type,
        base_model=models.Device).distinct():
        storage_classes.append(result[0])
    return storage_classes

def device_get_by_name_and_journal_and_service_id(context, name, \
                                                journal, service_id):
    result = model_query(
            context, models.Device, read_deleted="no").\
            filter_by(name=name).\
            filter_by(journal=journal).\
            filter_by(service_id=service_id).\
            first()
    return result

def device_get_by_service_id(context, service_id):
    result = model_query(
            context, models.Device, read_deleted="no").\
            filter_by(service_id=service_id).\
            all()
    return result

def osd_state_get_all(context,
                      limit=None,
                      marker=None,
                      sort_keys=None,
                      sort_dir=None):
    query = model_query(context, models.OsdState, read_deleted="no").\
        options(joinedload('device')).\
        options(joinedload('service')).\
        options(joinedload('storage_group')).\
        options(joinedload('zone'))

    marker_item = None
    if marker is not None:
        marker_item = osd_get(context, marker)

    if sort_keys is None:
        sort_keys = ['id']
    else:
        if 'id' not in sort_keys:
            sort_keys.insert(0, 'id')

    return sqlalchemyutils.paginate_query(query, models.OsdState,
                                          limit, sort_keys=sort_keys,
                                          marker=marker_item, sort_dir=sort_dir)

def get_zone_hostname_storagegroup_by_osd_id(context,osd_id):
    result = model_query(context, models.OsdState, read_deleted="no").\
        options(joinedload('device')).\
        options(joinedload('service')).\
        options(joinedload('storage_group')).\
        options(joinedload('zone')).filter_by(id=osd_id)
    return result

def osd_state_get_by_name(context, name):
    result = model_query(context,
            models.OsdState, read_deleted="no").\
            filter_by(osd_name=name).\
            first()
    return result

def osd_state_get_by_service_id_and_storage_group_id(context, service_id,
    storage_group_id):
    result = model_query(
        context, models.OsdState, read_deleted="no").\
        filter_by(service_id=service_id).\
        filter_by(storage_group_id=storage_group_id).\
        all()
    return result

def osd_state_get_by_service_id(context, service_id):
    result = model_query(
        context, models.OsdState, read_deleted="no").\
        filter_by(service_id=service_id).\
        all()
    return result

def osd_state_get_by_osd_name_and_service_id_and_cluster_id(\
        context, osd_name, service_id, cluster_id):
    result = model_query(
        context, models.OsdState).\
        filter_by(osd_name=osd_name).\
        filter_by(service_id=service_id).\
        filter_by(cluster_id=cluster_id).\
        first()
    return result

def osd_state_get_by_device_id_and_service_id_and_cluster_id(\
        context, device_id, service_id, cluster_id):
    result = model_query(
        context, models.OsdState).\
        filter_by(device_id=device_id).\
        filter_by(service_id=service_id).\
        filter_by(cluster_id=cluster_id).\
        first()
    return result

def osd_state_count_by_storage_group_id(context, storage_group_id):
    result = model_query(
        context, models.OsdState, read_deleted="no").\
        filter_by(storage_group_id=storage_group_id).\
        filter(models.OsdState.state!=FLAGS.vsm_status_uninitialized).\
        count()
    LOG.info('osd cnt ====%s'%result)
    return result

def osd_state_count_service_id_by_storage_group_id(context, storage_group_id):
    #result = model_query(context, models.OsdState.service_id,models.OsdState.storage_group_id, \
    #                    base_model=models.OsdState,read_deleted="no").\
    #                    filter_by(storage_group_id=storage_group_id).\
    #                    distinct().\
    #                    count()
    result = model_query(context, models.OsdState.service_id, \
                     base_model=models.OsdState,read_deleted="no").\
                     distinct().\
                     count()
    return result 

def device_update_or_create(context, values):
    session = get_session()
    with session.begin():
        result = None
        if values['id']:
           result = model_query(context, models.Device, session=session).\
                        filter_by(id=values['id']).\
                        first()
        if result:
            result.update(values)
        else:
            result = models.Device()
            result.update(values)
        result.save(session=session)
        return result

##############################################ly>

#region vsmapp operations

@require_context
def appnodes_get_by_id(context, id, session=None):
    result = model_query(
        context, models.Appnode, read_deleted='no',
        project_only=True, session=session).\
        options(joinedload('vsmapp')).\
        filter_by(id=id).\
        first()
    if not result:
        raise exception.AppNodeNotFound(appnode_id=id)

    return result

@require_context
def appnodes_get_by_ip_vsmappid(context, ip, vsmappid):
    return model_query(context, models.Appnode,
                       read_deleted='no',
                       project_only=True).\
        filter_by(ip=ip).\
        filter_by(vsmapp_id=vsmappid).\
        first()

@require_context
def appnodes_get_all_by_vsmappid(context, vsmapp_id):
    return model_query(context, models.Appnode,
                       read_deleted='no',
                       project_only=True).\
        filter_by(vsmapp_id=vsmapp_id).first()

@require_context
def appnodes_get_all(context):
    """admin is able to view all the app nodes in all the clusters while
        user can only view the appnodes under his account.
    """

    query = model_query(context, models.Appnode,
                        read_deleted='no',
                        project_only=True).\
        options(joinedload('vsmapp')).\
        all()

    return query

@require_context
def appnodes_create(context, values, allow_duplicate=False):
    vsmapp = vsmapps_get_by_project(context)
    vsmapp_id = vsmapp.id if vsmapp else None
    LOG.debug('vsmapp get by project %s' % vsmapp_id)

    if vsmapp_id is None:
        raise exception.VsmappNotFound()
    else:
        values['vsmapp_id'] = vsmapp_id

    ip = values.get('ip', None)
    if not ip:
        raise exception.AppNodeInvalidInfo()

    ref = appnodes_get_by_ip_vsmappid(context, ip, vsmapp_id)
    if ref:
        if not allow_duplicate:
            # The node exists, return the node info straightaway.
            raise exception.DuplicateVsmApp(ip=ip,
                                            err='The app node already exists.')
        else:
            return ref

    values['created_at'] = timeutils.utcnow()
    values['deleted'] = 0

    try:
        appnodes_ref = models.Appnode()
        appnodes_ref.update(values)
        appnodes_ref.save()
    except db_exc.DBDuplicateEntry as e:
        raise exception.DuplicateAppnode(ip=ip, err=e.message)

    return appnodes_ref

@require_context
def appnodes_update(context, appnode_id, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        if appnode_id:
            appnode_ref = appnodes_get_by_id(context, appnode_id, session=session)
            if not appnode_ref:
                raise exception.AppNodeNotFound()
            values['updated_at'] = timeutils.utcnow()
            convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
            appnode_ref.update(values)
        else:
            raise exception.AppNodeNotFound()

        return appnode_ref

@require_context
def appnodes_destroy(context, appnode_id=None):
    if not appnode_id:
        raise exception.AppNodeNotFound()

    kargs= {}
    kargs['deleted'] = 1
    kargs['id'] = appnode_id
    kargs['deleted_at'] = timeutils.utcnow()

    return appnodes_update(context, appnode_id, kargs)

@require_context
def vsmapps_get_by_project(context, create=True):
    LOG.debug('user id: %s, tenant_id: %s' % (context.user_id, context.project_id))
    result = model_query(
        context, models.Vsmapp, read_deleted='no').\
        filter_by(project_id=context.project_id).\
        first()

    if not result:
        if create:
        # no vsmapp cluster for this project, create one
            result = vsmapps_create(context, display_name='vsm')

    return result

@require_context
def vsmapps_get_by_id(context, vsmapp_id):

    result = model_query(
        context, models.Vsmapp, read_deleted='no', project_only=True).\
        filter_by(id=vsmapp_id).\
        first()

    if not result:
        raise exception.VsmappNotFound()

    return result

@require_context
def vsmapps_create(context, uuid=None, display_name=None,
                   app_type='OpenStack', storage_type='rbd', session=None):

    uid = uuidutils.generate_uuid() if not uuid else uuid

    kargs = {
        'user_id': context.user_id,
        'project_id': context.project_id,
        'uuid': uid,
        'display_name': display_name,
        'app_type': app_type,
        'storage_type': storage_type,
        'deleted': 0
    }

    if not session:
        session = get_session()

    try:
        with session.begin(subtransactions=True):
            vsmapps_ref = models.Vsmapp()
            session.add(vsmapps_ref)
            vsmapps_ref.update(kargs)

    except db_exc.DBDuplicateEntry as e:
        raise exception.DuplicateVsmApp(id=context.project_id, err=e.message)

    return vsmapps_ref

#endregion

#region storage_pool_usage db ops

@require_context
def get_sp_usage_all_by_vsmapp_id(context, vsmapp_id, session=None):
    if not session:
        session = get_session()

    usage_ref = model_query(context, models.StoragePoolUsage,
                            read_deleted='no', project_only=True).\
          filter_by(vsmapp_id=vsmapp_id).\
          all()
    return usage_ref

@require_context
def sp_usage_create(context, pools, session=None):

    if not session:
        session = get_session()

    vsmapp = vsmapps_get_by_project(context)
    vsmapp_id = vsmapp.id if vsmapp else None

    appnode = appnodes_get_all_by_vsmappid(context, vsmapp_id)
    vsmapp_ip = appnode['ip']

    if not vsmapp_id:
        raise exception.VsmappNotFound()

    pools = [int(x) for x in pools]
    #update pools
    old_pools = get_sp_usage_all_by_vsmapp_id(context, vsmapp_id, session)
    for pref in old_pools:
        pool_id = pref['pool_id']
        # Filter the deleted pools.
        pool_ref = pool_get_by_db_id(context, pool_id, session)
        if pool_ref:
            pools.append(pref['pool_id'])
    pools = list(set(pools))


    pool_info_list = []
    pool_name_list = []
    for pool_id in pools:
        pool_ref = pool_get_by_db_id(context, pool_id, session)
        storage_group = pool_ref['storage_group']
        #rule_id = pool_ref['crush_ruleset']
        #storage_group_ref = storage_group_get_by_rule_id(context,
        #                                                 rule_id,
        #                                                 session)
        storage_class = storage_group['storage_class']
        info = {'name': pool_ref['name'],
                'type': storage_class,
                'id': pool_ref['id']}
        pool_name_list.append(pool_ref['name'])
        pool_info_list.append(info)

    for pool_id in pools:
        ref = get_sp_usage_by_poolid_vsmappid(context, pool_id, vsmapp_id)

        kargs = {
            'pool_id': pool_id,
            'vsmapp_id': vsmapp_id,
            'attach_status': 'starting',
            'attach_at': timeutils.utcnow(),
            'deleted': 0
        }

        if ref:
            ref.update(kargs)
            continue


        with session.begin(subtransactions=True):
            sp_usage_ref = models.StoragePoolUsage()
            session.add(sp_usage_ref)
            sp_usage_ref.update(kargs)

    return {'pool_infos': pool_info_list,
            'pool_names': pool_name_list,
            'vsmapp_ip': vsmapp_ip,
            'vsmapp_id': vsmapp_id}

@require_context
def get_sp_usage_by_poolid_vsmappid(context, poolid, vsmapp_id):
    usage_ref = model_query(context, models.StoragePoolUsage,
                            read_deleted='no', project_only=True).\
        filter_by(pool_id=poolid).\
        filter_by(vsmapp_id=vsmapp_id).\
        first()
    return usage_ref

@require_context
def get_sp_usage(context):
    LOG.debug('user id: %s, tenant_id: %s' % (context.user_id, context.project_id))
    result = model_query(
        context, models.StoragePoolUsage, read_deleted='no', project_only=True).\
        all()

    return result

def _get_usage_by_id(context, usage_id, session):
    usage_ref = model_query(context, models.StoragePoolUsage,
                            read_deleted='no', project_only=True, session=session).\
        filter_by(id=usage_id).\
        first()
    if not usage_ref:
        raise exception.StoragePoolUsageNotFound()
    return usage_ref

@require_context
def sp_usage_update(context, id, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        if id:
            usage_ref = _get_usage_by_id(context, id, session=session)
            values['updated_at'] = timeutils.utcnow()
            usage_ref.update(values)
        else:
            return None

        return usage_ref

def sp_usage_destroy(context, id, session=None):
    if not session:
        session = get_session()

    if id:
        usage_ref = _get_usage_by_id(context, id, session=session)
        usage_ref.delete(session=session)
    else:
        return None

    return usage_ref

#endregion

#region summary
summary_type = ['osd', 'pg', 'mds', 'mon', 'cluster', 'vsm', 'ceph']

def validate_summary_type(stype):
    if not stype or stype not in summary_type:
        raise exception.InvalidInput('Incorrect summary type provided.')

def _summary_get(context, cluster_id, stype, session=None):
    return model_query(
        context, models.Summary, read_deleted='no', session=session).\
        filter_by(cluster_id=cluster_id).\
        filter_by(summary_type=stype).\
        first()

def summary_get_by_cluster_id_and_type(context, cluster_id, stype,
                                       session=None):
    validate_summary_type(stype)

    result = _summary_get(context, cluster_id, stype, session)

    #if not result:
    #    raise exception.SummaryNotFound(type=stype)

    return result

def summary_get_by_type_first(context, stype, session=None):
    validate_summary_type(stype)
    return model_query(
        context, models.Summary, read_deleted='no', session=session).\
        filter_by(summary_type=stype).\
        first()

def summary_create(context, values, session=None):

    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        summary_ref = models.Summary()
        session.add(summary_ref)
        summary_ref.update(values)
    return summary_ref

def summary_update(context, cluster_id, stype, values, session=None):
    validate_summary_type(stype)

    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        summary_ref = _summary_get(context, cluster_id, stype, session)
        if not summary_ref:
            # create one
            values['cluster_id'] = cluster_id
            values['summary_type'] = stype
            return summary_create(context, values, session)

        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')

        summary_ref.update(values)
        summary_ref.save(session=session)

        return summary_ref

#endregion

#region monitor data

def _get_monitor(context, session=None):
    return model_query(
        context, models.Monitor, read_deleted='no', session=session)

def monitor_get_all(context, session=None):
    return _get_monitor(context, session=session).all()

def monitor_get_by_name(context, monitor_name, session=None):
    mon = None
    if not monitor_name:
        return mon
    mon = _get_monitor(context, session).\
        filter_by(name=monitor_name).\
        first()

    if not mon:
        raise exception.MonitorNotFound(name=monitor_name)

    return mon

def monitor_get(context, mon_id, session=None):
    mon = None
    if not mon_id:
        return mon
    mon = _get_monitor(context, session).\
        filter_by(id=mon_id).\
        first()

    if not mon:
        raise exception.MonitorNotFound()

    return mon

def monitor_create(context, values, session=None):

    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        monitor_ref = models.Monitor()
        session.add(monitor_ref)
        monitor_ref.update(values)
    return monitor_ref

def monitor_update(context, monitor_name, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        mon_ref = _get_monitor(context, session).\
            filter_by(name=monitor_name).\
            first()
        if not mon_ref:
            # create one
            values['name'] = monitor_name
            return monitor_create(context, values, session)

        mon_ref.update(values)
        mon_ref.save(session=session)

        return mon_ref

def monitor_destroy(context, monitor_name):
    session = get_session()
    with session.begin():
        mon_ref = monitor_get_by_name(context, monitor_name, session=session)
        mon_ref.delete(session=session)

#endregion

def pg_create(context, values):
    pg_ref = models.PlacementGroup()
    pg_ref.update(values)
    try:
        pg_ref.save()
    except db_exc.DBDuplicateEntry:
        raise exception.PGExists(pg_id = values['pg_id'])
    return pg_ref

def pg_get(context, pg_id):
    return _pg_get(context, pg_id)

def _pg_get(context, pg_id, session=None):
    result = model_query(context, models.PlacementGroup, session=session).\
            filter_by(id=pg_id).\
            first()

    if not result:
        raise exception.PGNotFound(pg_id=pg_id)

    return result

def _pg_get_by_pgid(context, pgid, session=None):
    result = model_query(context, models.PlacementGroup, session=session).\
        filter_by(pgid=pgid).\
        first()

    if not result:
        raise exception.PGNotFound(pgid=pgid)

    return result

def pg_get_query(context, model, session):
    return model_query(context, model, read_deleted="no", session=session)

def pg_get_all(context, limit=None, marker=None, sort_keys=None,
               sort_dir=None, session=None):

    if not session:
        session = get_session()
    
    marker_item = None
    if marker is not None:
        marker_item = _pg_get_by_pgid(context,  marker)
    
    query = pg_get_query(context, models.PlacementGroup, session)

    if sort_keys is None:
        sort_keys = ['pgid']
    else:
        if 'pgid' not in sort_keys:
            sort_keys.insert(0, 'pgid')

    return sqlalchemyutils.paginate_query(query, models.PlacementGroup,
                                          limit, sort_keys=sort_keys,
                                          marker=marker_item,
                                          sort_dir=sort_dir)

def pg_get_by_pgid(context, pgid, session=None):
    if not session:
        session = get_session()
    return model_query(context, models.PlacementGroup, read_deleted="no",
                       session=session).\
                       filter_by(pgid=pgid).\
                       first()

def pg_update(context, pg_id, values, session=None):
    if not session:
        session = get_session()
    with session.begin():
        pg_ref = _pg_get(context, pg_id, session=session)
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        pg_ref.update(values)
        pg_ref.save(session=session)
    return pg_ref

def pg_update_or_create(context, values, session=None):
    if not session:
        session = get_session()
    pg_ref = pg_get_by_pgid(context, values['pgid'], session=session)
    if pg_ref:
        pg = pg_update(context, pg_ref['id'], values, session=session)
    else:
        pg = pg_create(context, values)
    return pg

#rbd
def rbd_create(context, values):
    rbd_ref = models.RBD()
    rbd_ref.update(values)
    try:
        rbd_ref.save()
    except db_exc.DBDuplicateEntry:
        raise exception.RBDExists
    return rbd_ref

def rbd_get(context, rbd_id):
    return _rbd_get(context, rbd_id)

def _rbd_get(context, rbd_id, session=None):
    result = model_query(context, models.RBD, session=session).\
            filter_by(id=rbd_id).\
            first()

    if not result:
        raise exception.RBDNotFound(rbd_id=rbd_id)

    return result

def rbd_get_query(context, model, session):
    return model_query(context, model, read_deleted="no", session=session)

def rbd_get_all(context, limit=None, marker=None, sort_keys=None, sort_dir=None, session=None):
    if not session:
        session = get_session()

    marker_item = None
    if marker is not None:
        marker_item = rbd_get(context, marker)

    query = rbd_get_query(context, models.RBD, session)

    if sort_keys is None:
        sort_keys = ['id']
    else:
        if 'id' not in sort_keys:
            sort_keys.insert(0, 'id')

    return sqlalchemyutils.paginate_query(query, models.RBD,
                                          limit, sort_keys=sort_keys,
                                          marker=marker_item,
                                          sort_dir=sort_dir)

#    return model_query(context, models.RBD, read_deleted="no",
#                       session=session).all()

def rbd_get_by_pool_and_image(context, pool, image, session=None):
    if not session:
        session = get_session()
    return model_query(context, models.RBD, read_deleted="no",
                       session=session).\
                       filter_by(pool=pool).\
                       filter_by(image=image).\
                       first()

def rbd_update(context, rbd_id, values, session=None):
    if not session:
        session = get_session()
    with session.begin():
        rbd_ref = _rbd_get(context, rbd_id, session=session)
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        rbd_ref.update(values)
        rbd_ref.save(session=session)
    return rbd_ref

def rbd_update_or_create(context, values, session=None):
    if not session:
        session = get_session()
    rbd_ref = rbd_get_by_pool_and_image(context, values['pool'], \
                                        values['image'],session=session)
    if rbd_ref:
        rbd = rbd_update(context, rbd_ref['id'], values, session=session)
    else:
        rbd = rbd_create(context, values)
    return rbd

#region license status query
def license_status_create(context, values, session=None):

    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        license_ref = models.LicenseStatus()
        session.add(license_ref)
        license_ref.update(values)
    return license_ref

def license_status_get(context, session=None):
    #FIXME(fengqian): We only have one license status here
    #just for admin users and id = 1
    result = model_query(
        context, models.LicenseStatus, session=session).\
        filter_by(id=1).first()
    return result

def license_status_update(context, value, session=None):
    
    kargs = {'license_accept': value,
             'id': 1}

    if not session:
        session = get_session()
   
    with session.begin(subtransactions=True):
        license_ref = license_status_get(context, session)
        if not license_ref:
            return license_status_create(context, kargs, session)

        license_ref.update(kargs)
        license_ref.save(session=session)
        
        return license_ref

#endregion

#mds
def mds_create(context, values):
    mds_ref = models.MDS()
    mds_ref.update(values)
    try:
        mds_ref.save()
    except db_exc.DBDuplicateEntry:
        raise exception.MDSExists
    return mds_ref

def mds_get(context, mds_id):
    return _mds_get(context, mds_id)

def _mds_get(context, mds_id, session=None):
    result = model_query(context, models.MDS, session=session).\
            filter_by(id=mds_id).\
            first()

    if not result:
        raise exception.MDSNotFound(mds_id=mds_id)

    return result

def mds_get_all(context, session=None):
    if not session:
        session = get_session()
    return model_query(context, models.MDS, read_deleted="no",
                       session=session).all()

def mds_get_by_name(context, name, session=None):
    if not session:
        session = get_session()
    return model_query(context, models.MDS, read_deleted="no",
                       session=session).\
                       filter_by(name=name).\
                       first()

def mds_update(context, mds_id, values, session=None):
    if not session:
        session = get_session()
    with session.begin():
        mds_ref = _mds_get(context, mds_id, session=session)
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        mds_ref.update(values)
        mds_ref.save(session=session)
    return mds_ref

def mds_update_or_create(context, values, session=None):
    if not session:
        session = get_session()
    mds_ref = mds_get_by_name(context, values['name'], \
                             session=session)
    if mds_ref:
        mds = mds_update(context, mds_ref['id'], values, session=session)
    else:
        mds = mds_create(context, values)
    return mds

#region vsm settings db ops

def _vsm_settings_query(context, session=None):
    return model_query(
        context, models.VsmSettings, read_deleted='no', session=session)

def vsm_settings_create(context, values, session=None):

    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        settings_ref = models.VsmSettings()
        session.add(settings_ref)
        settings_ref.update(values)
    return settings_ref

def vsm_settings_update(context, setting_id, values, session=None):
    if not session:
        session = get_session()
    with session.begin():
        setting_ref = _vsm_settings_query(context, session=session).\
            filter_by(id=setting_id).\
            first()
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        setting_ref.update(values)
        setting_ref.save(session=session)
    return setting_ref

def vsm_settings_update_or_create(context, values, session=None):
    if not session:
        session = get_session()

    if not values.get('name'):
        return None

    setting_ref = vsm_settings_get_by_name(context, values['name'], session=session)

    if setting_ref:
        setting = vsm_settings_update(context, setting_ref['id'], values, session=session)
    else:
        setting = vsm_settings_create(context, values, session=session)
    return setting

def vsm_settings_get_all(context):
    return _vsm_settings_query(context).all()

def vsm_settings_get_by_name(context, name, session=None):
    return _vsm_settings_query(context, session).\
        filter_by(name=name).\
        first()

#endregion

#long_call
def long_call_get_by_uuid(context, uuid, session=None):
    if not session:
        session = get_session()

    result = model_query(
        context,
        models.LongCalls,
        read_deleted="no",
        session=session,
        ).\
        filter_by(uuid=uuid).\
        first()

    return result

def long_call_create(context, values, session=None):
    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        """long call create"""
        long_call_ref = models.LongCalls()
        session.add(long_call_ref)
        long_call_ref.update(values)

    return long_call_ref

def long_call_delete(context, uuid, session=None):
    if not session:
        session = get_session()
    with session.begin(subtransactions=True):
        """ long call delete """
        long_call_ref = long_call_get_by_uuid(context, uuid, session=session)
        if long_call_ref:
            session.delete(long_call_ref)
        return uuid

def long_call_update(context, long_call_uuid, values, session=None):
    if not session:
        session = get_session()
    with session.begin(subtransactions=True):
        long_call_ref = long_call_get_by_uuid(context, long_call_uuid, session=session)
        if not long_call_ref:
            return long_call_create(context,values)
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        long_call_ref.update(values)
    return long_call_ref
#endlong_call

#region ec profiles db ops

def _ec_profile_query(context, session=None):
    return model_query(
        context, models.ErasureCodeProfile, read_deleted='no', session=session)

def ec_profile_create(context, values, session=None):

    if not session:
        session = get_session()

    with session.begin(subtransactions=True):
        ec_profile_ref = models.ErasureCodeProfile()
        session.add(ec_profile_ref)
        ec_profile_ref.update(values)
    return ec_profile_ref 

def ec_profile_update(context, profile_id, values, session=None):
    if not session:
        session = get_session()
    with session.begin():
        ec_profile_ref = _ec_profile_query(context, session=session).\
            filter_by(id=profile_id).\
            first()
        values['updated_at'] = timeutils.utcnow()
        convert_datetimes(values, 'created_at', 'deleted_at', 'updated_at')
        ec_profile_ref.update(values)
        ec_profile_ref.save(session=session)
    return ec_profile_ref 

def ec_profile_update_or_create(context, values, session=None):
    if not session:
        session = get_session()

    if not values.get('name'):
        return None

    profile_ref = ec_profile_get_by_name(context, values['name'], session=session)

    if profile_ref:
        profile = ec_profile_update(context, profile_ref['id'], values, session=session)
    else:
        profile = ec_profile_create(context, values, session=session)
    return profile 

def ec_profile_get_all(context):
    return _ec_profile_query(context).all()

def ec_profile_get(context, ec_profile_id):
    result = _ec_profile_query(context).\
                    filter_by(id=ec_profile_id).\
                    first()

    if not result:
        raise exception.ECProfileNotFound(ec_profile_id=ec_profile_id)

    return result

def ec_profile_get_by_name(context, name, session=None):
    return _ec_profile_query(context, session).\
        filter_by(name=name).\
        first()

def performance_metrics_query(context, search_opts, session=None):
    metrics_name = search_opts.has_key('metrics_name') and search_opts['metrics_name'] or ''
    host_name = search_opts.has_key('host_name') and search_opts['host_name'] or ''
    timestamp_start = search_opts.has_key('timestamp_start') and search_opts['timestamp_start'] or None
    timestamp_end = search_opts.has_key('timestamp_end') and search_opts['timestamp_end'] or None

    metrics_query = model_query(
        context, models.CephPerformanceMetric, read_deleted='yes', session=session)
    if metrics_name:
        metrics_query = metrics_query.filter(models.CephPerformanceMetric.metric==metrics_name)
    if host_name:
        metrics_query = metrics_query.filter(models.CephPerformanceMetric.hostname==host_name)
    if timestamp_start:
        metrics_query = metrics_query.filter(models.CephPerformanceMetric.timestamp>timestamp_start)
    if timestamp_end:
        metrics_query = metrics_query.filter(models.CephPerformanceMetric.timestamp<timestamp_end)
    return metrics_query.all()

def sum_performance_metrics(context, search_opts, session=None):#for iops bandwidth
    metrics_name =  search_opts['metrics_name']
    #host_name = search_opts['host_name'] or ''
    timestamp_start = search_opts.has_key('timestamp_start') and int(search_opts['timestamp_start']) or None
    timestamp_end = search_opts.has_key('timestamp_end') and int(search_opts['timestamp_end']) or None
    correct_cnt = search_opts.has_key('correct_cnt') and int(search_opts['correct_cnt']) or None
    if timestamp_start is None and timestamp_end:
        timestamp_start = timestamp_end - 15
    elif timestamp_start  and  timestamp_end is None:
        timestamp_end = timestamp_start + 15
    ret_list = []
    timestamp_cur = timestamp_start
    while timestamp_cur<timestamp_end:
        metrics_query = model_query(\
            context, models.CephPerformanceMetric, func.sum(models.CephPerformanceMetric.value), func.count(models.CephPerformanceMetric.value), read_deleted='yes', session=session)\
            .filter(models.CephPerformanceMetric.metric==metrics_name).filter(models.CephPerformanceMetric.timestamp>timestamp_cur).filter(models.CephPerformanceMetric.timestamp<timestamp_cur+15)
        sql_ret = metrics_query.all()[0]
        if correct_cnt:
            metrics_value =  sql_ret[1]/sql_ret[2]*correct_cnt
        else:
            metrics_value = sql_ret[1]
        sql_ret_dict = {'timestamp':str(timestamp_cur),'metrics_value':metrics_value,'metrics':metrics_name,}
        ret_list.append(sql_ret_dict)
        timestamp_cur = timestamp_cur + 15

    return ret_list

def lantency_performance_metrics(context, search_opts, session=None):#for iops bandwidth
    timestamp_start = search_opts.has_key('timestamp_start') and int(search_opts['timestamp_start']) or None
    timestamp_end = search_opts.has_key('timestamp_end') and int(search_opts['timestamp_end']) or None
    if timestamp_start is None and timestamp_end:
        timestamp_start = timestamp_end - 15
    elif timestamp_start  and  timestamp_end is None:
        timestamp_end = timestamp_start + 15
    ret_list = []
    timestamp_cur = timestamp_start
    session = get_session()
    while timestamp_cur<timestamp_end:
        sql_str = '''
            select  sum(iops_value) as sum_iops,sum(lantency_value* iops_value) as total_lantency  from \
            (\
              (select  metric,hostname,instance,timestamp,value as iops_value from metrics where metric='iops') as iopstable \
              inner join (select  metric,hostname,instance,timestamp,value as lantency_value from metrics where metric='latency') as latencytable \
            on iopstable.timestamp=latencytable.timestamp and iopstable.hostname=latencytable.hostname and iopstable.instance=latencytable.instance \
            )
            where iopstable.timestamp > %s and  iopstable.timestamp < %s;
            '''%(timestamp_cur,timestamp_cur+15)
        timestamp_cur = timestamp_cur + 15
        sql_ret = session.execute(sql_str).fetchall()[0]
        if sql_ret[0] and sql_ret[1]:
            metrics_value =  sql_ret[1]/sql_ret[0]
            ret_list.append({'timestamp':str(timestamp_cur),'metrics_value':metrics_value,'metrics':'lantency',})
    return ret_list
#endregion

