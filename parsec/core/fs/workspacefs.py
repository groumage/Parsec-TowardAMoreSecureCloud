# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPLv3 2019 Scille SAS

import math
import inspect
from typing import Tuple

from parsec.core.types import FsPath, AccessID, FileDescriptor
from parsec.core.fs.file_transactions import FileTransactions
from parsec.core.fs.entry_transactions import EntryTransactions
from parsec.core.fs.local_folder_fs import FSManifestLocalMiss, FSMultiManifestLocalMiss

# from parsec.core.fs.exceptions import FSBackendOfflineError, FSError
# from parsec.core.backend_connection import BackendNotAvailable, BackendConnectionError


class WorkspaceFS:
    def __init__(
        self,
        workspace_entry,
        device,
        local_storage,
        backend_cmds,
        event_bus,
        _local_folder_fs,
        _remote_loader,
        _syncer,
    ):
        self.workspace_entry = workspace_entry
        self.device = device
        self.local_storage = local_storage
        self.backend_cmds = backend_cmds
        self.event_bus = event_bus
        self._local_folder_fs = _local_folder_fs
        self._remote_loader = _remote_loader
        self._syncer = _syncer

        self._file_transactions = FileTransactions(local_storage, self._remote_loader, event_bus)
        self._entry_transactions = EntryTransactions(
            self.device, workspace_entry, local_storage, self._remote_loader, event_bus
        )

    @property
    def workspace_name(self):
        return self.workspace_entry.name

    # Workspace info

    async def workspace_info(self):
        # try:
        #     user_roles = await self.backend_cmds.vlob_group_get_roles(
        #         self.workspace_entry.access.id
        #     )

        # except BackendNotAvailable as exc:
        #     raise FSBackendOfflineError(str(exc)) from exc

        # except BackendConnectionError as exc:
        #     raise FSError(f"Cannot retreive workspace's vlob group rights: {exc}") from exc

        # TODO: finish me !
        try:
            manifest = self.local_storage.get_manifest(self.workspace_entry.access)
        except FSManifestLocalMiss as exc:
            manifest = await self._remote_loader.load_manifest(exc.access)
        return {
            "role": self.workspace_entry.role,
            "creator": manifest.creator,
            "participants": list(manifest.participants),
        }

    # Entry operations

    async def entry_info(self, path: FsPath) -> dict:
        return await self._entry_transactions.entry_info(path)

    async def entry_rename(self, src: FsPath, dst: FsPath, overwrite: bool = True) -> AccessID:
        return await self._entry_transactions.entry_rename(src, dst, overwrite)

    # Folder operations

    async def folder_create(self, path: FsPath) -> AccessID:
        return await self._entry_transactions.folder_create(path)

    async def folder_delete(self, path: FsPath) -> AccessID:
        return await self._entry_transactions.folder_delete(path)

    # File operations

    async def file_create(self, path: FsPath, open: bool = True) -> Tuple[AccessID, FileDescriptor]:
        return await self._entry_transactions.file_create(path, open=open)

    async def file_open(self, path: FsPath, mode="rw") -> Tuple[AccessID, FileDescriptor]:
        return await self._entry_transactions.file_open(path, mode=mode)

    async def file_delete(self, path: FsPath) -> AccessID:
        return await self._entry_transactions.file_delete(path)

    # File descriptor operations

    async def fd_close(self, fd: int) -> None:
        await self._file_transactions.fd_close(fd)

    async def fd_seek(self, fd: int, offset: int) -> None:
        await self._file_transactions.fd_seek(fd, offset)

    async def fd_resize(self, fd: int, length: int) -> None:
        await self._file_transactions.fd_resize(fd, length)

    async def fd_write(self, fd: int, content: bytes, offset: int = None) -> int:
        return await self._file_transactions.fd_write(fd, content, offset)

    async def fd_flush(self, fd: int) -> None:
        await self._file_transactions.fd_flush(fd)

    async def fd_read(self, fd: int, size: int = -1, offset: int = None) -> bytes:
        return await self._file_transactions.fd_read(fd, size, offset)

    # High-level file operations

    async def file_write(self, path: FsPath, content: bytes, offset: int = 0) -> int:
        _, fd = await self.file_open(path, "rw")
        try:
            if offset:
                await self.fd_seek(fd, offset)
            return await self.fd_write(fd, content)
        finally:
            await self.fd_close(fd)

    async def file_resize(self, path: FsPath, length: int) -> None:
        _, fd = await self.file_open(path, "w")
        try:
            await self.fd_resize(fd, length)
        finally:
            await self.fd_close(fd)

    async def file_read(self, path: FsPath, size: int = math.inf, offset: int = 0) -> bytes:
        _, fd = await self.file_open(path, "r")
        try:
            if offset:
                await self.fd_seek(fd, offset)
            return await self.fd_read(fd, size)
        finally:
            await self.fd_close(fd)

    # Left to migrate

    def _cook_path(self, relative_path=""):
        return FsPath(f"/{self.workspace_name}/{relative_path}")

    async def _load_and_retry(self, fn, *args, **kwargs):
        while True:
            try:
                if inspect.iscoroutinefunction(fn):
                    return await fn(*args, **kwargs)
                else:
                    return fn(*args, **kwargs)

            except FSManifestLocalMiss as exc:
                await self._remote_loader.load_manifest(exc.access)

            except FSMultiManifestLocalMiss as exc:
                for access in exc.accesses:
                    await self._remote_loader.load_manifest(access)

    async def sync(self, path: FsPath, recursive: bool = True) -> None:
        path = self._cook_path(path)
        await self._load_and_retry(self._syncer.sync, path, recursive=recursive)

    # TODO: do we really need this ? or should we provide id manipulation at this level ?
    async def sync_by_id(self, entry_id: AccessID) -> None:
        assert isinstance(entry_id, AccessID)
        await self._load_and_retry(self._syncer.sync_by_id, entry_id)

    async def get_entry_path(self, id: AccessID) -> FsPath:
        assert isinstance(id, AccessID)
        path, _, _ = await self._load_and_retry(self._local_folder_fs.get_entry_path, id)
        return path
