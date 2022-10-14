from datetime import datetime, timedelta

import pika

from rpc_helper.rpc_helper import RpcHelper, RpcResponse


class RpcPikaHelper(RpcHelper):
    def _callback(self, channel, method, properties: pika.BasicProperties, body: bytes):
        if properties.correlation_id == self.correlation_id:
            self.result = RpcResponse(
                raw_data=body.decode(properties.content_encoding or self.content_encoding),
                headers=properties.headers,
                content_type=properties.content_type,
            )

    def rpc_request(
            self,
            exchange: str,
            routing_key: str,
            headers: dict,
            body: str,
    ) -> RpcResponse:
        rpc_channel = self.connection.channel()
        result = rpc_channel.queue_declare(queue='', exclusive=True)
        self.reset()

        rpc_channel.basic_consume(
            queue=result.method.queue,
            on_message_callback=self._callback,
            auto_ack=True
        )
        rpc_channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            properties=pika.BasicProperties(
                reply_to=result.method.queue,
                headers=headers,
                content_encoding=self.content_encoding,
                content_type=self.content_type,
                # expiration=rpc_message.expiration,
                correlation_id=self.correlation_id,
            ),
            body=body,
        )

        while not self.has_result:
            is_timed_out = self.started_at + self._ttl < datetime.now()
            if is_timed_out:
                break
            rpc_channel.connection.process_data_events()

        return self.result


if __name__ == '__main__':
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.PlainCredentials(
                username='guest',
                password='guest',
            )
        ))
    helper = RpcPikaHelper(connection=connection, ttl=timedelta(seconds=10))
    response = helper.rpc_request(
        exchange='teleport',
        headers={},
        routing_key='noop',
        body='Hello from pika client!',
    )
    connection.close()

    print('Response is:', response)
    print('Rpc content_type:', response.content_type)
    print('as json:', response.json)

    # plaintext request
    print('-----')
    #

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.PlainCredentials(
                username='guest',
                password='guest',
            )
        ))
    helper = RpcPikaHelper(connection=connection, ttl=timedelta(seconds=10), content_type='application/plaintext')
    response = helper.rpc_request(
        exchange='teleport',
        headers={},
        routing_key='noop',
        body='Hello from pika client!',
    )
    connection.close()

    print('Response is:', response)
    print('Rpc content_type:', response.content_type)
