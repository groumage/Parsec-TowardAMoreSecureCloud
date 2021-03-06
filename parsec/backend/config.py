# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPLv3 2019 Scille SAS

import attr
from typing import List, Optional, Union, Tuple

from parsec.core.types import BackendAddr


class BaseBlockStoreConfig:
    pass


@attr.s(frozen=True, auto_attribs=True)
class RAID0BlockStoreConfig(BaseBlockStoreConfig):
    type = "RAID0"

    blockstores: List[BaseBlockStoreConfig]


@attr.s(frozen=True, auto_attribs=True)
class RAID1BlockStoreConfig(BaseBlockStoreConfig):
    type = "RAID1"

    blockstores: List[BaseBlockStoreConfig]


@attr.s(frozen=True, auto_attribs=True)
class RAID5BlockStoreConfig(BaseBlockStoreConfig):
    type = "RAID5"

    blockstores: List[BaseBlockStoreConfig]


@attr.s(frozen=True, auto_attribs=True)
class S3BlockStoreConfig(BaseBlockStoreConfig):
    type = "S3"

    s3_endpoint_url: Optional[str]
    s3_region: str
    s3_bucket: str
    s3_key: str
    s3_secret: str


@attr.s(frozen=True, auto_attribs=True)
class SWIFTBlockStoreConfig(BaseBlockStoreConfig):
    type = "SWIFT"

    swift_authurl: str
    swift_tenant: str
    swift_container: str
    swift_user: str
    swift_password: str


@attr.s(frozen=True, auto_attribs=True)
class PostgreSQLBlockStoreConfig(BaseBlockStoreConfig):
    type = "POSTGRESQL"


@attr.s(frozen=True, auto_attribs=True)
class MockedBlockStoreConfig(BaseBlockStoreConfig):
    type = "MOCKED"


@attr.s(slots=True, frozen=True, auto_attribs=True)
class SmtpEmailConfig:
    host: str
    port: int
    host_user: Optional[str]
    host_password: Optional[str]
    use_ssl: bool
    use_tls: bool
    sender: str

    def __str__(self):
        return f"{self.__class__.__name__}(sender={self.sender}, host={self.host}, port={self.port}, use_ssl={self.use_ssl})"


@attr.s(slots=True, frozen=True, auto_attribs=True)
class MockedEmailConfig:
    sender: str
    tmpdir: str

    def __str__(self):
        return f"{self.__class__.__name__}(sender={self.sender}, tmpdir={self.tmpdir})"


EmailConfig = Union[SmtpEmailConfig, MockedEmailConfig]


@attr.s(slots=True, frozen=True, auto_attribs=True)
class BackendConfig:
    administration_token: str

    db_url: str
    db_min_connections: int
    db_max_connections: int

    blockstore_config: BaseBlockStoreConfig

    email_config: Union[SmtpEmailConfig, MockedEmailConfig]
    ssl_context: bool
    forward_proto_enforce_https: Optional[Tuple[bytes, bytes]]
    backend_addr: Optional[BackendAddr]

    spontaneous_organization_bootstrap: bool
    organization_bootstrap_webhook_url: Optional[str]

    debug: bool

    @property
    def db_type(self):
        if self.db_url.upper() == "MOCKED":
            return "MOCKED"
        elif self.db_url.upper() == "BLOCKCHAIN":
            return "BLOCKCHAIN"
        else:
            return "POSTGRESQL"
        return self._db_type
