import collections


def find_duplicates(_list: list):
    return [item for item, count in collections.Counter(_list).items() if count > 1]
