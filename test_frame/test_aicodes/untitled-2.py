# coding=utf-8
import requests
from bs4 import BeautifulSoup
from funboost import boost, BrokerEnum, ConcurrentModeEnum, BoosterParams

# Define level-1 page crawler task function
@boost(BoosterParams(queue_name='level1_queue', do_task_filtering=True, qps=5, log_level=10, broker_exclusive_config={'a': 1}))
def crawl_level1(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Extract level-2 page links
    level2_links = [a['href'] for a in soup.find_all('a', href=True)]
    return level2_links

# Define level-2 page crawler task function
@boost(BoosterParams(queue_name='level2_queue', do_task_filtering=True, qps=5, log_level=10, broker_exclusive_config={'a': 1}))
def crawl_level2(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Parse data; this is just an example, you can modify it according to actual needs
    title = soup.title.string
    return title

# Run the spider
if __name__ == '__main__':
    # Assume you have a level-1 page URL
    level1_url = 'https://www.example.com'
    crawl_level1.push(level1_url)  # Add task to queue
    crawl_level1.consume()  # Start level-1 page crawler task
    # Handle level-2 page links returned from level-1 pages
    for level2_url in crawl_level1.get_result():
        crawl_level2.push(level2_url)  # Add task to queue
    crawl_level2.consume()  # Start level-2 page crawler task
