# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

"""Vsm base exception handling.

Includes decorator for re-raising Vsm-type exceptions.

SHOULD include dedicated exception logging.

"""

from oslo.config import cfg
import webob.exc

from vsm import flags
from vsm.openstack.common.gettextutils import _
from vsm.openstack.common import log as logging

LOG = logging.getLogger(__name__)

exc_log_opts = [
    cfg.BoolOpt('fatal_exception_format_errors',
                default=False,
                help='make exception message format errors fatal'),
]

FLAGS = flags.FLAGS
FLAGS.register_opts(exc_log_opts)

class ConvertedException(webob.exc.WSGIHTTPException):
    def __init__(self, code=0, title="", explanation=""):
        self.code = code
        self.title = title
        self.explanation = explanation
        super(ConvertedException, self).__init__()

class ProcessExecutionError(IOError):
    def __init__(self, stdout=None, stderr=None, exit_code=None, cmd=None,
                 description=None):
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        self.cmd = cmd
        self.description = description

        if description is None:
            description = _('Unexpected error while running command.')
        if exit_code is None:
            exit_code = '-'
        message = _('%(description)s\nCommand: %(cmd)s\n'
                    'Exit code: %(exit_code)s\nStdout: %(stdout)r\n'
                    'Stderr: %(stderr)r') % locals()
        IOError.__init__(self, message)

class Error(Exception):
    pass

class DBError(Error):
    code="E-5081"
    """Wraps an implementation specific exception."""
    def __init__(self, inner_exception=None):
        self.inner_exception = inner_exception
        super(DBError, self).__init__(str(inner_exception))

def wrap_db_error(f):
    def _wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except UnicodeEncodeError:
            raise InvalidUnicodeParameter()
        except Exception, e:
            LOG.exception(_('DB exception wrapped.'))
            raise DBError(e)
    _wrap.func_name = f.func_name
    return _wrap

class VsmException(Exception):
    """Base Vsm Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    """
    message = _("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.message % kwargs

            except Exception as e:
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception(_('Exception in string format operation'))
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))
                if FLAGS.fatal_exception_format_errors:
                    raise e
                else:
                    # at least get the core message out if something happened
                    message = self.message

        super(VsmException, self).__init__(message)

class GlanceConnectionFailed(VsmException):
    message = _("Connection to glance failed") + ": %(reason)s"

class NotAuthorized(VsmException):
    message = _("Not authorized.")
    code = 403

class AdminRequired(NotAuthorized):
    code = "E-8849"
    message = _("User does not have admin privileges")

class PolicyNotAuthorized(NotAuthorized):
    message = _("Policy doesn't allow %(action)s to be performed.")

class ImageNotAuthorized(VsmException):
    message = _("Not authorized for image %(image_id)s.")

class AppNodeNotAuthorized(NotAuthorized):
    message = _("Not authorized for Appnodes.")

class Invalid(VsmException):
    message = _("Unacceptable parameters.")
    code = 400

class InvalidSnapshot(Invalid):
    message = _("Invalid snapshot") + ": %(reason)s"

class HardwareAttached(Invalid):
    message = _("Hardware %(storage_id)s is still attached, detach storage first.")

class SfJsonEncodeFailure(VsmException):
    message = _("Failed to load data into json format")

class InvalidRequest(Invalid):
    message = _("The request is invalid.")

class InvalidResults(Invalid):
    message = _("The results are invalid.")

class InvalidInput(Invalid):
    message = _("Invalid input received") + ": %(reason)s"

class InvalidHardwareType(Invalid):
    message = _("Invalid storage type") + ": %(reason)s"

class InvalidHardware(Invalid):
    message = _("Invalid storage") + ": %(reason)s"

class InvalidPortRange(Invalid):
    message = _("Invalid port range %(from_port)s:%(to_port)s. %(msg)s")

class InvalidContentType(Invalid):
    message = _("Invalid content type %(content_type)s.")

class InvalidUnicodeParameter(Invalid):
    message = _("Invalid Parameter: "
                "Unicode is not supported by the current database.")

# Cannot be templated as the error syntax varies.
# msg needs to be constructed when raised.
class InvalidParameterValue(Invalid):
    message = _("%(err)s")

