import apify
# -*- coding: utf-8 -*-
import json
import scrapy
import jsonlines as jl
from scrapy import Selector

from actor.recipe_item import RecipeItem
from shanghai.tools import batch
import re


class RecipeSpider(scrapy.Spider):
    name = "recipe_spider"
    languages = "en"
    custom_settings = {"ITEM_PIPELINES": {"actor.pipelines.RecipePipeline": 300}}

    def start_requests(self):
        staring_url = "https://www.allrecipes.com/"
        yield scrapy.Request(url=staring_url, callback=self.crawl_categories)

    def crawl_categories(self, response):
        categories = response.xpath('//a[@data-internal-referrer-link="top hubs"]/@href').extract()
        if not categories:
            try:
                script = [s for s in response.xpath("//script").extract() if 'angular.module("allrecipes")' in s][0]
                script = (
                    script.replace('angular.module("allrecipes").value("hubCategories", ', "")
                    .strip()
                    .replace("<script>", "")
                    .replace("</script>", "")
                    .replace("');", "")
                    .strip()[1:]
                    .replace("\\", "")
                    .strip()
                )
                data = json.loads(script)
                categories = [f"https://www.allrecipes.com{d['Path']}" for d in data[0]["ChildHubs"]]
            except IndexError:
                pass
        # Yield other categories which have there own pages.
        if categories:
            for link in categories:
                print(link)
                # categories = [i for i in link.split("?")[0].replace("https://www.allrecipes.com/recipes/", "").split("/")[1:] if i]
                yield scrapy.Request(
                    url=link,
                    callback=self.crawl_categories,
                    # meta={"categories": response.meta['categories'].extend(categories)}
                )

        # Scrape recipes on current page.
        recipe_links = response.xpath('//a[@class="fixed-recipe-card__title-link"]/@href').extract()
        for link in recipe_links:
            yield scrapy.Request(url=response.urljoin(link), callback=self.parse_recipe)

        # If there is a next page scrape that page in a recursive fashion without scraping categories again.
        next_page = response.xpath('//link[@rel="next"]/@href').extract_first()
        if next_page:
            print(f"Recursive page {next_page}")
            yield scrapy.Request(url=next_page, callback=self.parse_recipes_page)

    def parse_recipes_page(self, response):
        recipe_links = response.xpath('//a[@class="fixed-recipe-card__title-link"]/@href').extract()

        for link in recipe_links:
            yield scrapy.Request(url=response.urljoin(link), callback=self.parse_recipe)

        # If there is a next page scrape that page in a recursive fashion without scraping categories again.
        next_page = response.xpath('//link[@rel="next"]/@href').extract_first()
        if next_page:
            print(f"Recursive call page {next_page}")
            yield scrapy.Request(url=next_page, callback=self.parse_recipes_page)

    def parse_recipe(self, response):
        # Two types of pages on all recipes.
        script = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        if script:
            data = json.loads(script)[1]
            cuisines = data.get("recipeCategory", [])
            review_count = response.xpath(
                '//div[@class="component recipe-reviews container-full-width template-two-col with-sidebar-right main-reviews"]/@data-ratings-count'
            ).extract_first()
            review_count = int(review_count) if review_count else -1
            score = response.xpath('//meta[@name="og:rating"]/@content').extract_first()
            score = float(score) if score else -1
            description = response.xpath('//meta[@name="description"]/@content').extract_first()
            description = description.strip() if description else ""
            prep_time = data.get("prepTime", -1)
            cook_time = data.get("cookTime", -1)
            total_time = data.get("totalTime", -1)
            nutrition_info = [
                v + " " + convert(k).replace("Content", "").title().replace('Calories', '').strip()
                for k, v in data.get("nutrition", {}).items()
                if k != "@type" and v
            ]
            directions = [d["text"] for d in data.get("recipeInstructions", [])]
            title = data["name"]
            ingredients = data.get("recipeIngredient", [])
            imgs = [data["image"]["url"]]

        else:
            cuisines = [
                c.strip()
                for c in response.xpath('//li[@itemprop="itemListElement"]/a/span[@itemprop="name"]/text()').extract()[
                    2:
                ]
            ]
            title = response.xpath('//h1[@id="recipe-main-content"]/text()').extract_first()
            score = response.xpath('//div[@class="rating-stars"]/@data-ratingstars').extract_first()
            score = float(score.strip()) if score else -1
            img_dom = "https://images.media-allrecipes.com/userphotos/"
            imgs = [
                img_dom + i.split("/")[-1]
                for i in response.xpath('//ul[@class="photo-strip__items"]/li/a/img/@src').extract()
            ]
            review_count = response.xpath('//span[@class="review-count"]/text()').extract_first()
            if review_count:
                review_count = review_count.replace("reviews", "")
                if "k" in review_count:
                    review_count = int(int(review_count.replace("k", "").strip()) * 1000)
                else:
                    review_count = int(review_count.strip())

            ingredients = response.xpath('//li[@class="checkList__line"]/label/@title').extract()
            description = response.xpath('//meta[@id="metaDescription"]/@content').extract_first()
            description = description.strip() if description else ""

            prep_time = response.xpath('//time[@itemprop="prepTime"]/@datetime').extract_first()
            cook_time = response.xpath('//time[@itemprop="cookTime"]/@datetime').extract_first()
            total_time = response.xpath('//time[@itemprop="totalTime"]/@datetime').extract_first()

            directions = [
                d.strip() for d in response.xpath('//span[@class="recipe-directions__list--item"]/text()').extract()
            ]
            nutrition_info_raw = response.xpath('//div[@class="nutrition-summary-facts"]/span/text()').extract()
            nutrition_info = []
            for n in batch(nutrition_info_raw, 2):
                nutrition_info.append(" ".join(n).replace("Per Serving:", "").replace(";", "").strip())
        recipe_item = RecipeItem(
            action_link=response.url,
            uid=response.url[:-1].split("/")[-1],
            imgs=[i for i in imgs if i.strip() != "https://www.allrecipes.com/img/misc/og-default.png"],
            score=score,
            review_count=review_count,
            name=title,
            ingredient_count=len(ingredients),
            prep_time=parse_time(recipe_time=prep_time),
            cook_time=parse_time(recipe_time=cook_time),
            total_time=parse_time(recipe_time=total_time),
            ingredients=ingredients,
            directions=directions,
            nutrition_info=nutrition_info,
            description=description,
            cuisines=cuisines,
            full_item=False
            # categories=response.meta['categories']
        ).to_dict()

        apify.pushData(recipe_item)


