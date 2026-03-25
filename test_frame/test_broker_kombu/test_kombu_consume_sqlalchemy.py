import time
from funboost import BrokerEnum, boost
from funboost.funboost_config_deafult import BrokerConnConfig

'''
Automatically creates tables kombu_message and kombu_queue by default. Choose the correct sqlalchemy version — tested with 1.4.8 (works), 2.0.15 (errors).
All queue messages are stored in one table kombu_message; the queue_id field distinguishes which queue the message belongs to.
'''
@boost('test_kombu_sqlalchemy_queue2', broker_kind=BrokerEnum.KOMBU, qps=0.1,
       broker_exclusive_config={
           'kombu_url': f'sqla+mysql+pymysql://{BrokerConnConfig.MYSQL_USER}:{BrokerConnConfig.MYSQL_PASSWORD}'
                        f'@{BrokerConnConfig.MYSQL_HOST}:{BrokerConnConfig.MYSQL_PORT}/{BrokerConnConfig.MYSQL_DATABASE}',
           'transport_options': {},
           'prefetch_count': 500})
def f2(x, y):
    print(f'start {x} {y} ...')
    time.sleep(60)
    print(f'{x} + {y} = {x + y}')
    print(f'over {x} {y}')


@boost('test_kombu_sqlalchemy_queue3', broker_kind=BrokerEnum.KOMBU, qps=0.1,
       broker_exclusive_config={
           'kombu_url': f'sqla+mysql+pymysql://{BrokerConnConfig.MYSQL_USER}:{BrokerConnConfig.MYSQL_PASSWORD}'
                        f'@{BrokerConnConfig.MYSQL_HOST}:{BrokerConnConfig.MYSQL_PORT}/{BrokerConnConfig.MYSQL_DATABASE}',
           'transport_options': {},
           'prefetch_count': 500})
def f3(x, y):
    print(f'start {x} {y} ...')
    time.sleep(60)
    print(f'{x} + {y} = {x + y}')
    print(f'over {x} {y}')


if __name__ == '__main__':
    for i in range(100):
        f2.push(i, i + 1)
        f3.push(i,i*2)
    f2.consume()
    f3.consume()
