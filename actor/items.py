from w3lib.html import replace_entities
from typing import TYPE_CHECKING, List, Optional
import unidecode

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass
from pydantic import validator
import json
import os
import inspect


def clean_item_label(*, label: str):
    label = unidecode.unidecode(replace_entities(str(label.lower())))
    l_out = []
    for c in label:
        if c.isalpha() or c.isdigit() or c == " " or c == "-":
            l_out.append(c)
    label = "".join(l_out).replace(" ", "_").replace("-", "_").strip()
    for i in range(4, 1, -1):
        underscores = i * "_"
        if underscores in label:
            label = label.replace(underscores, "_").strip()
    if "_" == label[-1]:
        label = label[:-1]
    if "_" == label[0]:
        label = label[1:]
    return label


@dataclass
class BaseItem:
    action_link: str
    uid: str
    name: str
    imgs: List[str]
    description: Optional[str]
    full_item: bool

    class Meta:
        name = "base_item"

    @classmethod
    def domain_name(cls):
        return cls.Meta.name

    @validator("action_link", "uid")
    def check_exist(cls, v):
        if not v:
            raise ValueError("Value cannot be empty")
        return v

    @validator("name", always=True)
    def check_html_ascii(cls, v):
        if not v:
            raise ValueError("Name cannot be empty")
        return replace_entities(v)

    @validator("description", always=True)
    def check_html_ascii_description(cls, v):
        if not v or v == "":
            return ""
        return replace_entities(v)

    @validator("action_link", always=True)
    def check_each_img(cls, v):
        if "http:" not in v and "https:" not in v:
            raise ValueError(f"The url is does not use http or https: {v}")
        return v

    # @validator("imgs", always=True, whole=True)
    # def check_each_img(cls, v):
    #     for u in v:
    #         if "http:" not in u and "https:" not in u:
    #             raise ValueError(f"The url is does not use http or https: {u}")
    #     return v

    @classmethod
    def clean_label_values(cls, labels: List[str]) -> List[str]:
        res: List[str] = []
        temp_list: List[str] = []
        for label in labels:
            label = str(label).strip()
            if not label:
                continue
            if len(label) >= 32:
                continue
            if not label[0].isalpha() and not label[0].isdigit():
                continue
            if not all([c.isalpha() or c.isdigit() or c == "_" or c == "-" or c == " " for c in label]):
                continue
            temp_list.append(label)

        for val in temp_list:
            cv = clean_item_label(label=val)
            if cv:
                res.append(cv)
        if len(res) == 0:
            raise ValueError(f"There are no valid labels,raw labels: {labels}")
        return res

    def img_label_values(self) -> List[str]:
        raise NotImplementedError("Must implement img labels for image models.")

    def search_engine_query(self) -> str:
        raise NotImplementedError("Must implement bing query for scraping images.")

    def to_dict(self):
        dict_ver = self.__dict__
        del dict_ver["__initialised__"]
        return dict_ver

    def append_config_vals(self, domain: str):
        with open(f'{domain}/config.json') as config:
            mapping = json.load(config)
            for json_attribute_key in mapping.keys():
                if hasattr(self, json_attribute_key):
                    for key in mapping[json_attribute_key].keys():
                        if key in getattr(self, json_attribute_key):
                            getattr(self, json_attribute_key).extend(mapping[json_attribute_key][key])
                    setattr(self, json_attribute_key, list(set(getattr(self, json_attribute_key))))

