

from funboost_consume import print_number
import datetime

if __name__ == '__main__':
    for i in range(100000):
        if i % 1000 == 0:
            print(f'Current time: {datetime.datetime.now()} {i}')
        print_number.push(i)


'''
Tested on win11 + python3.9 + funboost + redis middleware + amd r7 5800h cpu

funboost publish performance test results:

funboost publishes 100,000 messages in 5 seconds, averaging 20,000 messages per second.
As can be seen from the printed publish timestamps, it prints once every 0.05 seconds for 1000 messages published.
'''
