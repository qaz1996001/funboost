from tests.ai_codes.test_extreme_load_balancing_consume import extreme_load_balancing_consumer

if __name__ == '__main__':
    print("Starting to publish messages...")
    for i in range(50):
        extreme_load_balancing_consumer.push(i)
    print("Messages published. Please start two or more consumer processes to observe the load balancing effect.")
