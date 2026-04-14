
# feapder 2-level crawler demo

# Import relevant modules from the feapder framework
from feapder import Item, Spider, Request

# Define a data model class, inheriting from feapder's Item class
class MyItem(Item):
    # Define data fields
    title = "default"
    url = "default"

# Define a spider class, inheriting from feapder's Spider class
class MySpider(Spider):
    # Define starting URLs
    start_urls = ["https://www.example.com"]

    # Parse function for handling list pages
    def parse(self, request, response):
        # Use xpath to parse and get all article links
        links = response.xpath('//div[@class="post-title"]/a/@href').extract()

        # Iterate over the link list, construct Request objects and send them
        for link in links:
            yield Request(link, callback=self.parse_detail)

    # Parse function for handling detail pages
    def parse_detail(self, request, response):
        # Instantiate MyItem class
        item = MyItem()

        # Extract title and URL
        item.title = response.xpath('//h1[@class="post-title"]/text()').extract_first()
        item.url = request.url

        # Return data
        yield item

# Run the spider
if __name__ == "__main__":
    MySpider().start()
