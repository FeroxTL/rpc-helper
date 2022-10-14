import json
import typing
from datetime import timedelta

import pika

from rpc_helper.rpc_helper_amqp import RpcAmqpHelper


class RpcAmqpServer(RpcAmqpHelper):
    def __init__(self, *args, **kwargs):
        super(RpcAmqpServer, self).__init__(*args, **kwargs)
        self._channel = None

    def stop_server(self):
        if self._channel is not None:
            self._channel.stop_consuming()

    def handle_message(self, message: str, content_type: typing.Optional[str]):
        if content_type == 'application/json':
            return json.dumps({'message': message}), 'application/json'
        return 'Hello from amqp server! Your request is "{}"'.format(message), 'application/plaintext'

    def _server_callback(self, channel, method, properties: pika.BasicProperties, body: bytes):
        reply_to = properties.reply_to

        message_str = body.decode(properties.content_encoding or self.content_encoding)
        print('Received', message_str)
        response_msg, content_type = self.handle_message(message=message_str, content_type=properties.content_type)

        if reply_to is not None and response_msg is not None:
            channel.basic_publish(
                body=response_msg.encode(self.content_encoding),
                properties=pika.BasicProperties(
                    reply_to=reply_to,
                    headers={},
                    content_encoding=self.content_encoding,
                    content_type=content_type,
                    correlation_id=properties.correlation_id,
                    expiration=str(int(self._ttl.total_seconds() * 1000)),
                ),
                exchange='',
                routing_key=reply_to,
            )

    def serve_forever(self, queue: str):
        channel = self.connection.channel()
        channel.basic_qos(prefetch_size=0, prefetch_count=1, global_qos=False)
        channel.basic_consume(
            queue=queue,
            auto_ack=True,
            on_message_callback=self._server_callback,
        )
        channel.start_consuming()


if __name__ == '__main__':
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.PlainCredentials(
                username='guest',
                password='guest',
            )
        )
    )
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

    connection.close()
