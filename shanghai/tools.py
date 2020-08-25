from w3lib.html import replace_entities
from collections import defaultdict
from typing import Dict, Set
from PIL import Image
from io import BytesIO
import jsonlines
import copy
import glob
import csv
import os

import hashlib
import zlib


def md5s(*args) -> str:
    return "_".join((hashlib.md5(str(arg).encode()).hexdigest()[:9] for arg in args))


def adler32s(*args) -> str:
    return "_".join((str(zlib.adler32(str(arg).encode())) for arg in args))


def multi_hash(*args) -> str:
    return md5s(*args) + adler32s(*args)



def batch(*, iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx : min(ndx + n, l)]


def ensure_dir(*, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def clear_dir(*, dir_glob: str) -> None:
    files = glob.glob(dir_glob)
    for f in files:
        os.remove(f)


def save_img_bytes(*, path, bytes):
    img = Image.open(BytesIO(bytes))
    img.save(path)


def get_resolver(*, csv_file) -> Dict[str, Set]:
    res: Dict[str, Set] = defaultdict(set)
    with open(csv_file) as file_pointer:
        reader = csv.reader(file_pointer, delimiter=",")
        for row in reader:
            for col in row[1:]:
                res[row[0].lower().strip()].add(col.lower().strip())
    return res


def clean_file(file_name, fields):
    res = []
    with jsonlines.open(file_name) as rdr:
        for line in rdr:
            for f in fields:
                if not line[f]:
                    continue
                line[f] = replace_entities(line[f].replace("\n", "").strip())
            res.append(copy.deepcopy(line))
    return res
