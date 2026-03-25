import requests
from parsel import Selector
from funboost import boost, BrokerEnum, IdeAutoCompleteHelper

"""
Demonstrates using the distributed function scheduling framework to drive crawler functions.
Using this framework, crawler tasks can achieve: automatic scheduling, distributed execution, guaranteed consumption,
ultra-high-speed automatic concurrency, precise frequency control, seed filtering (implemented via function parameter filtering),
automatic retry, and scheduled crawling. This implements all the functionality a crawler framework should have.

This framework automatically schedules a function, not a URL request. Traditional frameworks use yield Request(),
which is incompatible with user-written requests/urllib code. If users need custom request handling, they must write
middleware hooks, and complex highly-customized requests can't even be implemented in those frameworks — extremely inflexible.

Since this framework schedules functions, users write request/parse/store logic inside the function however they want —
extremely flexible. Users can directly reuse existing functions. For example, if you previously wrote bare requests crawlers
without using a framework, just add the @task_deco decorator and it gets automatically scheduled.

90% of common crawlers conflict seriously with user-written request parsing/storage in terms of logic flow.
Adapting to use those frameworks requires major rewrites. This framework compared to the 90% of domestic scrapy-clone
crawler frameworks is completely different philosophically — it opens your mind. Traditional frameworks require inheriting
a Spider base class, overriding def parse, and yielding Request(url, callback=another_parse) inside parse.
Request logic is tightly constrained by the Request class with no room for easy customization. You usually need to write
middleware to intercept HTTP requests, which is also tightly constrained by the framework and hard to learn.
A distributed function scheduling framework naturally avoids these problems since it schedules functions, not URL requests.

Other crawler frameworks require inheriting BaseSpider, overriding many methods, writing many middleware methods
and config files, switching back and forth between many folders.
With this crawler, you only need to learn the @boost decorator. Code lines are greatly reduced, tasks are fail-safe
on restart, and worries are greatly reduced.

This crawler example is representative because it demonstrates distributed automatic scheduling from list pages to detail pages.

"""

"""
Beyond the most important feature of extremely flexible custom request/parse/store logic, other advantages over typical crawler frameworks:
2. This crawler framework supports redis_ack_able and rabbitmq modes. During large-scale concurrent crawling, it supports
   arbitrary code restarts with seed tasks guaranteed. With ordinary redis.blpop, tasks taken out during consumption are
   lost instantly if code is restarted — that's a pseudo-resumable pattern.
3. This framework supports both constant concurrency count and constant qps crawling. For example, crawling 7 pages/second
   is commonly thought to mean 7 threads, which is wrong. Server response times are not always exactly 1 second.
   Only a framework that runs at constant qps can guarantee 7 pages/second. Constant concurrency count frameworks fall short.
4. Supports task filtering with expiry cache. Ordinary crawler frameworks only support permanent filtering. For example,
   a page updated weekly cannot have its tasks permanently filtered.
Since this framework has 20+ control features, everything ordinary crawler frameworks can control is already built in.
"""


@boost('car_home_list', broker_kind=BrokerEnum.RedisBrpopLpush, max_retry_times=5, qps=2)
def crawl_list_page(news_type, page, do_page_turning=False):
    url = f'https://www.autohome.com.cn/{news_type}/{page}/#liststart'
    resp_text = requests.get(url).text  # To change IP or request headers, just write a function that auto-rotates IPs and headers — no need to write request middleware classes like some frameworks require.
    sel = Selector(resp_text)
    for li in sel.css('ul.article > li'):
        if len(li.extract()) > 100:  # Skip elements like this: <li id="ad_tw_04" style="display: none;">
            url_detail = 'https:' + li.xpath('./a/@href').extract_first()
            title = li.xpath('./a/h3/text()').extract_first()
            crawl_detail_page.push(url_detail, title=title, news_type=news_type)  # Publish detail page task
    if do_page_turning:
        last_page = int(sel.css('#channelPage > a:nth-child(12)::text').extract_first())
        for p in range(2, last_page + 1):
            crawl_list_page.push(news_type, p)  # Paginate list pages.


@boost('car_home_detail', broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=3,
       do_task_filtering=True, is_using_distributed_frequency_control=True)
def crawl_detail_page(url, title, news_type):
    resp_text = requests.get(url).text # To change IP or request headers, just write a function that auto-rotates IPs and headers — no need to write request middleware classes like some frameworks require.
    sel = Selector(resp_text)
    author = sel.css('#articlewrap > div.article-info > div > a::text').extract_first() or \
             sel.css('#articlewrap > div.article-info > div::text').extract_first() or ''
    author = author.replace("\n", "").strip()
    print(f'Saving data  {news_type}   {title} {author} {url} to database')  # Users can freely implement their own saving logic.


if __name__ == '__main__':
    # crawl_list_page('news',1)
    crawl_list_page.consume()  # Start list page consumer
    crawl_detail_page.consume()
    # This way is even faster, stacking multiple processes
    # crawl_detail_page.multi_process_consume(4)



