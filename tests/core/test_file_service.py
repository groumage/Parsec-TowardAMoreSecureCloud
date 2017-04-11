from freezegun import freeze_time
import pytest

from parsec.backend import MockedVlobService
from parsec.core import (CryptoService, FileService, IdentityService, PubKeysService,
                         UserManifestService)
from parsec.server import BaseServer, WebSocketServer


class BaseTestFileService:

    @pytest.mark.asyncio
    async def test_create_file(self):
        ret = await self.service.dispatch_msg({'cmd': 'create_file'})
        assert ret['status'] == 'ok'
        # assert ret['file']['id'] # TODO check id

    @pytest.mark.xfail
    @pytest.mark.asyncio
    async def test_read_file(self):
        ret = await self.service.dispatch_msg({'cmd': 'create_file'})
        id = ret['file']['id']
        read_trust_seed = ret['file']['read_trust_seed']
        write_trust_seed = ret['file']['write_trust_seed']
        # Empty file
        ret = await self.service.dispatch_msg({'cmd':
                                               'read_file',
                                               'id': id,
                                               'trust_seed': read_trust_seed})
        assert ret == {'status': 'ok', 'content': '', 'version': 1}
        # Not empty file
        ret = await self.service.dispatch_msg({'cmd': 'write_file',
                                               'id': id,
                                               'trust_seed': write_trust_seed,
                                               'version': 2,
                                               'content': 'foo'})
        ret = await self.service.dispatch_msg({'cmd': 'read_file',
                                               'id': id,
                                               'trust_seed': read_trust_seed})
        assert ret == {'status': 'ok', 'content': 'foo', 'version': 2}
        # Unknown file
        ret = await self.service.dispatch_msg({'cmd': 'read_file',
                                               'id': '5ea26ae2479c49f58ede248cdca1a3ca',
                                               'trust_seed': read_trust_seed})
        assert ret == {'status': 'not_found', 'label': 'File not found.'}

    @pytest.mark.xfail
    @pytest.mark.asyncio
    async def test_write_file(self):
        ret = await self.service.dispatch_msg({'cmd': 'create_file'})
        id = ret['file']['id']
        read_trust_seed = ret['file']['read_trust_seed']
        write_trust_seed = ret['file']['write_trust_seed']
        # Check with empty and not empty file
        content = ['foo', 'bar']
        for value in content:
            ret = await self.service.dispatch_msg({'cmd': 'write_file',
                                                   'id': id,
                                                   'trust_seed': write_trust_seed,
                                                   'version': content.index(value) + 2,
                                                   'content': value})
            assert ret == {'status': 'ok'}
            ret = await self.service.dispatch_msg({'cmd': 'read_file',
                                                   'id': id,
                                                   'trust_seed': read_trust_seed})
            assert ret == {'status': 'ok', 'content': value, 'version': content.index(value) + 2}
        # Unknown file
        ret = await self.service.dispatch_msg({'cmd': 'write_file',
                                               'id': '1234',
                                               'trust_seed': write_trust_seed,
                                               'version': 1,
                                               'content': 'foo'})
        assert ret == {'status': 'not_found', 'label': 'File not found.'}

    @pytest.mark.xfail
    @pytest.mark.asyncio
    # @freeze_time("2012-01-01")
    async def test_stat_file(self):
            # Good file
            with freeze_time('2012-01-01') as frozen_datetime:
                ret = await self.service.dispatch_msg({'cmd': 'create_file'})
                id = ret['file']['id']
                read_trust_seed = ret['file']['read_trust_seed']
                write_trust_seed = ret['file']['write_trust_seed']
                ret = await self.service.dispatch_msg({'cmd': 'stat_file', 'id': id})
                ctime = frozen_datetime().timestamp()
                assert ret == {'status': 'ok', 'stats': {'id': id,
                                                         'ctime': ctime,
                                                         'mtime': ctime,
                                                         'atime': ctime,
                                                         'size': 0}}
                frozen_datetime.tick()
                mtime = frozen_datetime().timestamp()
                ret = await self.service.dispatch_msg({'cmd': 'write_file',
                                                       'id': id,
                                                       'trust_seed': write_trust_seed,
                                                       'version': 2,
                                                       'content': 'foo'})
                ret = await self.service.dispatch_msg({'cmd': 'stat_file', 'id': id})
                assert ret == {'status': 'ok', 'stats': {'id': id,
                                                         'ctime': ctime,
                                                         'mtime': mtime,
                                                         'atime': ctime,
                                                         'size': 3}}

                frozen_datetime.tick()
                atime = frozen_datetime().timestamp()
                ret = await self.service.dispatch_msg({'cmd': 'read_file',
                                                       'id': id,
                                                       'trust_seed': read_trust_seed})
                ret = await self.service.dispatch_msg({'cmd': 'stat_file', 'id': id})
                assert ret == {'status': 'ok', 'stats': {'id': id,
                                                         'ctime': ctime,
                                                         'mtime': mtime,
                                                         'atime': atime,
                                                         'size': 3}}
            # Unknown file
            ret = await self.service.dispatch_msg({'cmd': 'write_file',
                                                   'id': '1234',
                                                   'trust_seed': write_trust_seed,
                                                   'version': 1,
                                                   'content': 'foo'})
            assert ret == {'status': 'not_found', 'label': 'File not found.'}

    @pytest.mark.xfail
    @pytest.mark.asyncio
    async def test_history(self):
        raise NotImplementedError()


class TestFileService(BaseTestFileService):

    def setup_method(self):
        backend_server = WebSocketServer()
        backend_server.register_service(MockedVlobService())
        backend_server.bootstrap_services()
        backend_server.start('localhost', 6777)  # TODO
        self.service = FileService('localhost', 6777)
        server = BaseServer()
        server.register_service(self.service)
        server.register_service(CryptoService())
        server.register_service(IdentityService('localhost', 6777))
        server.register_service(PubKeysService())
        server.register_service(UserManifestService('localhost', 6777))
        server.bootstrap_services()