def parse_time(*, recipe_time):
    # Format of all the times.
    if recipe_time:
        recipe_time = recipe_time.replace("PT", "").replace("P0", "").replace("DT", "")
        day_mins = 0
        hour_mins = 0
        mins = 0
        if "Days" in recipe_time:
            days = recipe_time.split("Days")[0]
            day_mins = int(days) * 24 * 60
            recipe_time = recipe_time.replace(days + "Days", "")
        if "Day" in recipe_time:
            days = recipe_time.split("Day")[0]
            day_mins = int(days) * 24 * 60
            recipe_time = recipe_time.replace(days + "Day", "")
        if "H" in recipe_time:
            # Get time of hour in minutes
            hours = recipe_time.split("H")[0]
            hour_mins = int(hours) * 60
            recipe_time = recipe_time.replace(hours + "H", "")
        if "M" in recipe_time:
            mins = int(recipe_time.replace("M", ""))
        time_out = hour_mins + mins + day_mins
    else:
        time_out = -1

    return time_out


def convert(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1 \2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1 \2", s1)


# angular.module('allrecipes').value('feedItems', [{"title":"Creamy Summer Pasta Salad with BelGioioso Shaved Parmesan","videoTitle":"","reviewCount":2,"imageUrl":"https://images.media-allrecipes.com/userphotos/300x300/4516514.jpg","description":"Fusilli pasta is tossed with sauteed tomatoes, kale, and zucchini and a creamy rosemary-infused dressing. Serve topped with almonds and Parmesan cheese.","stars":{"rating":4.6700000762939453,"starsCssClasses":"stars stars-4-5"},"cook":{"id":21359636,"displayName":"BelGioioso Cheese","thumbnail":"https://images.media-allrecipes.com/userphotos/50x50/4488254.jpg","followersCount":96,"favoriteCount":9,"handle":"belgioioso","thumbnailUrl":"https://images.media-allrecipes.com/userphotos/50x50/4488254.jpg","profileUrl":"/cook/belgioioso/"},"collectionId":"0","feedItemViewModelType":"RecipeFeedItemViewModel","feedSubItemType":"RecipeOfTheDay","cardHeaderText":"","detailUrl":"/recipe/258218/creamy-summer-pasta-salad-with-belgioioso-shaved-parmesan/","videoDetailUrl":"","altText":"Creamy Summer Pasta Salad with BelGioioso Shaved Parmesan Recipe - Fusilli pasta is tossed with sauteed tomatoes, kale, and zucchini and a creamy rosemary-infused dressing. Serve topped with almonds and Parmesan cheese.","titleText":"Creamy Summer Pasta Salad with BelGioioso Shaved Parmesan Recipe","id":258218,"analyticsType":"rotd","sourceId":545,"trackingPixelUrl":"https://pubads.g.doubleclick.net/gampad/ad?iu=/3865/DFP_1x1_impression_tracker\u0026sz=1x1\u0026t=adpartner%3D\u0026c=05adb71f-4172-4c7d-ae34-c29184583848","contentProviderId":"535"},{"_cardPath":"~/Views/Shared/Partials/Grids/Cards/FixedGridMarketingCard.cshtml","feedItemViewModelType":"CommunityElementFeedItemViewModel","imageUrl":"https://images.media-allrecipes.com/images/64217.jpg","title":"Celebrate Independence Day!","linkUrl":"https://www.allrecipes.com/recipes/191/holidays-and-events/4th-of-july/","description":"Find everything you need for your July 4th festivities.","cook":{"id":3672150,"displayName":"Allrecipes","thumbnail":"https://secureimages.allrecipes.com/userphotos/250x250/2400622.jpg","followersCount":3512107,"favoriteCount":1414,"madeRecipesCount":64,"handle":"allrecipes","thumbnailUrl":"https://secureimages.allrecipes.com/userphotos/250x250/2400622.jpg","profileUrl":"/cook/allrecipes/"},"contentProviderId":"0"},{"title":"Key West Chicken","reviewCount":999,"imageUrl":"https://images.media-allrecipes.com/userphotos/300x300/694150.jpg","description":"This recipe from the Florida Keys is the best marinade for chicken, and it only takes 30 minutes from prep till you can grill! It\u0027s a great blend of flavors with honey, soy sauce, and lime juice.","videoId":1354,"stars":{"rating":4.3000001907348633,"starsCssClasses":"stars stars-4-5"},"cook":{"id":69960,"displayName":"TINA B","thumbnail":"","followersCount":29,"favoriteCount":7,"madeRecipesCount":15,"handle":"","thumbnailUrl":"https://images.media-allrecipes.com/userphotos/50x50/5674137.jpg","profileUrl":"/cook/69960/"},"collectionId":"0","feedItemViewModelType":"RecipeFeedItemViewModel","feedSubItemType":"RecipeRecommendationPopular","cardHeaderText":"","detailUrl":"/recipe/25445/key-west-chicken/","videoDetailUrl":"/video/1354/key-west-chicken/","altText":"Key West Chicken Recipe and Video - This recipe from the Florida Keys is the best marinade for chicken, and it only takes 30 minutes from prep till you can grill! It\u0027s a great blend of flavors with honey, soy sauce, and lime juice.","titleText":"Key West Chicken Recipe and Video","id":25445,"analyticsType":"popular","contentProviderId":"0"},{"title":"Spanish Rice Bake","reviewCount":959,"imageUrl":"https://images.media-allrecipes.com/userphotos/300x300/2471.jpg","description":"Ground beef, fresh onion, green bell pepper, tomatoes and rice are simmered in a sweet-hot sauce then baked with Cheddar and garnished with fresh cilantro.","videoId":8049,"stars":{"rating":4.3499999046325684,"starsCssClasses":"stars stars-4-5"},"cook":{"id":37304,"displayName":"MELODIE","thumbnail":"","followersCount":11,"favoriteCount":1,"handle":"","thumbnailUrl":"https://images.media-allrecipes.com/userphotos/50x50/5674137.jpg","profileUrl":"/cook/37304/"},"collectionId":"0","feedItemViewModelType":"RecipeFeedItemViewModel","feedSubItemType":"RecipeRecommendationPopular","cardHeaderText":"","detailUrl":"/recipe/18830/spanish-rice-bake/","videoDetailUrl":"/video/8049/spanish-rice-bake/","altText":"Spanish Rice Bake Recipe and Video - Ground beef, fresh onion, green bell pepper, tomatoes and rice are simmered in a sweet-hot sauce then baked with Cheddar and garnished with fresh cilantro.","titleText":"Spanish Rice Bake Recipe and Video","id":18830,"analyticsType":"popular","sourceId":254,"trackingPixelUrl":"https://pubads.g.doubleclick.net/gampad/ad?iu=/3865/DFP_1x1_impression_tracker\u0026sz=1x1\u0026t=adpartner%3D\u0026c=06f41a59-a0df-49ea-a64f-5781fe0ee7da","contentProviderId":"0"},{"title":"No-Noodle Zucchini Lasagna","reviewCount":409,"imageUrl":"https://images.media-allrecipes.com/userphotos/300x300/6287281.jpg","description":"Thin slices of zucchini stand in for noodles in this lasagna. It is perfect in the summer with your garden-fresh veggies and herbs, or in the winter when you need a comforting meal.","videoId":4683,"stars":{"rating":4.5900001525878906,"starsCssClasses":"stars stars-4-5"},"cook":{"id":1530738,"displayName":"Jill Welch","thumbnail":"","followersCount":15,"favoriteCount":15,"madeRecipesCount":65,"handle":"","thumbnailUrl":"https://images.media-allrecipes.com/userphotos/50x50/5614284.jpg","profileUrl":"/cook/1530738/"},"collectionId":"0","feedItemViewModelType":"RecipeFeedItemViewModel","feedSubItemType":"RecipeRecommendationPopular","cardHeaderText":"","detailUrl":"/recipe/172958/no-noodle-zucchini-lasagna/","videoDetailUrl":"/video/4683/no-noodle-zucchini-lasagna/","altText":"No-Noodle Zucchini Lasagna Recipe and Video - Thin slices of zucchini stand in for noodles in this lasagna. It is perfect in the summer with your garden-fresh veggies and herbs, or in the winter when you need a comforting meal.","titleText":"No-Noodle Zucchini Lasagna Recipe and Video","id":172958,"analyticsType":"popular","contentProviderId":"0"},{"title":"Slow-Cooker Pepper Steak","reviewCount":2301,"imageUrl":"https://images.media-allrecipes.com/userphotos/300x300/496244.jpg","description":"Tasty strips of sirloin are seasoned with garlic powder, then slow cooked with onion, green pepper, and stewed tomatoes for this easy and comforting dinner.","videoId":698,"stars":{"rating":4.440000057220459,"starsCssClasses":"stars stars-4-5"},"cook":{"id":193357,"displayName":"MJWAGNER68","thumbnail":"","followersCount":20,"favoriteCount":44,"madeRecipesCount":9,"handle":"","thumbnailUrl":"https://images.media-allrecipes.com/userphotos/50x50/5674138.jpg","profileUrl":"/cook/193357/"},"collectionId":"0","feedItemViewModelType":"RecipeFeedItemViewModel","feedSubItemType":"RecipeRecommendationPopular","cardHeaderText":"","detailUrl":"/recipe/23567/slow-cooker-pepper-steak/","videoDetailUrl":"/video/698/slow-cooker-pepper-steak/","altText":"Slow-Cooker Pepper Steak Recipe and Video - Tasty strips of sirloin are seasoned with garlic powder, then slow cooked with onion, green pepper, and stewed tomatoes for this easy and comforting dinner.","titleText":"Slow-Cooker Pepper Steak Recipe and Video","id":23567,"analyticsType":"popular","sourceId":461,"trackingPixelUrl":"https://pubads.g.doubleclick.net/gampad/ad?iu=/3865/DFP_1x1_impression_tracker\u0026sz=1x1\u0026t=adpartner%3Dallrecipesmagazine_earned_impression\u0026c=07d208b7-dd95-4682-ae49-f13a7ea70e91","contentProviderId":"451"},{"title":"Delicious Egg Salad for Sandwiches","reviewCount":1202,"imageUrl":"https://images.media-allrecipes.com/userphotos/300x300/191517.jpg","description":"Make the perfect egg salad for sandwiches!","videoId":3288,"stars":{"rating":4.619999885559082,"starsCssClasses":"stars stars-4-5"},"cook":{"id":2309128,"displayName":"wifeyluvs2cook","thumbnail":"https://images.media-allrecipes.com/userphotos/50x50/343276.jpg","followersCount":311,"favoriteCount":265,"madeRecipesCount":117,"handle":"","thumbnailUrl":"https://images.media-allrecipes.com/userphotos/50x50/343276.jpg","profileUrl":"/cook/2309128/"},"collectionId":"0","feedItemViewModelType":"RecipeFeedItemViewModel","feedSubItemType":"RecipeRecommendationPopular","cardHeaderText":"","detailUrl":"/recipe/147103/delicious-egg-salad-for-sandwiches/","videoDetailUrl":"/video/3288/delicious-egg-salad-for-sandwiches/","altText":"Delicious Egg Salad for Sandwiches Recipe and Video - Make the perfect egg salad for sandwiches!","titleText":"Delicious Egg Salad for Sandwiches Recipe and Video","id":147103,"analyticsType":"popular","sourceId":461,"trackingPixelUrl":"https://pubads.g.doubleclick.net/gampad/ad?iu=/3865/DFP_1x1_impression_tracker\u0026sz=1x1\u0026t=adpartner%3Dallrecipesmagazine_earned_impression\u0026c=860eed3d-e38a-48eb-ba7a-5b2ed8284b90","contentProviderId":"451"},{"title":"Pineapple Sticky Ribs","reviewCount":36,"imageUrl":"https://images.media-allrecipes.com/userphotos/300x300/4039350.jpg","description":"These savory pork ribs are baked in a sticky-sweet mixture of pineapple tidbits, apricot jam, and soy sauce to create a crowd-pleasing meal.","stars":{"rating":4.6599998474121094,"starsCssClasses":"stars stars-4-5"},"cook":{"id":1178074,"displayName":"SUNKIST2","thumbnail":"https://images.media-allrecipes.com/userphotos/50x50/3979554.jpg","followersCount":17,"favoriteCount":142,"madeRecipesCount":55,"handle":"sunkist2","thumbnailUrl":"https://images.media-allrecipes.com/userphotos/50x50/3979554.jpg","profileUrl":"/cook/sunkist2/"},"collectionId":"0","feedItemViewModelType":"RecipeFeedItemViewModel","feedSubItemType":"RecipeRecommendationPopular","cardHeaderText":"","detailUrl":"/recipe/255220/pineapple-sticky-ribs/","videoDetailUrl":"","altText":"Pineapple Sticky Ribs Recipe - These savory pork ribs are bak…


		 
