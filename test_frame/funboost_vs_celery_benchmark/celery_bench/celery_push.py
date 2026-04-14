


from celery_consume import print_number
import nb_log
import datetime

if __name__ == '__main__':
    print(f'Current time: {datetime.datetime.now()}')

    for i in range(100000):
        if i % 1000 == 0:
            print(f'Current time: {datetime.datetime.now()} {i}')
        print_number.delay(i)
    print(f'Current time: {datetime.datetime.now()}')


'''

Tested on win11 + python3.9 + celery 5 + redis middleware + amd r7 5800h cpu

Celery publish performance test results:

Celery publishes 100,000 simple messages in 110 seconds, averaging 900 messages per second.
As can be seen from the printed publish timestamps, it prints once every 1.1 seconds for 1000 messages published.
'''