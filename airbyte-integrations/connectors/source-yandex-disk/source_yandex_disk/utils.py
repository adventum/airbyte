import collections
def find_duplicates(l: list):
    return [item for item, count in collections.Counter(l).items() if count > 1]