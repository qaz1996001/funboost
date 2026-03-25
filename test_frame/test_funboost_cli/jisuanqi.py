

import fire
import re

class Calculator:
    def __init__(self):
        self.value = 0

    def evaluate(self, expression):
        expression = expression.replace(' ', '')  # Remove spaces
        expression = re.sub(r'(\d+)', r'self.add(\1)', expression)  # Replace numbers with self.add(num)
        expression = expression.replace('+', '.add')  # Replace + with .add
        expression = expression.replace('-', '.subtract')  # Replace - with .subtract
        expression = expression.replace('*', '.multiply')  # Replace * with .multiply
        expression = expression.replace('/', '.divide')  # Replace / with .divide
        eval(expression)  # Execute expression

    def add(self, num):
        self.value += num

    def subtract(self, num):
        self.value -= num

    def multiply(self, num):
        self.value *= num

    def divide(self, num):
        self.value /= num

    def __str__(self):
        return str(self.value)

def main():
    fire.Fire(Calculator)

if __name__ == "__main__":
    main()