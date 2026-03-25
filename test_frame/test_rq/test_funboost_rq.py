import time

from funboost import boost, BrokerEnum,set_interrupt_signal_handler

from funboost.assist.rq_helper import RqHelper


@boost('test_rq_queue1a', broker_kind=BrokerEnum.RQ)
def f(x, y):
    time.sleep(2)
    print(f'x:{x},y:{y}')


@boost('test_rq_queue2a', broker_kind=BrokerEnum.RQ)
def f2(a, b):
    time.sleep(3)
    print(f'a:{a},b:{b}')


if __name__ == '__main__':
    RqHelper.add_nb_log_handler_to_rq()  # Use nb_log handler to replace rq's default handler
    for i in range(100):
        f.push(i, i * 2)
        f2.push(i, i * 10)
    f.consume()  # f.consume() registers the queue name for the rq f function to start
    f2.consume()  # f2.consume() registers the queue name for the rq f2 function
    RqHelper.realy_start_rq_worker()  # realy_start_rq_worker actually starts the rq worker, equivalent to running 'rqworker' on the command line


