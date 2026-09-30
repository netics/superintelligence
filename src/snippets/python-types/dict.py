stock = {"apple": 3, "pear": 0}
stock["plum"] = 5  # add or update by key
print(stock.get("kiwi", 0))  # 0, a default for a missing key

counts = {}
for word in "to be or not to be".split():
    counts[word] = counts.get(word, 0) + 1
print(counts)  # {'to': 2, 'be': 2, 'or': 1, 'not': 1}
