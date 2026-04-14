# coding=utf-8
import requests
from bs4 import BeautifulSoup
from funboost import boost, BrokerEnum, ConcurrentModeEnum, BoosterParams

# Define the crawler task function
@boost(BoosterParams(queue_name='test_queue70ac', do_task_filtering=True, qps=5, log_level=10, broker_exclusive_config={'a': 1}))
def crawl(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Parse the data; this is just an example, modify as needed for your use case
    title = soup.title.string
    return title

# Run the crawler
if __name__ == '__main__':
    # Assume you have a list of URLs
    urls = ['https://www.example.com', 'https://www.example.org', 'https://www.example.net']
    for url in urls:
        crawl.push(url)  # Add task to the queue
    crawl.consume()  # Start the crawler task