class ServiceUnavailable(Invalid):
    code = "E-86EE"
    message = _("Service is unavailable at this time.")

class VsmServiceUnavailable(ServiceUnavailable):
    code ="E-7B58"
    message = _("Vsm service is unavailable at this time.")

class ImageUnacceptable(Invalid):
    message = _("Image %(image_id)s is unacceptable: %(reason)s")

class InvalidUUID(Invalid):
    message = _("Expected a uuid but received %(uuid).")

class NotFound(VsmException):
    message = _("Resource could not be found.")
    code = 404
    safe = True

class PersistentHardwareFileNotFound(NotFound):
    message = _("Hardware %(storage_id)s persistence file could not be found.")

class HardwareNotFound(NotFound):
    message = _("Hardware %(storage_id)s could not be found.")

class SfAccountNotFound(NotFound):
    message = _("Unable to locate account %(account_name)s on "
                "Solidfire device")

class HardwareNotFoundForInstance(HardwareNotFound):
    message = _("Hardware not found for instance %(instance_id)s.")

class HardwareMetadataNotFound(NotFound):
    message = _("Hardware %(storage_id)s has no metadata with "
                "key %(metadata_key)s.")

class InvalidHardwareMetadata(Invalid):
    message = _("Invalid metadata") + ": %(reason)s"

class InvalidHardwareMetadataSize(Invalid):
    message = _("Invalid metadata size") + ": %(reason)s"

class SnapshotMetadataNotFound(NotFound):
    message = _("Snapshot %(snapshot_id)s has no metadata with "
                "key %(metadata_key)s.")

class InvalidSnapshotMetadata(Invalid):
    message = _("Invalid metadata") + ": %(reason)s"

class InvalidSnapshotMetadataSize(Invalid):
    message = _("Invalid metadata size") + ": %(reason)s"

class HardwareTypeNotFound(NotFound):
    message = _("Hardware type %(storage_type_id)s could not be found.")

class HardwareTypeNotFoundByName(HardwareTypeNotFound):
    message = _("Hardware type with name %(storage_type_name)s "
                "could not be found.")

class HardwareTypeExtraSpecsNotFound(NotFound):
    message = _("Hardware Type %(storage_type_id)s has no extra specs with "
                "key %(extra_specs_key)s.")

class SnapshotNotFound(NotFound):
    message = _("Snapshot %(snapshot_id)s could not be found.")

class HardwareIsBusy(VsmException):
    message = _("deleting storage %(storage_name)s that has snapshot")

class SnapshotIsBusy(VsmException):
    message = _("deleting snapshot %(snapshot_name)s that has "
                "dependent storages")

class ISCSITargetNotFoundForHardware(NotFound):
    message = _("No target id found for storage %(storage_id)s.")

class ISCSITargetCreateFailed(VsmException):
    message = _("Failed to create iscsi target for storage %(storage_id)s.")

class ISCSITargetAttachFailed(VsmException):
    message = _("Failed to attach iSCSI target for storage %(storage_id)s.")

class ISCSITargetRemoveFailed(VsmException):
    message = _("Failed to remove iscsi target for storage %(storage_id)s.")

class DiskNotFound(NotFound):
    code = "E-1C1A"
    message = _("No disk at %(location)s")

class InvalidImageRef(Invalid):
    message = _("Invalid image href %(image_href)s.")

class ImageNotFound(NotFound):
    message = _("Image %(image_id)s could not be found.")

class ServiceNotFound(NotFound):
    code = "E-F158"
    message = _("Service %(service_id)s could not be found.")

class HostNotFound(NotFound):
    code = "E-5B0E"
    message = _("Host %(host)s could not be found.")

#add vsm exception

class VsmHostNotFound(HostNotFound):
    code = "E-3F38"
    message = _("Vsm host %(host)s could not be found.")

class OsdNotFound(NotFound):
    code = "E-B676"
    message = _("Osd %(osd)s could not be found.")

class VsmOsdNotFound(OsdNotFound):
    code = "E-EC04"
    message = _("Osd %(osd)s could not be found.")

class VsmStorageGroupNotFound(NotFound):
    code = "E-352E"
    message = _("storagegroup %(group)% could not be found.")

