# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPLv3 2019 Scille SAS

from parsec.serde import BaseSchema, fields, validate
from parsec.api.protocol.base import BaseReqSchema, BaseRepSchema, CmdSerializer
from parsec.api.protocol.types import DeviceIDField


__all__ = (
    "vlob_create_serializer",
    "vlob_read_serializer",
    "vlob_update_serializer",
    "vlob_poll_changes_serializer",
    "vlob_list_versions_serializer",
    "vlob_history_serializer",
    "vlob_maintenance_get_reencryption_batch_serializer",
    "vlob_maintenance_save_reencryption_batch_serializer",
)


_validate_version = validate.Range(min=1)


class VlobCreateReqSchema(BaseReqSchema):
    realm_id = fields.UUID(required=True)
    encryption_revision = fields.Integer(required=True)
    vlob_id = fields.UUID(required=True)
    # If blob contains a signed message, it timestamp cannot be directly enforced
    # by the backend (given the message is probably also encrypted).
    # Hence the timestamp is passed in clear so backend can reject the message
    # if it considers the timestamp invalid. On top of that each client asking
    # for the message will receive the declared timestamp to check against
    # the actual timestamp within the message.
    timestamp = fields.DateTime(required=True)
    blob = fields.Bytes(required=True)
    signature = fields.Bytes(required=True)


class VlobCreateRepSchema(BaseRepSchema):
    pass


vlob_create_serializer = CmdSerializer(VlobCreateReqSchema, VlobCreateRepSchema)


class VlobReadReqSchema(BaseReqSchema):
    encryption_revision = fields.Integer(required=True)
    vlob_id = fields.UUID(required=True)
    version = fields.Integer(validate=lambda n: n is None or _validate_version(n), missing=None)
    timestamp = fields.DateTime(allow_none=True, missing=None)
    signature = fields.Bytes(required=True)


class VlobReadRepSchema(BaseRepSchema):
    version = fields.Integer(required=True, validate=_validate_version)
    blob = fields.Bytes(required=True)
    author = DeviceIDField(required=True)
    timestamp = fields.DateTime(required=True)


vlob_read_serializer = CmdSerializer(VlobReadReqSchema, VlobReadRepSchema)


class VlobUpdateReqSchema(BaseReqSchema):
    encryption_revision = fields.Integer(required=True)
    vlob_id = fields.UUID(required=True)
    timestamp = fields.DateTime(required=True)
    version = fields.Integer(required=True, validate=_validate_version)
    blob = fields.Bytes(required=True)
    signature = fields.Bytes(required=True)


class VlobUpdateRepSchema(BaseRepSchema):
    pass


vlob_update_serializer = CmdSerializer(VlobUpdateReqSchema, VlobUpdateRepSchema)


class VlobPollChangesReqSchema(BaseReqSchema):
    realm_id = fields.UUID(required=True)
    last_checkpoint = fields.Integer(required=True)


class VlobPollChangesRepSchema(BaseRepSchema):
    changes = fields.Map(fields.UUID(), fields.Integer(required=True), required=True)
    current_checkpoint = fields.Integer(required=True)


vlob_poll_changes_serializer = CmdSerializer(VlobPollChangesReqSchema, VlobPollChangesRepSchema)


# List available vlobs
class VlobListVersionsReqSchema(BaseReqSchema):
    vlob_id = fields.UUID(required=True)


class VlobListVersionsRepSchema(BaseRepSchema):
    versions = fields.Map(
        fields.Integer(required=True),
        fields.Tuple(fields.DateTime(required=True), DeviceIDField(required=True)),
        required=True,
    )


vlob_list_versions_serializer = CmdSerializer(VlobListVersionsReqSchema, VlobListVersionsRepSchema)


class HistoryEntrySchema(BaseSchema):
    version = fields.Integer(required=True)
    author = DeviceIDField(required=True)
    timestamp = fields.DateTime(required=True, allow_none=True)
    hash_obj_after_operation = fields.String(required=True)
    hash_prev_digest = fields.String(required=True)
    signature = fields.Bytes(required=True)
    is_read_op = fields.Boolean(required=True)


class VlobHistoryReqSchema(BaseReqSchema):
    vlob_id = fields.UUID(required=True)
    after_version = fields.Integer(required=True)
    before_version = fields.Integer(required=True)


class VlobHistoryRepSchema(BaseRepSchema):
    history = fields.List(fields.Nested(HistoryEntrySchema), required=True)


vlob_history_serializer = CmdSerializer(VlobHistoryReqSchema, VlobHistoryRepSchema)

# Maintenance stuff


class VlobMaintenanceGetReencryptionBatchReqSchema(BaseReqSchema):
    realm_id = fields.UUID(required=True)
    encryption_revision = fields.Integer(required=True)
    size = fields.Integer(required=True, validate=validate.Range(min=0, max=1000))


class ReencryptionBatchEntrySchema(BaseSchema):
    vlob_id = fields.UUID(required=True)
    version = fields.Integer(required=True, validate=validate.Range(min=0))
    blob = fields.Bytes(required=True)


class VlobMaintenanceGetReencryptionBatchRepSchema(BaseRepSchema):
    batch = fields.List(fields.Nested(ReencryptionBatchEntrySchema), required=True)


vlob_maintenance_get_reencryption_batch_serializer = CmdSerializer(
    VlobMaintenanceGetReencryptionBatchReqSchema, VlobMaintenanceGetReencryptionBatchRepSchema
)


class VlobMaintenanceSaveReencryptionBatchReqSchema(BaseReqSchema):
    realm_id = fields.UUID(required=True)
    encryption_revision = fields.Integer(required=True)
    batch = fields.List(fields.Nested(ReencryptionBatchEntrySchema), required=True)


class VlobMaintenanceSaveReencryptionBatchRepSchema(BaseRepSchema):
    total = fields.Integer(required=True)
    done = fields.Integer(required=True)


vlob_maintenance_save_reencryption_batch_serializer = CmdSerializer(
    VlobMaintenanceSaveReencryptionBatchReqSchema, VlobMaintenanceSaveReencryptionBatchRepSchema
)
