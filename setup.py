# coding=utf-8
from setuptools import setup, find_packages
from funboost import __version__

# from logging_tree import printout
# printout()

extra_brokers = ['confluent_kafka==1.7.0',
                 "pulsar-client==3.1.0; python_version>='3.7'",
                 'celery',
                 'flower',
                 'nameko==2.14.1',
                 'sqlalchemy==1.4.13',
                 'sqlalchemy_utils==0.36.1',
                 'dramatiq==1.14.2',
                 'huey==2.4.5',
                 'rq==1.15.0',
                 'kombu',
                
                 'elasticsearch',
                 'gnsq==1.0.1',
                 'psutil',
                 'peewee==3.17.3',
                 'nats-python',
                 'aiohttp==3.8.3',
                 'paho-mqtt',
                 'rocketmq',
                 'zmq',
                 'pyzmq',
                 'kafka-python==2.0.2',
                  'eventlet==0.33.3',
                 'gevent==22.10.2',

                  'mysql-replication==1.0.9',

                    'grpcio==1.60.0',
                    'grpcio-tools==1.60.0',
                    'protobuf==4.25.1',

                    'waitress',
                 ]

extra_flask = ['flask', 'flask_bootstrap', 'flask_wtf', 'wtforms', 'flask_login','psutil']
setup(
    name='funboost',  #
    version=__version__,
    description=(
        'pip install funboost, a full-featured Python distributed function scheduling framework. funboost is comprehensive and heavyweight in features — 99% of what users can think of is already there; yet its usage is lightweight — only one line of code (@boost) is needed. Supports all Python concurrency modes and every major message-queue middleware. Frameworks such as celery and dramatiq can be used wholesale as funboost middleware. It is a Python function accelerator that covers everything; all the control features users can imagine are included. It unifies the programming mindset, is compatible with 50% of Python business scenarios, and has a wide range of applicability. Only one line of code is needed to execute any Python function in a distributed manner. The funboost web manager makes it easy to view and manage consumer functions. 99% of Python developers who have used funboost describe it as: simple, convenient, powerful, and wish they had found it sooner.'
    ),
    # long_description=open('README.md', 'r',encoding='utf8').read(),
    keywords=["funboost", "distributed-framework", "function-scheduling", "rabbitmq", "rocketmq", "kafka", "nsq", "redis", "disk",
              "sqlachemy", "consume-confirm", "timing", "task-scheduling", "apscheduler", "pulsar", "mqtt", "kombu", "de", "celery", "framework", 'distributed-scheduling'],
    long_description_content_type="text/markdown",
    long_description=open('README.md', 'r', encoding='utf8').read(),
    author='bfzs',
    author_email='ydf0509@sohu.com',
    maintainer='ydf',
    maintainer_email='ydf0509@sohu.com',
    # license='BSD License',
    license='BSD-3-Clause',
    # packages=['douban'], #
    packages=find_packages() + ['funboost.beggar_version_implementation', 'funboost.assist'],  # can also be specified in MANIFEST.in
    # packages=['function_scheduling_distributed_framework'], # this way nested sub-package folders are not included in the build.
    include_package_data=True,
    platforms=["all"],
    url='https://github.com/ydf0509/funboost',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        # 'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        # 'Programming Language :: Python :: 3.15',
        # 'Programming Language :: Python :: 3.16',
        # 'Programming Language :: Python :: 3.17',
        # 'Programming Language :: Python :: 3.18',
        # 'Programming Language :: Python :: 3.19',
        # 'Programming Language :: Python :: 3.20',
        # 'Programming Language :: Python :: 3.21',
        "Programming Language :: Python :: 3 :: Only",
        'Topic :: Software Development :: Libraries'
    ],
    install_requires=[
        'nb_log>=13.9',
        'nb_libs>=1.9',
        'nb_time>=2.7',
        "pymongo>=4.6.3",  # 3.5.1  -> 4.0.2
        'AMQPStorm==2.10.6',
        # 'rabbitpy==2.0.1',
        'decorator==5.1.1',
        'tomorrow3==1.1.0',
        'persist-queue>=0.4.2',
        'apscheduler>=3.10.1,<4.0.0',
        'pikav0',
        'pikav1',
        'redis2',
        'redis3',
        'redis5',
        'redis',
        'setuptools_rust',
        'fabric2>=2.6.0',  # some machines have a Rust build error; fix it with: curl https://sh.rustup.rs -sSf | sh
        'nb_filelock',
        'pysnooper',
        'deprecated',
        'cryptography',
        'auto_run_on_remote',
        'frozenlist',
        'fire',
        'pydantic',
        'orjson',
        'croniter',
        'cron-descriptor',
        "async-timeout",
        "async-timeout",
        "typing-extensions",
        
    ],
    extras_require={'all': extra_brokers + extra_flask,
                    'extra_brokers': extra_brokers,
                    'flask': extra_flask,
                    },

    entry_points={
        'console_scripts': [
            'funboost = funboost.__main__:main',
            'funboost_cli_super = funboost.__main__:main',
        ]}
)

"""
Official   https://pypi.org/simple
Tsinghua   https://pypi.tuna.tsinghua.edu.cn/simple
Douban     https://pypi.douban.com/simple/
Aliyun     https://mirrors.aliyun.com/pypi/simple/
Tencent    http://mirrors.tencentyun.com/pypi/simple/

Build and upload
python setup.py sdist upload -r pypi

# python setup.py bdist_wheel
python setup.py bdist_wheel ; python -m twine upload dist/funboost-23.5-py3-none-any.whl
python setup.py bdist_wheel && python -m twine upload dist/funboost-24.8-py3-none-any.whl
python setup.py sdist & twine upload dist/funboost-10.9.tar.gz

Fastest download method — installable immediately after upload. Aliyun mirror sync with the official PyPI can take a long time.
./pip install funboost==3.5 -i https://pypi.org/simple
Install the latest version
./pip install funboost --upgrade -i https://pypi.org/simple

pip install funboost[all]     # install all optional, less common middleware packages.


Install from git
pip install git+https://github.com/ydf0509/funboost.git
pip install git+https://gitee.com/bfzshen/funboost.git

"""
