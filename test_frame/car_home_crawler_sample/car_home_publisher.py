from funboost import fsdf_background_scheduler
from test_frame.car_home_crawler_sample.car_home_consumer import crawl_list_page, crawl_detail_page

crawl_list_page.clear()  # Clear list page queue
crawl_detail_page.clear()  # Clear detail page queue

# # Push list page homepage, and set pagination to True
crawl_list_page.push('news', 1, do_page_turning=True)  # News
crawl_list_page.push('advice', page=1, do_page_turning=True)  # Buying advice
crawl_list_page.push(news_type='drive', page=1, do_page_turning=True)  # Driving reviews


for news_typex in ['news', 'advice', 'drive']:  # Scheduled task, syntax is same as apscheduler package. Checks homepage for updates every 120 seconds, this can be omitted.
    fsdf_background_scheduler.add_timing_publish_job(crawl_list_page, 'interval', seconds=120, kwargs={"news_type": news_typex, "page": 1, "do_page_turning": False})
fsdf_background_scheduler.start()  # Start the scheduled publish task that checks for new news on the homepage