#add vsm exception

class SchedulerHostFilterNotFound(NotFound):
    message = _("Scheduler Host Filter %(filter_name)s could not be found.")

class SchedulerHostWeigherNotFound(NotFound):
    message = _("Scheduler Host Weigher %(weigher_name)s could not be found.")

class HostBinaryNotFound(NotFound):
    message = _("Could not find binary %(binary)s on host %(host)s.")

class InvalidReservationExpiration(Invalid):
    message = _("Invalid reservation expiration %(expire)s.")

class InvalidQuotaValue(Invalid):
    message = _("Change would make usage less than 0 for the following "
                "resources: %(unders)s")

class QuotaNotFound(NotFound):
    message = _("Quota could not be found")

class QuotaResourceUnknown(QuotaNotFound):
    message = _("Unknown quota resources %(unknown)s.")

class ProjectQuotaNotFound(QuotaNotFound):
    message = _("Quota for project %(project_id)s could not be found.")

class QuotaClassNotFound(QuotaNotFound):
    message = _("Quota class %(class_name)s could not be found.")

class QuotaUsageNotFound(QuotaNotFound):
    message = _("Quota usage for project %(project_id)s could not be found.")

class ReservationNotFound(QuotaNotFound):
    message = _("Quota reservation %(uuid)s could not be found.")

class OverQuota(VsmException):
    message = _("Quota exceeded for resources: %(overs)s")

class MigrationNotFound(NotFound):
    message = _("Migration %(migration_id)s could not be found.")

class MigrationNotFoundByStatus(MigrationNotFound):
    message = _("Migration not found for instance %(instance_id)s "
                "with status %(status)s.")

class FileNotFound(NotFound):
    code = "E-D55E"
    message = _("File %(file_path)s could not be found.")

class ClassNotFound(NotFound):
    message = _("Class %(class_name)s could not be found: %(exception)s")

class NotAllowed(VsmException):
    message = _("Action not allowed.")

#TODO(bcwaldon): EOL this exception!
class Duplicate(VsmException):
    pass

class KeyPairExists(Duplicate):
    message = _("Key pair %(key_name)s already exists.")

class HardwareTypeExists(Duplicate):
    message = _("Hardware Type %(id)s already exists.")

class MigrationError(VsmException):
    message = _("Migration error") + ": %(reason)s"

class MalformedRequestBody(VsmException):
    message = _("Malformed message body: %(reason)s")

class ConfigNotFound(NotFound):
    code = "E-89AF"
    message = _("Could not find config at %(path)s")

class PasteAppNotFound(NotFound):
    message = _("Could not load paste app '%(name)s' from %(path)s")

class NoValidHost(VsmException):
    code = "E-6550"
    message = _("No valid host was found. %(reason)s")

class WillNotSchedule(VsmException):
    message = _("Host %(host)s is not up or doesn't exist.")

class QuotaError(VsmException):
    message = _("Quota exceeded") + ": code=%(code)s"
    code = 413
    headers = {'Retry-After': 0}
    safe = True

class HardwareSizeExceedsAvailableQuota(QuotaError):
    message = _("Requested storage or snapshot exceeds "
                "allowed Gigabytes quota")

class HardwareSizeExceedsQuota(QuotaError):
    message = _("Maximum storage/snapshot size exceeded")

class HardwareLimitExceeded(QuotaError):
    message = _("Maximum number of storages allowed (%(allowed)d) exceeded")

class SnapshotLimitExceeded(QuotaError):
    message = _("Maximum number of snapshots allowed (%(allowed)d) exceeded")

class DuplicateSfHardwareNames(Duplicate):
    message = _("Detected more than one storage with name %(vol_name)s")

class DuplicateControllerIPs(VsmException):
    code = "E-848B"
    message = _("More than one Controller IP exists: %(err)s.  %(info)s")

class Duplicate3PARHost(VsmException):
    message = _("3PAR Host already exists: %(err)s.  %(info)s")

class HardwareTypeCreateFailed(VsmException):
    message = _("Cannot create storage_type with "
                "name %(name)s and specs %(extra_specs)s")

class SolidFireAPIException(VsmException):
    message = _("Bad response from SolidFire API")

