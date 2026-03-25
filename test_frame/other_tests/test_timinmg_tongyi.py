# difference_calculator.py
from funboost import boost, BrokerEnum

# Define a consumer function to calculate the difference between two numbers
@boost('difference_queue', broker_kind=BrokerEnum.REDIS)
def calculate_difference(a, b):
    result = a - b
    print(f'The difference between {a} and {b} is {result}')
    return result

# Define a producer function to push tasks
def push_difference_tasks():
    tasks = [(10, 5), (20, 3), (15, 7)]
    for a, b in tasks:
        calculate_difference.push(a=a, b=b)

if __name__ == '__main__':
    # Start consumer
    calculate_difference.consume()
    # Push tasks
    push_difference_tasks()