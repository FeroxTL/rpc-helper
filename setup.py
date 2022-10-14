from setuptools import setup

setup(
    name='rpc_helper',
    version='1.0.2',
    python_requires='~=3.5',
    install_requires=[],
    packages=[
        'rpc_helper',
        # 'rpc_helper.rpc_helper_amqp',
        # 'rpc_helper.rpc_helper_pika',
    ],
    package_dir={
        'rpc_helper': 'rpc_helper',
    },
    license='MIT',
    description='RPC helper classes'
)