class SolidFireAPIDataException(SolidFireAPIException):
    message = _("Error in SolidFire API response: data=%(data)s")

class UnknownCmd(Invalid):
    code = "E-94FF"
    message = _("Unknown or unsupported command %(cmd)s")

class MalformedResponse(Invalid):
    message = _("Malformed response to command %(cmd)s: %(reason)s")

class BadHTTPResponseStatus(VsmException):
    code = "E-CDB5"
    message = _("Bad HTTP response status %(status)s")

class FailedCmdWithDump(VsmException):
    message = _("Operation failed with status=%(status)s. Full dump: %(data)s")

class ZadaraServerCreateFailure(VsmException):
    message = _("Unable to create server object for initiator %(name)s")

class ZadaraServerNotFound(NotFound):
    message = _("Unable to find server object for initiator %(name)s")

class ZadaraVPSANoActiveController(VsmException):
    message = _("Unable to find any active VPSA controller")

class ZadaraAttachmentsNotFound(NotFound):
    message = _("Failed to retrieve attachments for storage %(name)s")

class ZadaraInvalidAttachmentInfo(Invalid):
    message = _("Invalid attachment info for storage %(name)s: %(reason)s")

class InstanceNotFound(NotFound):
    message = _("Instance %(instance_id)s could not be found.")

class HardwareBackendAPIException(VsmException):
    message = _("Bad or unexpected response from the storage storage "
                "backend API: %(data)s")

class NfsException(VsmException):
    message = _("Unknown NFS exception")

class NfsNoSharesMounted(NotFound):
    message = _("No mounted NFS shares found")

class NfsNoSuitableShareFound(NotFound):
    message = _("There is no share which can host %(storage_size)sG")

class GlusterfsException(VsmException):
    message = _("Unknown Gluster exception")

class GlusterfsNoSharesMounted(NotFound):
    message = _("No mounted Gluster shares found")

class GlusterfsNoSuitableShareFound(NotFound):
    message = _("There is no share which can host %(storage_size)sG")

class GlanceMetadataExists(Invalid):
    message = _("Glance metadata cannot be updated, key %(key)s"
                " exists for storage id %(storage_id)s")

class ImageCopyFailure(Invalid):
    message = _("Failed to copy image to storage")

class BackupNotFound(NotFound):
    message = _("Backup %(backup_id)s could not be found.")

class InvalidBackup(Invalid):
    message = _("Invalid backup: %(reason)s")

class SwiftConnectionFailed(VsmException):
    message = _("Connection to swift failed") + ": %(reason)s"

class AppNodeNotFound(NotFound):
    message = _("App Node %(appnode_id) could not be found.")

class VsmappNotFound(NotFound):
    code = "E-AB30"
    message = _("Vsm app could not be found under the account.")

class AppNodeInvalidInfo(Invalid):
    message = _("Invalid request for App nodes.")

class DuplicateAppnode(VsmException):
    message = _("App node %(ip) already exists: %(err)s.")

class AppNodeFailure(VsmException):
    message = _("Failure on app nodes db operations") + ": %(reason)s"

class DuplicateVsmApp(VsmException):
    message = _("Vsmapp for project %(id) already exists: %(err)s.")

class DuplicateStoragePoolUsage(VsmException):
    message = _("The storage pool %(pool_id) has been presented: %(err).")

class StoragePoolUsageNotFound(NotFound):
    code = "E-1EAF"
    message = _('The storage pool usage could not be found.')

class StoragePoolUsageFailure(VsmException):
    code = "E-80F6"
    message = _('Failure on storage pool usage operations.')

class StatusTrackingError(VsmException):
    message = _('Status traceking Error.')

class StoragePoolUsageInvalid(Invalid):
    code = "E-FF52"
    message = _("Invalid request for Storage pool usages.")

class SummaryNotFound(NotFound):
    code = "E-A067"
    message = _("%(type) summary could not be found.")

class MonitorNotFound(NotFound):
    code = "E-87CA"
    message = _("monitor %(name) could not be found.")

class PGExists(VsmException):
    code = "E-9B97"
    message = _("The PG already exists.")

class PGNotFound(NotFound):
    code = "E-483842BE"
    message = _("The PG id %(pg_id) could not be found.")

