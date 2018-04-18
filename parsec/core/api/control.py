from parsec.networking import ClientContext
from parsec.schema import BaseCmdSchema, fields
from parsec.core.app import Core
from parsec.core.fuse_manager import (
    FuseNotAvailable, FuseAlreadyStarted, FuseNotStarted
)
from parsec.core.backend_connection import BackendNotAvailable
from parsec.core.devices_manager import DeviceLoadingError
from parsec.utils import ParsecError, to_jsonb64, from_jsonb64, ejson_dumps


class PathOnlySchema(BaseCmdSchema):
    path = fields.String(required=True)


class cmd_LOGIN_Schema(BaseCmdSchema):
    id = fields.String(required=True)
    password = fields.String(missing=None)


class cmd_FUSE_START_Schema(BaseCmdSchema):
    mountpoint = fields.String(required=True)


async def login(req: dict, client_ctx: ClientContext, core: Core) -> dict:
    if core.auth_device:
        return {"status": "already_logged", "reason": "Already logged"}

    msg = cmd_LOGIN_Schema().load_or_abort(req)
    try:
        device = core.devices_manager.load_device(msg["id"], msg["password"])
    except DeviceLoadingError:
        return {"status": "unknown_user", "reason": "Unknown user"}

    await core.login(device)
    return {"status": "ok"}


async def logout(req: dict, client_ctx: ClientContext, core: Core) -> dict:
    if not core.auth_device:
        return {"status": "login_required", "reason": "Login required"}

    await core.logout()
    return {"status": "ok"}


async def info(req: dict, client_ctx: ClientContext, core: Core) -> dict:
    return {
        "status": "ok",
        # TODO: replace by `logged_in`
        "loaded": bool(core.auth_device),
        # TODO: replace by `device_id` ?
        "id": core.auth_device.id if core.auth_device else None,
    }


async def list_available_logins(
    req: dict, client_ctx: ClientContext, core: Core
) -> dict:
    devices = core.devices_manager.list_available_devices()
    return {"status": "ok", "devices": devices}


async def get_core_state(req: dict, client_ctx: ClientContext, core: Core) -> dict:
    status = {"status": "ok", "login": None, "backend_online": False}
    if core.auth_device:
        status["login"] = core.auth_device.id
        try:
            await core.backend_connection.ping()
            status["backend_online"] = True
        except BackendNotAvailable:
            status["backend_online"] = False
    return status


# TODO: create a fuse module to handle fusepy/libfuse availability


async def fuse_start(req: dict, client_ctx: ClientContext, core: Core) -> dict:
    if not core.auth_device:
        return {"status": "login_required", "reason": "Login required"}

    msg = cmd_FUSE_START_Schema().load_or_abort(req)

    try:
        await core.fuse_manager.start_mountpoint(msg["mountpoint"])
    except FuseNotAvailable as exc:
        return {"status": "fuse_not_available", "reason": str(exc)}

    except FuseAlreadyStarted as exc:
        return {"status": "fuse_already_started", "reason": str(exc)}

    return {"status": "ok"}


async def fuse_stop(req: dict, client_ctx: ClientContext, core: Core) -> dict:
    if not core.auth_device:
        return {"status": "login_required", "reason": "Login required"}

    BaseCmdSchema().load_or_abort(req)  # empty msg expected

    try:
        await core.fuse_manager.stop_mountpoint()
    except FuseNotAvailable as exc:
        return {"status": "fuse_not_available", "reason": str(exc)}

    except FuseNotStarted as exc:
        return {"status": "fuse_not_started", "reason": str(exc)}

    return {"status": "ok"}


async def fuse_open(req: dict, client_ctx: ClientContext, core: Core) -> dict:
    if not core.auth_device:
        return {"status": "login_required", "reason": "Login required"}

    msg = PathOnlySchema().load_or_abort(req)

    try:
        core.fuse_manager.open_file(msg["path"])
    except FuseNotAvailable as exc:
        return {"status": "fuse_not_available", "reason": str(exc)}

    except FuseNotStarted as exc:
        return {"status": "fuse_not_started", "reason": str(exc)}

    return {"status": "ok"}