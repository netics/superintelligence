# 1. Order doesn't matter: {a, b} is the same key as {b, a}
since = {frozenset({"ana", "bo"}): 2019}
print(since[frozenset({"bo", "ana"})])  # 2019

# 2. Sets inside a set (a plain set isn't hashable)
teams = {frozenset({"ana", "bo"}), frozenset({"bo", "ana"})}
print(len(teams))  # 1, the same team twice

# 3. A constant set nobody can change by accident
METHODS = frozenset({"GET", "POST"})
print("PUT" in METHODS)  # False
