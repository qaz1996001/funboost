---
noteId: "f63aee30d7be11efb3956b6f0fb3ea8d"
tags: []

---

# Funboost vs Scrapy

## Introduction
In web scraping development, Scrapy is a commonly used framework. This article compares the pros and cons of Funboost and Scrapy through a web scraping example.

## Example Code
### Funboost Example
The following is a web scraping code example using the Funboost framework for downloading celebrity images:

```python
from funboost import boost, BoosterParams
import requests
from parsel import Selector

@boost(BoosterParams(queue_name='xiaoxianrou_list_page', qps=0.2))
def crawl_list_page(page_index):
    """Crawl the list page"""
    url = f'http://www.5442tu.com/mingxing/list_2_{page_index}.html'
    resp = requests.get(url)
    sel = Selector(resp.content.decode('gbk'))
    detail_sels = sel.xpath('//div[@class="imgList2"]/ul/li/a')
    for detail_sel in detail_sels:
        detail_url = detail_sel.xpath('./@href').extract_first()
        title = detail_sel.xpath('./@title').extract_first()
        crawl_detail_page.push(detail_url, title)

    # Pagination logic
    next_page = sel.xpath('//a[text()="Next Page"]/@href').extract_first()
    if next_page:
        next_page_index = page_index + 1
        crawl_list_page.push(next_page_index)

@boost(BoosterParams(queue_name='xiaoxianrou_detail_page', qps=0.2))
def crawl_detail_page(detail_url, title):
    """Crawl the detail page"""
    resp = requests.get(detail_url)
    sel = Selector(resp.content.decode('gbk'))
    img_url = sel.xpath('//div[@class="imgContent"]//img/@src').extract_first()
    print(f'Image found: {title} - {img_url}')

if __name__ == '__main__':
    crawl_list_page.push(1)  # Start crawling from page 1
    crawl_list_page.consume()
    crawl_detail_page.consume()
```

### Scrapy Example
The following is a web scraping code example using the Scrapy framework:

```python
import scrapy
from scrapy_redis.spiders import RedisSpider

class XiaoxianrouSpider(RedisSpider):
    name = 'xiaoxianrou'
    allowed_domains = ['5442tu.com']
    start_urls = ["http://www.5442tu.com/mingxing/list_2_1.html"]

    def parse(self, response):
        """Parse the list page"""
        detail_sels = response.xpath('//div[@class="imgList2"]/ul/li/a')
        for detail_sel in detail_sels:
            yield scrapy.Request(
                url=detail_sel.xpath('./@href').extract_first(),
                callback=self.parse_detail,
                meta={'title': detail_sel.xpath('./@title').extract_first()}
            )

        # Pagination logic
        next_page = response.xpath('//a[text()="Next Page"]/@href').extract_first()
        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse)

    def parse_detail(self, response):
        """Parse the detail page"""
        title = response.meta['title']
        img_url = response.xpath('//div[@class="imgContent"]//img/@src').extract_first()
        yield {
            'title': title,
            'img_url': img_url
        }
```

## Framework Comparison Analysis

### 1. Code Structure
- **Funboost**:
  - Simple structure, high flexibility; users can freely write request logic and use any request library.
  - Distributed functionality is achieved simply with a decorator, without creating a complex project structure.

- **Scrapy**:
  - Requires creating a complete project structure; users must frequently switch between multiple files while writing code.
  - Must follow framework conventions when writing code.
  - Many files are involved, including settings.py, items.py, pipelines.py, etc.

A fixed directory structure for a Scrapy project looks like this:
  my_scrapy_project/
├── scrapy.cfg                # Project configuration file
├── my_scrapy_project/        # Project main directory
│   ├── __init__.py           # Project initialization file
│   ├── items.py              # Defines the data structure to be scraped
│   ├── middlewares.py        # Middleware configuration
│   ├── pipelines.py          # Data processing pipeline
│   ├── settings.py           # Project settings file
│   ├── spiders/              # Spider directory
│   │   ├── __init__.py       # Spider initialization file
│   │   └── example_spider.py # Example spider file
│   └── utils/                # Utilities directory (optional)
│       └── __init__.py       # Utilities initialization file
└── requirements.txt          # Project dependencies (optional)

### 2. Learning Curve
- **Funboost**:
  - Gentle learning curve; users only need to master the use of decorators and can get started quickly.

- **Scrapy**:
  - Steep learning curve; requires understanding the various components of the framework, increasing the learning difficulty.

### 3. Features
- **Funboost**:
  - Provides a wide range of control features, supports high concurrency and flexible task scheduling, suitable for large-scale crawling projects.
  - Allows users to write crawler code inside functions and supports multiple message queues.

- **Scrapy**:
  - Relatively limited features; it is difficult to implement complex scheduling logic and extensibility is poor.
  - Users must be very proficient in the Scrapy framework itself to freely customize requests and implement unconventional ideas.

### 4. Code Migration
- **Funboost**:
  - Minimal intrusion into existing code
  - Only requires adding a decorator
  - Preserves the original code logic unchanged

- **Scrapy**:
  - In high-concurrency scenarios, Scrapy's performance falls short of Funboost's.

## Conclusion
**Funboost is far superior to Scrapy for web scraping in every dimension — flexibility, learning curve, features, and performance. Funboost provides a better developer experience. Choosing Funboost allows developers to complete crawler projects faster and more efficiently, truly achieving high-performance and convenient scraping.**

In addition, there is a large number of Scrapy-API-imitation crawler frameworks in China, such as Feapder. These frameworks suffer from the same issues as Scrapy and are far behind Funboost in terms of ease of use and performance.