class RBDExists(VsmException):
    code = "E-FC23"
    message = _("The RBD already exists.")

class RBDNotFound(NotFound):
    code = "E-567C"
    message = _("The RBD id %(rbd_id) could not be found.")

class MDSExists(VsmException):
    code = "E-6BD1"
    message = _("The MDS already exists.")

class MDSNotFound(NotFound):
    code = "E-6E62"
    message = _("The MDS id %(mds_id) could not be found.")

class ECProfileNotFound(NotFound):
    code = "E-6E1B" 
    message = _("The erasure code profile id %(ec_profile_id) could not be found.")

#    from vsm import exception
#    try:
#        raise exception.CreateStorageGroupFailed
#    except Exception, e:
#        LOG.error("%s: %s" %(e.code, e.message))

class MonitorException(VsmException):
    code = "E-A5B9"
    message = _("Monitor Exception")

class MonitorAddFailed(MonitorException):
    code = "E-47AE"
    message = _("Monitor Add Failed")

class MonitorRemoveFailed(MonitorException):
    code = "E-A4CA"
    message = _("Monitor Remove Failed")

class MonitorStartFailed(MonitorException):
    code = "E-0141"
    message = _("Monitor Start Failed")

class MonitorStopFailed(MonitorException):
    code = "E-A206"
    message = _("Monitor Stop Failed")

class StorageServerException(VsmException):
    code = "E-C79B"
    message = _("Storage Server Exception")

class StorageServerAddFailed(StorageServerException):
    code = "E-3200"
    message = _("Storage Server Add Failed")

class StorageServerRemoveFailed(StorageServerException):
    code = "E-F228"
    message = _("Storage Server Remove Failed")

class StorageServerStartFailed(StorageServerException):
    code = "E-1002"
    message = _("Storage Server Start Failed")

class StorageServerStopFailed(StorageServerException):
    code = "E-90FD"
    message = _("Storage Server Stop Failed")

class DeviceException(VsmException):
    code = "E-5682"
    message = _("Device Exception")

class DeviceAddFailed(DeviceException):
    code = "E-98E9"
    message = _("Device Add Failed")

class DeviceRemoveFailed(DeviceException):
    code = "E-7479"
    message = _("Device Remove Failed")

class DeviceStartFailed(DeviceException):
    code = "E-81C1"
    message = _("Device Start Failed")

class DeviceStopFailed(DeviceException):
    code = "E-0667"
    message = _("Device Stop Failed")

class StorageGroupException(VsmException):
    code = "E-39ED"
    message = _("Storage Group Exception")

class StorageGroupAddFailed(StorageGroupException):
    code = "E-9390"
    message = _("Storage Group Add Failed")

class PresentOpenStackException(VsmException):
    code = "E-CA97"
    message = _("Present Openstack Exception")

class AddPoolToOpenStackFailed(PresentOpenStackException):
    code = "E-3CC2"
    message = _("Add Pool To Openstack Failed")

class PathNotExist(VsmException):
    code = "E-C3C7"
    message = _("Path does't exist!")

class UpdateDBError(VsmException):
    code = "E-B869"
    message = _("Update DB error!")

class ExeCmdError(VsmException):
    code = "E-1E4C"
    message = _("Execute cmd error!")

class CephConfException(VsmException):
    code = "E-6CF6"
    message = _("Ceph config error!")

class LoadCephConfFailed(CephConfException):
    code = "E-C785"
    message = _("Load ceph config failed!")

class AddGlobalToCephConfFailed(CephConfException):
    code = "E-07C1"
    message = _("Add global item to ceph config failed!")

class AddMonToCephConfFailed(CephConfException):
    code = "E-3373"
    message = _("Add mon item to ceph config failed!")

class AddMdsToCephConfFailed(CephConfException):
    code = "E-691F"
    message = _("Add mds item to ceph config failed!")

class AddOsdToCephConfFailed(CephConfException):
    code = "E-BF96"
    message = _("Add osd item to ceph config failed!")

class GetNoneError(VsmException):
    code = "E-86A2"
    message = _("Get None error!")

class StartCephFaild(VsmException):
    code = "E-3994"
    message = _("Start ceph cluster Failed!")
