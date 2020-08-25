# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
from recipes.convert_recipe_ingredients import batch_recipe_formatting
import jsonlines

CURRENT_DATASET = "temp_recipe"


class RecipePipeline(object):
    def __init__(self, crawler):
        self.crawler = crawler
        self.ids_seen = set()
        # self.wtr = jsonlines.open(f"domains_data/items/{CURRENT_DATASET}.jl", "w")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def open_spider(self, spider):
        pass

    # def close_spider(self, spider):
    #     self.wtr.close()
    #     batch_recipe_formatting(f"domains_data/items/{CURRENT_DATASET}.jl", f"domains_data/final/{CURRENT_DATASET}.jl")

    # def process_item(self, item, spider):
    #     if item["uid"] in self.ids_seen:
    #         raise DropItem("Item has already been scraped and collected.")
    #     # Flag if item has full necessary data items.
    #     full_item = all([item[f] for f in ["action_link", "uid", "name", "imgs", "description"]])
    #     self.ids_seen.add(item["uid"])
    #     item["full_item"] = full_item
    #     self.wtr.write(dict(item))
    #     return item
