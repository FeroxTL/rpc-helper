import json
import socket
import typing
from datetime import timedelta
from functools import partial
from threading import Event

import amqp

from rpc_helper.rpc_helper_amqp import RpcAmqpHelper


class RpcAmqpServer(RpcAmqpHelper):
    def __init__(self, *args, **kwargs):
        super(RpcAmqpServer, self).__init__(*args, **kwargs)
        self.stop_event = Event()

    def stop_server(self):
        self.stop_event.set()

    def handle_message(self, message: str, content_type: typing.Optional[str]):
        message = 'Hello from amqp server! Your request is "{}"'.format(message)
        if content_type == 'application/json':
            return json.dumps({'message': message}), 'application/json'
        return message, 'application/plaintext'

    def _server_callback(self, message: amqp.Message, channel: amqp.Channel):
        reply_to = message.properties.get('reply_to')

        message.body = message.body.decode(message.properties.get('content_encoding', self.content_encoding))
        print('Received', message.body, message.properties)

        response, content_type = self.handle_message(
            message=message.body,
            content_type=message.properties.get('content_type')
        )

        if reply_to is not None and response is not None:
            channel.basic_publish(
                msg=amqp.Message(
                    response.encode(self.content_encoding),
                    reply_to=reply_to,
                    content_encoding=self.content_encoding,
                    content_type=content_type,
                    application_headers={},
                    correlation_id=message.properties.get('correlation_id'),
                    expiration=str(int(self._ttl.total_seconds() * 1000)),
                ),
                exchange='',
                routing_key=reply_to,
            )

    def serve_forever(self, queue: str):
        channel = self.connection.channel()
        channel.auto_decode = False
        channel.basic_qos(prefetch_size=0, prefetch_count=1, a_global=False)
        channel.basic_consume(
            queue=queue,
            no_ack=True,  # equals auto_ack in pika
            callback=partial(self._server_callback, channel=channel),
        )
        while not self.stop_event.is_set():
            try:
                self.connection.drain_events(timeout=2)
            except socket.timeout:
                pass
            self.connection.heartbeat_tick()


if __name__ == '__main__':
    with amqp.Connection(host='localhost:5672', userid='guest', password='guest') as connection:
        with connection.channel() as queue_channel:
            queue_channel.queue_declare(queue='noop', durable=True, auto_delete=False)
            queue_channel.queue_bind(queue='noop', exchange='teleport', routing_key='noop')

        helper = RpcAmqpServer(connection=connection, ttl=timedelta(seconds=10))
        try:
            helper.serve_forever(
                queue='noop',
            )
        except KeyboardInterrupt:
            helper.stop_server()
