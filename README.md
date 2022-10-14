Class-helper for rabbitmq rpc requests and responses. Works with two libraries: pika and amqp
(install your favourite from `requirements.txt`)

* `rpc-helper.py` -- base class `RpcHelper`, do not use directly
* `rpc_helper_amqp.py` -- client for amqp, use it
* `rpc_helper_pika.py` -- client for pika, use it
* `rpc_helper_amqp_server.py` -- amqp example
* `rpc_helper_pika_server.py` -- pika example

Installation:

1. Set up rabbit. Default hostname is `localhost`
2. Install python and requirements:
```shell
python3 -m venv ./env
source env/bin/activate
pip install -r rpc_helper/requirements.txt
```

Running:

Severs and clients are identical by functionality, run whatever you
like. Example with amqp:

```shell
python -m server_helper.rpc_helper_amqp_server
```

Clients are also identical by functionality. Use any you like. amqp example:

```shell
python -m rpc_helper.rpc_helper_amqp
```

You should see response from your server. Server should display request.

This also could be build as a package. `make sdist` should do the thing.
