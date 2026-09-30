def add_tag(tag, tags=None):
    if tags is None:  # a fresh list on every call
        tags = []
    tags.append(tag)
    return tags


print(add_tag("a"), add_tag("b"))  # ['a'] ['b']
