from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional
from actor.items import BaseItem

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass


@dataclass
class RecipeItem(BaseItem):
    score: float
    review_count: int
    # rating_distribution = scrapy.Field()
    ingredient_count: int
    prep_time: float
    cook_time: float
    total_time: float
    ingredients: List[str]
    directions: List[str]
    nutrition_info: List[str]
    cuisines: List[str]

    class Meta:
        name = "recipe_item"

    def img_label_values(self) -> List[str]:
        return BaseItem.clean_label_values(labels=self.cuisines + [i["name"] for i in self.ingredients if "name" in i])

    def search_engine_query(self):
        return self.name.replace("'", "").replace("-", " ").replace(" ", "+").strip()

    def to_dict(self):
        self.full_item = all([self.total_time, self.score, self.review_count, self.ingredients])
        return super().to_dict()
