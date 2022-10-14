import socket
from datetime import datetime, timedelta

import amqp

from rpc_helper.rpc_helper import RpcHelper, RpcResponse


class RpcAmqpHelper(RpcHelper):
    def _callback(self, message: amqp.Message):
        if message.properties.get('correlation_id') == self.correlation_id:
            # Можно поставить connection.auto_decode = True и message.body будет уже str
            content_encoding = message.properties.get('content_encoding', self.content_encoding)
            self.result = RpcResponse(
                raw_data=message.body.decode(content_encoding),
                headers=message.headers,
                content_type=message.properties.get('content_type', 'application/plaintext')
            )

    def rpc_request(
            self,
            exchange: str,
            routing_key: str,
            headers: dict,
            body: str,
    ) -> RpcResponse:
        rpc_channel = self.connection.channel()
        rpc_channel.auto_decode = False
        result = rpc_channel.queue_declare(queue='', exclusive=True)
        callback_queue = result.queue
        self.reset()

        rpc_channel.basic_publish(
            msg=amqp.Message(
                body,
                reply_to=callback_queue,
                content_encoding=self.content_encoding,
                application_headers=headers,
                correlation_id=self.correlation_id,
                content_type=self.content_type,
                expiration=str(int(self._ttl.total_seconds() * 1000)),
            ),
            exchange=exchange,
            routing_key=routing_key,
        )

        rpc_channel.basic_consume(
            queue=callback_queue,
            exclusive=True,
            callback=self._callback,
            no_ack=True,
        )

        while not self.has_result:
            is_timed_out = self.started_at + self._ttl < datetime.now()
            if is_timed_out:
                break

            try:
                self.connection.drain_events(timeout=1)
            except socket.timeout:
                pass

            self.connection.heartbeat_tick()

        return self.result


if __name__ == '__main__':
    connection = amqp.Connection(host='localhost:5672', userid='guest', password='guest')
    connection.connect()
    # Код выше можно заменить на
    #     with Connection(...) as connection:
    # и убрать connection.close()

    helper = RpcAmqpHelper(connection=connection, ttl=timedelta(seconds=10), content_type='application/plaintext')
    response = helper.rpc_request(
        exchange='teleport',
        headers={},
        routing_key='noop',
        body='Hello world!',
    )
    connection.close()

    print('Rpc response:', response)
    print('Rpc content_type:', response.content_type)

    # json example
    print('-----')

    with amqp.Connection(host='localhost:5672', userid='guest', password='guest') as connection:
        helper = RpcAmqpHelper(connection=connection, ttl=timedelta(seconds=10), content_type='application/json')
        response = helper.rpc_request(
            exchange='teleport',
            headers={},
            routing_key='noop',
            body='Hello world!',
        )

    print('JSON Rpc response:', response)
    print('Rpc content_type:', response.content_type)
    if response.ok and response.content_type == 'application/json':
        print('as json:', response.json)
