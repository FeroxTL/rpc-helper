import json
import typing
import uuid
from datetime import timedelta, datetime


class RpcResult:
    ok = False
    content_type = None


class _NoResult(RpcResult):
    def __repr__(self):
        return '<No result>'
    __str__ = __repr__


no_result = _NoResult()


class RpcResponse(RpcResult):
    ok = True

    def __init__(self, raw_data: str, headers: dict, content_type: str):
        self.raw_data = raw_data
        self.headers = headers
        self.content_type = content_type

    @property
    def json(self) -> typing.Union[str, int, dict, list, None]:
        return json.loads(self.raw_data)

    def __str__(self):
        return self.raw_data

    def __repr__(self):
        return '<{self.__class__.__name__} raw_data: {self.raw_data} headers: {self.headers}>'.format(self=self)


class RpcHelper:
    """Класс для сохранения состояния отправки rpc-сообщения."""
    def __init__(
            self,
            ttl: timedelta,
            connection,
            content_encoding: str = 'utf-8',
            content_type: str = 'application/json',
    ):
        self._ttl = ttl
        self.connection = connection
        self.content_encoding = content_encoding
        self.content_type = content_type
        # Must be reset
        self._callback_result: typing.Optional[RpcResponse] = None
        self._started_at = None
        self.correlation_id = None

    @property
    def result(self) -> RpcResponse:
        return self._callback_result

    @result.setter
    def result(self, value: RpcResponse):
        self._callback_result = value

    @property
    def started_at(self):
        return self._started_at

    def reset(self):
        self._started_at = datetime.now()
        self.result = no_result
        self.correlation_id = str(uuid.uuid4())

    @property
    def has_result(self):
        return self.result is not no_result

    def rpc_request(
            self,
            exchange: str,
            routing_key: str,
            headers: dict,
            body: bytes,
    ) -> RpcResponse:
        raise NotImplementedError
